"""A US Letter test page, as a PDF, with geometry that can be measured.

Written by hand so it needs nothing but Python: a one-inch grid with a
ruler, a border half an inch inside the sheet, diagonals, Helvetica text
from 6 to 48 points, and grey squares from 10% to 90%.
"""

from __future__ import annotations

WIDTH, HEIGHT = 612, 792  # US Letter, in points


def _content() -> str:
    ops = ["0.25 w"]
    # The one-inch grid, light grey.
    ops.append("0.8 G")
    for x in range(0, WIDTH + 1, 72):
        ops.append(f"{x} 0 m {x} {HEIGHT} l S")
    for y in range(0, HEIGHT + 1, 72):
        ops.append(f"0 {y} m {WIDTH} {y} l S")
    # The border, half an inch in, and its diagonals.
    ops.append("0 G 1 w")
    ops.append(f"36 36 {WIDTH - 72} {HEIGHT - 72} re S")
    ops.append(f"36 36 m {WIDTH - 36} {HEIGHT - 36} l S")
    ops.append(f"36 {HEIGHT - 36} m {WIDTH - 36} 36 l S")
    # A ruler along the top inside edge: ticks every 1/10 inch.
    for tenth in range(0, 76):
        x = 36 + tenth * 7.2
        length = 12 if tenth % 10 == 0 else 6 if tenth % 5 == 0 else 3
        ops.append(f"{x:.1f} {HEIGHT - 36} m {x:.1f} {HEIGHT - 36 - length} l S")
    # Text, in sizes from 6 to 48 points.
    y = HEIGHT - 90
    for size in (48, 36, 24, 18, 14, 12, 10, 8, 6):
        ops.append(f"BT /F1 {size} Tf 54 {y} Td (Papyrium {size} pt: The quick brown fox) Tj ET")
        y -= size * 1.4
    # Grey squares, 10% to 90%.
    for step in range(9):
        grey = 1 - (step + 1) / 10
        x = 54 + step * 54
        ops.append(f"{grey:.1f} g {x} 108 45 45 re f")
    ops.append("0 g")
    ops.append("BT /F1 10 Tf 54 90 Td (10%  20%  30%  40%  50%  60%  70%  80%  90% grey) Tj ET")
    return "\n".join(ops)


def test_page_pdf() -> bytes:
    """The test page as the bytes of a PDF file."""
    content = _content().encode("latin-1")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {WIDTH} {HEIGHT}] "
        "/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>".encode(),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(content)).encode() + b" >>\nstream\n" + content + b"\nendstream",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{number} 0 obj\n".encode() + body + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
    for offset in offsets:
        out += f"{offset:010d} 00000 n \n".encode()
    out += (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    )
    return bytes(out)
