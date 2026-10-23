"""PDF output: each job as one document, each dot as a vector dot."""

from __future__ import annotations

import zlib
from fractions import Fraction
from pathlib import Path

from papyrium.core.output import Document, Output
from papyrium.core.page import UNITS_PER_INCH, Page, TextMark

__version__ = "0.0.0"

__all__ = ["PdfOutput"]

#: Page units per PDF point (1/72 inch).
_UNITS_PER_POINT = UNITS_PER_INCH // 72


#: Courier's advance width as a fraction of its size.
_COURIER_ADVANCE = Fraction(3, 5)

#: The baseline of a text cell, as a fraction of the cell's height down from its top.
_BASELINE = Fraction(7, 9)


def _pdf_string(text: str) -> str:
    """A PDF literal string in WinAnsiEncoding; unencodable characters become '?'."""
    encoded = text.encode("cp1252", errors="replace")
    parts = []
    for byte in encoded:
        if byte in b"()\\":
            parts.append("\\" + chr(byte))
        elif 0x20 <= byte < 0x7F:
            parts.append(chr(byte))
        else:
            parts.append(f"\\{byte:03o}")
    return "(" + "".join(parts) + ")"


def _text_runs(marks: tuple[TextMark, ...]) -> list[list[TextMark]]:
    """Group marks into runs printed side by side in cells of one size."""
    runs: list[list[TextMark]] = []
    for mark in marks:
        if runs:
            last = runs[-1][-1]
            if (
                mark.y == last.y
                and mark.width == last.width
                and mark.height == last.height
                and mark.x == last.x + last.width
            ):
                runs[-1].append(mark)
                continue
        runs.append([mark])
    return runs


def _number(value: Fraction | float) -> str:
    """A PDF real: exact for whole numbers, otherwise four decimal places."""
    value = Fraction(value)
    if value.denominator == 1:
        return str(value.numerator)
    return f"{float(value):.4f}".rstrip("0").rstrip(".")


class _PdfDocument(Document):
    def __init__(self, filepath: Path, ink: float, text: bool) -> None:
        self._filepath = filepath
        self._ink = ink
        self._text = text
        self._pages: list[tuple[Page, bytes]] = []

    def add_page(self, page: Page) -> None:
        self._pages.append((page, zlib.compress(self._content(page), 6)))

    def _content(self, page: Page) -> bytes:
        height_points = Fraction(page.height, _UNITS_PER_POINT)
        # Ten decimal places: four would misplace dots by over a point on a page.
        scale = f"{1 / _UNITS_PER_POINT:.10f}"
        lines = self._text_content(page, height_points) if self._text else []
        lines += [
            "q",
            f"{scale} 0 0 -{scale} 0 {_number(height_points)} cm",
            f"1 J {page.dot_diameter} w {_number(Fraction(self._ink))} G",
        ]
        # One row of dots at a time: translate down to the row, then give
        # only x coordinates. Rows of text repeat, so this compresses far
        # better than absolute coordinates. Each row is its own path because
        # cm may not appear inside one.
        rows: dict[int, list[int]] = {}
        for x, y in sorted(set(page.dots), key=lambda dot: (dot[1], dot[0])):
            rows.setdefault(y, []).append(x)
        row_y = 0
        for y, xs in rows.items():
            lines.append(f"1 0 0 1 0 {y - row_y} cm")
            row_y = y
            lines.extend(f"{x} 0 m {x} 0 l" for x in xs)
            lines.append("S")
        lines.extend(["Q", ""])
        return "\n".join(lines).encode("ascii")

    def _text_content(self, page: Page, height_points: Fraction) -> list[str]:
        """Invisible text (render mode 3) in each cell, so the page can be searched."""
        if not page.text:
            return []
        lines = ["BT", "3 Tr"]
        for run in _text_runs(page.text):
            first = run[0]
            size = Fraction(first.height, _UNITS_PER_POINT)
            width = Fraction(first.width, _UNITS_PER_POINT)
            baseline = Fraction(first.y, _UNITS_PER_POINT) + size * _BASELINE
            lines.append(f"/F1 {_number(size)} Tf")
            lines.append(f"{_number(100 * width / (size * _COURIER_ADVANCE))} Tz")
            x = Fraction(first.x, _UNITS_PER_POINT)
            lines.append(f"1 0 0 1 {_number(x)} {_number(height_points - baseline)} Tm")
            lines.append(_pdf_string("".join(mark.character for mark in run)) + " Tj")
        lines.append("ET")
        return lines

    def close(self) -> list[Path]:
        if not self._pages:
            return []
        # Written aside and renamed into place, so a reader never sees a partial file.
        temporary_filepath = self._filepath.with_name(self._filepath.name + ".tmp")
        temporary_filepath.write_bytes(self._serialise())
        temporary_filepath.replace(self._filepath)
        return [self._filepath]

    def _serialise(self) -> bytes:
        objects: list[bytes] = []

        def add(body: bytes) -> int:
            objects.append(body)
            return len(objects)

        catalog_number = add(b"")  # Filled in once the page tree number is known.
        pages_number = add(b"")
        font_number = add(
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier /Encoding /WinAnsiEncoding >>"
        )
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
                    f"/Contents {contents_number} 0 R "
                    f"/Resources << /Font << /F1 {font_number} 0 R >> >> >>".encode("ascii")
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

    Each dot is a zero-length stroke with round caps, which PDF draws as a
    filled circle the width of the line.

    Options: ``ink`` grey level from 0 (black) to 1 (white), default 0.15;
    ``text``, invisible text under the dots so the document can be searched
    and copied from, default yes; ``filename``, default ``job.pdf``.
    """

    def __init__(
        self,
        name: str,
        *,
        ink: float = 0.15,
        text: bool = True,
        filename: str = "job.pdf",
        **kwargs,
    ):
        super().__init__(name=name, **kwargs)
        self._ink = ink
        self._text = text
        self._filename = filename

    def open_document(self, dirpath: Path) -> Document:
        return _PdfDocument(dirpath / self._filename, self._ink, self._text)
