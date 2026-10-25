"""Writing ESC/P jobs in code, for printers' demonstration pages and tests."""

from __future__ import annotations

from collections.abc import Callable

ESC = b"\x1b"
CR_LF = b"\r\n"
FF = b"\x0c"


def line(*parts: bytes | str) -> bytes:
    """*parts*, text in ASCII or bytes as they are, then CR LF."""
    return (
        b"".join(part.encode("ascii") if isinstance(part, str) else part for part in parts) + CR_LF
    )


def picture(width: int, rows: int, ink: Callable[[int, int], bool], *, mode: int = 1) -> bytes:
    """A picture *width* columns by *rows* dots, as bands of eight pins.

    *ink* says whether the dot at (column, row) is inked, row 0 the top.
    Each band is printed in the ``ESC *`` bit-image mode *mode* and the
    paper fed 8/72 inch between bands, so they meet; the line spacing is
    then 1/6 inch again.
    """
    out = bytearray(ESC + b"3\x18")
    for top in range(0, rows, 8):
        columns = bytes(
            sum(0x80 >> pin for pin in range(8) if top + pin < rows and ink(x, top + pin))
            for x in range(width)
        )
        out += ESC + b"*" + bytes([mode, width % 256, width // 256]) + columns + CR_LF
    return bytes(out + ESC + b"2")
