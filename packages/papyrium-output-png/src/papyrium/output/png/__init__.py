"""PNG output: one greyscale raster image per page."""

from __future__ import annotations

import math
from functools import cache
from pathlib import Path

from PIL import Image, ImageDraw

from papyrium.core.output import Document, Output
from papyrium.core.page import UNITS_PER_INCH, Page
from papyrium.core.stationery import Circle

__version__ = "0.0.0"

__all__ = ["PngOutput"]

#: Dot centres are placed to 1/SUBPIXELS of a pixel.
SUBPIXELS = 8
#: Each pixel's coverage by a dot is measured on a SUPERSAMPLE-square grid.
SUPERSAMPLE = 16


@cache
def _dot_stamp(diameter: float, x_eighths: int, y_eighths: int) -> tuple[Image.Image, int]:
    """A mask of how much of each pixel a dot covers, and its margin.

    The dot is *diameter* pixels across, centred *x_eighths* and
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
        draw = ImageDraw.Draw(image)
        for feature in features:
            if isinstance(feature, Circle):
                r = feature.diameter * scale / 2
                cx, cy = feature.x * scale, feature.y * scale
                draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=feature.colour)
            else:
                x0, y0 = feature.x * scale, feature.y * scale
                x1 = (feature.x + feature.width) * scale
                y1 = (feature.y + feature.height) * scale
                # At least a pixel, so fine rules and perforations show at low resolution.
                draw.rectangle(
                    (x0, y0, max(x1, x0 + 1) - 1, max(y1, y0 + 1) - 1), fill=feature.colour
                )
        # Each dot is stamped with the share of each pixel it covers, so a dot
        # only a pixel or two across stays round.
        diameter = page.dot_diameter * scale
        for x, y in dict.fromkeys(page.dots):
            column, x_eighths = divmod(round(x * scale * SUBPIXELS), SUBPIXELS)
            row, y_eighths = divmod(round(y * scale * SUBPIXELS), SUBPIXELS)
            stamp, margin = _dot_stamp(diameter, x_eighths, y_eighths)
            image.paste(ink, (column - margin, row - margin), mask=stamp)
        return image
