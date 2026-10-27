"""The LC-10's demonstration page: Papyrium's own ESC/P job."""

from __future__ import annotations

import textwrap

from papyrium.language.escp.demo_parts import heading, waves
from papyrium.language.escp.writing import ESC, FF, line

SI, DC2 = b"\x0f", b"\x12"

LETTER = (
    "The LC-10 is Star's 9-pin printer of 1987, the Multi-Font: four near "
    "letter quality typefaces, each in pica and elite, chosen from its front "
    "panel or by your program, and italics of every one of them."
)


def _typeface(n: int, name: str) -> bytes:
    return line(
        ESC + b"k" + bytes([n]), f"{name:<26}", ESC + b"4", "Italic", ESC + b"5", "  ",
        ESC + b"M", "and elite, 12 to the inch", ESC + b"P",
    )  # fmt: skip


def demo() -> bytes:
    return b"".join(
        [
            ESC + b"@" + ESC + b"x\x01",
            line(ESC + b"W\x01", "Star LC-10", ESC + b"W\x00"),
            line(),
            *(line(text) for text in textwrap.wrap(LETTER, 72)),
            heading("Near letter quality"),
            _typeface(0, "Courier"),
            _typeface(1, "Sanserif"),
            _typeface(2, "Orator, small capitals"),
            _typeface(3, "Orator, lower case"),
            ESC + b"k\x00",
            line(ESC + b"h\x01", "Double size", ESC + b"h\x00", "  hangs from the cap line"),
            line(
                ESC + b"p\x01",
                "Proportional spacing: each letter as wide as it needs, a slim i, a broad W.",
                ESC + b"p\x00",
            ),
            ESC + b"x\x00",
            heading("Draft, and its pitches"),
            line("Pica: 10 characters to the inch  ", ESC + b"4", "and italic", ESC + b"5"),
            line(ESC + b"M", "Elite: 12 characters to the inch", ESC + b"P"),
            line(SI, "Condensed: 17 characters to the inch, 137 to the line", DC2),
            line(
                ESC + b"M" + SI,
                "Condensed elite: 20 characters to the inch, 160 to the line",
                DC2 + ESC + b"P",
            ),
            heading("International character sets"),
            line(ESC + b"R\x02", "Germany:   Gr}~e aus M}nchen"),
            line(ESC + b"R\x04", "Denmark I: Bl{b{rgr|d med fl|de", ESC + b"R\x00"),
            heading("Block graphics, joining at 1/6 inch"),
            ESC + b"t\x01",
            line(b"\xc9" + b"\xcd" * 20 + b"\xcb" + b"\xcd" * 10 + b"\xbb"),
            line(b"\xba", " The IBM PC table   ", b"\xba \xb0\xb1\xb2\xdb\xdb\xb2\xb1\xb0 \xba"),
            line(b"\xc8" + b"\xcd" * 20 + b"\xca" + b"\xcd" * 10 + b"\xbc"),
            ESC + b"t\x00",
            heading("Bit-image graphics"),
            waves(),
            FF,
        ]
    )  # fmt: skip
