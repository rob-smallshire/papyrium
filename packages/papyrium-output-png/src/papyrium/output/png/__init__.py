"""PNG output: one greyscale raster image per page."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from papyrium.core.output import Document, Output
from papyrium.core.page import UNITS_PER_INCH, Page

__version__ = "0.0.0"

__all__ = ["PngOutput"]


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
    """Greyscale PNG images, one per page, with each struck dot drawn as a dot.

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
        """Draw *page* as a greyscale image."""
        scale = self._dpi / UNITS_PER_INCH
        size = (round(page.width * scale), round(page.height * scale))
        image = Image.new("L", size, self._paper)
        draw = ImageDraw.Draw(image)
        radius = page.dot_diameter * scale / 2
        for x, y in dict.fromkeys(page.dots):
            cx, cy = x * scale, y * scale
            draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=self._ink)
        return image
