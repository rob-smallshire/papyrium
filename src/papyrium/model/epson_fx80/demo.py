"""The FX-80's demonstration page: Papyrium's own ESC/P job."""

from __future__ import annotations

from papyrium.language.escp.demo_parts import SMILE, heading, waves
from papyrium.language.escp.writing import ESC, FF, line

SI, DC2 = b"\x0f", b"\x12"


def demo() -> bytes:
    return b"".join(
        [
            ESC + b"@",
            line(ESC + b"E" + ESC + b"W\x01", "Epson FX-80", ESC + b"W\x00" + ESC + b"F"),
            line("Papyrium's demonstration of the FX-80, Epson's 9-pin printer of 1983."),
            heading("Pitches"),
            line("Pica: 10 characters to the inch"),
            line(ESC + b"M", "Elite: 12 characters to the inch", ESC + b"P"),
            line(SI, "Condensed: about 17 characters to the inch, 132 to the line", DC2),
            line(ESC + b"p\x01", "Proportional: each letter as wide as it needs", ESC + b"p\x00"),
            heading("Styles"),
            line(
                ESC + b"E", "Emphasized", ESC + b"F", "   ",
                ESC + b"G", "Double-strike", ESC + b"H", "   ",
                ESC + b"4", "Italic", ESC + b"5", "   ",
                ESC + b"-\x01", "Underlined", ESC + b"-\x00",
            ),
            line(
                ESC + b"W\x01", "Double width", ESC + b"W\x00", "   E = mc",
                ESC + b"S\x00", "2", ESC + b"T", "   H", ESC + b"S\x01", "2", ESC + b"T", "O",
            ),
            heading("International character sets"),
            line(ESC + b"R\x02", "Germany:  Gr}~e aus M}nchen"),
            line(ESC + b"R\x01", "France:   Fran\\ais, {t{"),
            line(ESC + b"R\x04", "Denmark:  K|benhavn"),
            line(ESC + b"R\x07", "Spain:    Espa|a"),
            line(ESC + b"R\x03", "UK:       #4.99", ESC + b"R\x00"),
            heading("A character of your own"),
            ESC + b":\x00\x00\x00" + ESC + b"&\x00@@" + SMILE,
            line(ESC + b"%\x01\x00", "Have a nice day @", ESC + b"%\x00\x00"),
            heading("Bit-image graphics"),
            waves(),
            FF,
        ]
    )  # fmt: skip
