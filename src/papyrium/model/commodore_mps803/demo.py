"""The MPS-803's demonstration page: Papyrium's own job in PETSCII, for the graphic set.

Lower case is reached within a line with code 17, which lasts to the end
of the line, and upper case and graphics again with 145.
"""

from __future__ import annotations

import math

CR = b"\r"
SO, SI, BS, POS, DOWN, RVS_ON, SUB, ESC = (
    b"\x0e",
    b"\x0f",
    b"\x08",
    b"\x10",
    b"\x11",
    b"\x12",
    b"\x1a",
    b"\x1b",
)
UP, RVS_OFF = b"\x91", b"\x92"


def _text(text: str) -> bytes:
    """ASCII *text* as PETSCII's business set codes: letters' cases swapped."""
    return text.swapcase().encode("ascii")


def demo() -> bytes:
    return b"".join(
        [
            SO + b"COMMODORE MPS-803" + SI + CR,
            DOWN + _text("Papyrium's demonstration of the MPS-803, Commodore's printer") + CR,
            DOWN + _text("for its serial bus, made by Brother in 1984.") + CR,
            CR,
            RVS_ON
            + b" GRAPHIC SET "
            + RVS_OFF
            + b"  ABCDEFGHIJKLMNOPQRSTUVWXYZ 0123456789 @[]^"
            + CR,
            DOWN
            + RVS_ON
            + _text(" Business set ")
            + RVS_OFF
            + _text("  abcdefghijklmnopqrstuvwxyz ABC")
            + CR,
            CR,
            b"STANDARD, " + SO + b"DOUBLE WIDTH" + SI + b", " + RVS_ON + b"REVERSE" + RVS_OFF,
            b" AND " + SO + RVS_ON + b"BOTH" + RVS_OFF + SI + CR,
            b'QUOTE MODE: "' + RVS_ON + b"\x12\x92\x0e\x93" + RVS_OFF + b'"' + CR,
            CR,
            _graphics(),
            CR,
            b"POSITIONS:" + POS + b"20" + b"COLUMN 20" + ESC + POS + b"\x01\x2c" + b"DOT 300" + CR,
            CR,
            _waves(),
        ]
    )


def _graphics() -> bytes:
    """PETSCII's box drawing, card suits and blocks, in the graphic set."""
    top = b"\xb0" + b"\xc0" * 30 + b"\xae"
    inside = b" \xc1 \xd3 \xda \xd8  \xd1 \xd7  \xa6\xa6\xa6 \xba\xbe\xbc\xbf\xa2\xa3"
    middle = b"\xdd" + inside.ljust(30) + b"\xdd"
    bottom = b"\xad" + b"\xc0" * 30 + b"\xbd"
    return top + CR + middle + CR + bottom + CR


def _waves(width: int = 470, rows: int = 21) -> bytes:
    """Two crossing waves as bit images of seven dots a column, the paper
    fed 7/72 inch after each band, over a rule repeated with SUB."""

    def ink(x: int, y: int) -> bool:
        phase = 4 * math.pi * x / width
        first = rows / 2 - (rows / 2 - 2) * math.sin(phase)
        second = rows / 2 - (rows / 2 - 2) * math.cos(phase / 2)
        return abs(y - first) < 1.0 or abs(y - second) < 1.0

    out = bytearray(BS)
    for top in range(0, rows, 7):
        out += bytes(
            0x80 | sum(1 << pin for pin in range(7) if ink(x, top + pin)) for x in range(width)
        )
        out += CR
    # A rule along the bottom wire: SUB repeats a column, 256 for a count of 0.
    out += SUB + bytes([0, 0xC0]) + SUB + bytes([width - 256, 0xC0]) + CR
    return bytes(out + SI)
