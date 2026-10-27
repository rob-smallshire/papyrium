"""The LX-800's demonstration page: Papyrium's own ESC/P job."""

from __future__ import annotations

from papyrium.language.escp.demo_parts import heading, waves
from papyrium.language.escp.writing import ESC, FF, line

SI, DC2 = b"\x0f", b"\x12"

LETTER = (
    "The LX-800 is Epson's 9-pin printer of 1987. Like the FX-80 before it, "
    "it prints quick drafts, but it also prints near letter quality, striking "
    "each line twice to fill in its characters, and in near letter quality it "
    "can centre a line, set it flush right, or justify a paragraph, as this "
    "one is, spreading its words so that both margins are straight."
)


def demo() -> bytes:
    return b"".join(
        [
            ESC + b"@" + ESC + b"x\x01",
            ESC + b"a\x02", line("26 October 1987"),
            ESC + b"a\x01", line(ESC + b"W\x01", "Epson LX-800", ESC + b"W\x00"),
            ESC + b"a\x00", line(), line("Dear reader,"), line(),
            ESC + b"a\x03", line(LETTER), ESC + b"a\x00",
            line(),
            line(
                "Its IBM PC table has mathematics: ", ESC + b"t\x01",
                b"\xe3 \xf7 3.14159, \xe0\xfd \xf2 0, \xf1\xfb2, \xab + \xac", ESC + b"t\x00",
            ),
            line(), line("Yours sincerely,"), line(), line("The LX-800"),
            ESC + b"x\x00",
            heading("Draft, and its pitches"),
            line("Pica: 10 characters to the inch"),
            line(ESC + b"M", "Elite: 12 characters to the inch", ESC + b"P"),
            line(SI, "Condensed: 17 characters to the inch, 132 to the line", DC2),
            line(
                ESC + b"M" + SI,
                "Condensed elite: 20 characters to the inch, 160 to the line",
                DC2 + ESC + b"P",
            ),
            heading("Styles, by master select"),
            line(
                ESC + b"!\x08", "Emphasized", ESC + b"!\x00", "   ",
                ESC + b"!\x40", "Italic", ESC + b"!\x00", "   ",
                ESC + b"!\x80", "Underlined", ESC + b"!\x00", "   ",
                ESC + b"!\x20", "Double width", ESC + b"!\x00",
            ),
            heading("International character sets"),
            line(ESC + b"R\x02", "Germany:        Gr}~e aus M}nchen"),
            line(ESC + b"R\x0b", "Spain II:       [Hola, Espa|a!"),
            line(ESC + b"R\x0c", "Latin America:  El ping`ino", ESC + b"R\x00"),
            heading("Bit-image graphics"),
            waves(),
            FF,
        ]
    )  # fmt: skip
