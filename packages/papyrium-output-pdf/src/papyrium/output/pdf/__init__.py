"""PDF output: each job as one document, each dot as a vector dot."""

from __future__ import annotations

import zlib
from fractions import Fraction
from pathlib import Path

from papyrium.core.output import Document, Output
from papyrium.core.page import UNITS_PER_INCH, Page

__version__ = "0.0.0"

__all__ = ["PdfOutput"]

#: Page units per PDF point (1/72 inch).
_UNITS_PER_POINT = UNITS_PER_INCH // 72


def _number(value: Fraction | float) -> str:
    """A PDF real: exact for whole numbers, otherwise four decimal places."""
    value = Fraction(value)
    if value.denominator == 1:
        return str(value.numerator)
    return f"{float(value):.4f}".rstrip("0").rstrip(".")


class _PdfDocument(Document):
    def __init__(self, filepath: Path, ink: float) -> None:
        self._filepath = filepath
        self._ink = ink
        self._pages: list[tuple[Page, bytes]] = []

    def add_page(self, page: Page) -> None:
        self._pages.append((page, zlib.compress(self._content(page), 9)))

    def _content(self, page: Page) -> bytes:
        height_points = Fraction(page.height, _UNITS_PER_POINT)
        scale = _number(Fraction(1, _UNITS_PER_POINT))
        lines = [
            "q",
            f"{scale} 0 0 -{scale} 0 {_number(height_points)} cm",
            f"1 J {page.dot_diameter} w {_number(Fraction(self._ink))} G",
        ]
        lines.extend(f"{x} {y} m {x} {y} l" for x, y in dict.fromkeys(page.dots))
        lines.extend(["S", "Q", ""])
        return "\n".join(lines).encode("ascii")

    def close(self) -> list[Path]:
        if not self._pages:
            return []
        self._filepath.write_bytes(self._serialise())
        return [self._filepath]

    def _serialise(self) -> bytes:
        objects: list[bytes] = []

        def add(body: bytes) -> int:
            objects.append(body)
            return len(objects)

        catalog_number = add(b"")  # Filled in once the page tree number is known.
        pages_number = add(b"")
        page_numbers = []
        for page, stream in self._pages:
            contents_number = add(
                b"<< /Length %d /Filter /FlateDecode >>\nstream\n" % len(stream)
                + stream
                + b"\nendstream"
            )
            media_box = " ".join(
                _number(value)
                for value in (
                    0,
                    0,
                    Fraction(page.width, _UNITS_PER_POINT),
                    Fraction(page.height, _UNITS_PER_POINT),
                )
            )
            page_numbers.append(
                add(
                    f"<< /Type /Page /Parent {pages_number} 0 R /MediaBox [{media_box}] "
                    f"/Contents {contents_number} 0 R /Resources << >> >>".encode("ascii")
                )
            )
        kids = " ".join(f"{number} 0 R" for number in page_numbers)
        objects[pages_number - 1] = (
            f"<< /Type /Pages /Kids [{kids}] /Count {len(page_numbers)} >>".encode("ascii")
        )
        objects[catalog_number - 1] = f"<< /Type /Catalog /Pages {pages_number} 0 R >>".encode(
            "ascii"
        )
        info_number = add(b"<< /Producer (Papyrium) >>")

        output = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offsets = []
        for number, body in enumerate(objects, start=1):
            offsets.append(len(output))
            output += b"%d 0 obj\n" % number + body + b"\nendobj\n"
        xref_offset = len(output)
        output += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objects) + 1)
        for offset in offsets:
            output += b"%010d 00000 n \n" % offset
        output += b"trailer\n<< /Size %d /Root %d 0 R /Info %d 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (
            len(objects) + 1,
            catalog_number,
            info_number,
            xref_offset,
        )
        return bytes(output)


class PdfOutput(Output):
    """One PDF per job, one page per printed page, every dot a vector dot.

    Options: ``ink`` grey level from 0 (black) to 1 (white), default 0.15;
    ``filename``, default ``job.pdf``.
    """

    def __init__(self, name: str, *, ink: float = 0.15, filename: str = "job.pdf", **kwargs):
        super().__init__(name=name, **kwargs)
        self._ink = ink
        self._filename = filename

    def open_document(self, dirpath: Path) -> Document:
        return _PdfDocument(dirpath / self._filename, self._ink)
