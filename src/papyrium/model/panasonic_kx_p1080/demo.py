"""The KX-P1080's demonstration page: Papyrium's own ESC/P job."""

from __future__ import annotations

from papyrium.language.escp.demo_parts import heading, waves
from papyrium.language.escp.writing import ESC, FF, line

SI, DC2 = b"\x0f", b"\x12"

LETTER = (
    "The KX-P1080 is Panasonic's 9-pin printer. It speaks the Epson FX-80's "
    "language with Epson's near letter quality and some commands of "
    "Panasonic's own: a choice of four pitches, characters you design "
    "yourself, and proportional spacing in near letter quality, as this "
    "paragraph is printed, its words spread so that both margins are straight."
)

#: A download character: a small printer, nine columns of eight dots.
PRINTER_GLYPH = bytes([0x1E, 0x12, 0x7F, 0x41, 0x5D, 0x41, 0x7F, 0x12, 0x1E])


def demo() -> bytes:
    return b"".join(
        [
            ESC + b"@" + ESC + b"n",
            ESC + b"a\x02", line("10 November 1986"),
            ESC + b"a\x01", line(ESC + b"W\x01", "Panasonic KX-P1080", ESC + b"W\x00"),
            ESC + b"a\x00", line(), line("Dear reader,"), line(),
            ESC + b"p\x01" + ESC + b"a\x03", line(LETTER), ESC + b"a\x00" + ESC + b"p\x00",
            line(),
            line("Yours sincerely,"), line(),
            line(ESC + b"4", "The KX-P1080", ESC + b"5"),
            ESC + b"P",
            heading("Draft, and its four pitches"),
            line(ESC + b"w\x00", "Pica: 10 characters to the inch"),
            line(ESC + b"w\x01", "Elite: 12 characters to the inch"),
            line(ESC + b"w\x02", "Semi-compressed: 15 characters to the inch, 120 to the line"),
            line(ESC + b"w\x03", "Compressed: 17 characters to the inch, 137 to the line"),
            ESC + b"w\x00",
            heading("Styles"),
            line(
                ESC + b"E", "Emphasized", ESC + b"F", "   ",
                ESC + b"G", "Double strike", ESC + b"H", "   ",
                ESC + b"4", "Italic", ESC + b"5", "   ",
                ESC + b"-\x01", "Underlined", ESC + b"-\x00", "   ",
                ESC + b"W\x01", "Wide", ESC + b"W\x00",
            ),
            line(
                "Super", ESC + b"S\x00", "script", ESC + b"T", " and sub",
                ESC + b"S\x01", "script", ESC + b"T", "   ",
                ESC + b"p\x01", "Proportional spacing, in draft too", ESC + b"p\x00",
            ),
            line(ESC + b"n" + ESC + b"4", "Near letter quality italic", ESC + b"5" + ESC + b"P"),
            heading("International character sets"),
            line(ESC + b"R\x03", "England:  #12 for tea"),
            line(ESC + b"R\x02", "Germany:  Gr}~e aus M}nchen"),
            line(ESC + b"R\x07", "Spain:    [Hola, Espa|a!", ESC + b"R\x00"),
            heading("A character of your own"),
            ESC + b"y\x7e" + PRINTER_GLYPH,
            line("ESC y gives code 126 a new shape: ~ ~ ~", ESC + b"z\x7e"),
            heading("Bit-image graphics"),
            waves(),
            FF,
        ]
    )  # fmt: skip
