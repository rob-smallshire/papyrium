"""PNG output: one greyscale raster image per page."""

from __future__ import annotations

import math
from functools import cache
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

from papyrium.core.output import Document, Output
from papyrium.core.page import UNITS_PER_INCH, Page
from papyrium.core.stationery import Circle

__version__ = "0.1.0"

__all__ = ["PngOutput"]

# Everything is drawn antialiased: each shape is pasted through a mask of
# the share of each pixel it covers, so shapes a pixel or two across keep
# their form and edges fall between pixels.

#: Disc centres are placed to 1/SUBPIXELS of a pixel.
SUBPIXELS = 8
#: Each pixel's coverage by a disc is measured on a SUPERSAMPLE-square grid.
SUPERSAMPLE = 16


@cache
def _disc_stamp(diameter: float, x_eighths: int, y_eighths: int) -> tuple[Image.Image, int]:
    """A mask of how much of each pixel a disc covers, and its margin.

    The disc is *diameter* pixels across, centred *x_eighths* and
    *y_eighths* of a pixel (in SUBPIXELS) right of and below the top-left
    corner of the stamp's centre pixel, which is *margin* pixels in from
    the stamp's top-left corner.
    """
    margin = math.ceil(diameter / 2) + 1
    size = 2 * margin + 1
    radius = diameter / 2 * SUPERSAMPLE
    cx = (margin + x_eighths / SUBPIXELS) * SUPERSAMPLE
    cy = (margin + y_eighths / SUBPIXELS) * SUPERSAMPLE
    large = Image.new("L", (size * SUPERSAMPLE,) * 2, 0)
    ImageDraw.Draw(large).ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=255)
    return large.reduce(SUPERSAMPLE), margin


def _paste_disc(image: Image.Image, colour, x: float, y: float, diameter: float) -> None:
    """Paint a disc *diameter* pixels across, centred at pixel coordinates *x*, *y*."""
    column, x_eighths = divmod(round(x * SUBPIXELS), SUBPIXELS)
    row, y_eighths = divmod(round(y * SUBPIXELS), SUBPIXELS)
    stamp, margin = _disc_stamp(diameter, x_eighths, y_eighths)
    image.paste(colour, (column - margin, row - margin), mask=stamp)


def _coverage(start: float, end: float) -> tuple[int, bytes]:
    """The first pixel a span from *start* to *end* touches, and its share of each, 0-255."""
    first, last = math.floor(start), max(math.ceil(end), math.floor(start) + 1)
    shares = bytes(
        round(255 * max(0.0, min(end, pixel + 1) - max(start, pixel)))
        for pixel in range(first, last)
    )
    return first, shares


def _paste_rectangle(image: Image.Image, colour, x0: float, y0: float, x1: float, y1: float):
    """Paint a rectangle with corners at pixel coordinates (*x0*, *y0*) and (*x1*, *y1*)."""
    column, across = _coverage(x0, x1)
    row, down = _coverage(y0, y1)
    size = (len(across), len(down))
    mask = ImageChops.multiply(
        Image.frombytes("L", (len(across), 1), across).resize(size, Image.Resampling.NEAREST),
        Image.frombytes("L", (1, len(down)), down).resize(size, Image.Resampling.NEAREST),
    )
    image.paste(colour, (column, row, column + size[0], row + size[1]), mask=mask)


class _PngDocument(Document):
    def __init__(self, output: PngOutput, dirpath: Path) -> None:
        self._output = output
        self._dirpath = dirpath
        self._filepaths: list[Path] = []

    def add_page(self, page: Page) -> None:
        filepath = self._dirpath / f"page-{page.number:04d}.png"
        # Written aside and renamed into place, so a reader never sees a partial image.
        temporary_filepath = filepath.with_name(filepath.name + ".tmp")
        image = self._output.render(page)
        image.save(temporary_filepath, format="PNG", dpi=(self._output.dpi,) * 2)
        temporary_filepath.replace(filepath)
        self._filepaths.append(filepath)

    def close(self) -> list[Path]:
        return list(self._filepaths)


class PngOutput(Output):
    """PNG images, one per page, with each struck dot drawn as a dot.

    Pages are greyscale, or colour when their stationery is printed.

    Options: ``dpi`` (default 360, at which a page unit is exactly 1/12
    pixel), ``ink`` and ``paper`` grey levels from 0 (black) to 255 (white).
    """

    def __init__(self, name: str, *, dpi: int = 360, ink: int = 40, paper: int = 255, **kwargs):
        super().__init__(name=name, **kwargs)
        self._dpi = dpi
        self._ink = ink
        self._paper = paper

    @property
    def dpi(self) -> int:
        return self._dpi

    def open_document(self, dirpath: Path) -> Document:
        return _PngDocument(self, dirpath)

    def render(self, page: Page) -> Image.Image:
        """Draw *page*, in greyscale unless its stationery has features."""
        scale = self._dpi / UNITS_PER_INCH
        size = (round(page.width * scale), round(page.height * scale))
        features = page.stationery.features(page.width, page.height) if page.stationery else ()
        if features:
            image = Image.new("RGB", size, (self._paper,) * 3)
            ink: int | tuple[int, int, int] = (self._ink,) * 3
        else:
            image = Image.new("L", size, self._paper)
            ink = self._ink
        for feature in features:
            if isinstance(feature, Circle):
                x, y = feature.x * scale, feature.y * scale
                _paste_disc(image, feature.colour, x, y, feature.diameter * scale)
            else:
                _paste_rectangle(
                    image,
                    feature.colour,
                    feature.x * scale,
                    feature.y * scale,
                    (feature.x + feature.width) * scale,
                    (feature.y + feature.height) * scale,
                )
        diameter = page.dot_diameter * scale
        for x, y in dict.fromkeys(page.dots):
            _paste_disc(image, ink, x * scale, y * scale, diameter)
        return image
