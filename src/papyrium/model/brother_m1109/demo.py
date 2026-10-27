"""The M-1109's demonstration page: Papyrium's own ESC/P job."""

from __future__ import annotations

from papyrium.language.escp.demo_parts import heading, waves
from papyrium.language.escp.writing import ESC, FF, line

SI, DC2 = b"\x0f", b"\x12"


def demo() -> bytes:
    return b"".join(
        [
            ESC + b"@" + ESC + b"x\x01",
            line(ESC + b"W\x01", "Brother M-1109", ESC + b"W\x00"),
            line("Papyrium's demonstration of the M-1109, Brother's 9-pin printer"),
            line("of 1985. This is near letter quality: each line is printed twice,"),
            line("the second pass a fraction of a dot lower, to fill in the strokes."),
            ESC + b"x\x00",
            heading("Draft, and its pitches"),
            line("Pica: 10 characters to the inch"),
            line(ESC + b"M", "Elite: 12 characters to the inch", ESC + b"P"),
            line(SI, "Condensed: 17 characters to the inch, 136 to the line", DC2),
            line(
                ESC + b"M" + SI,
                "Condensed elite: 20 characters to the inch, 160 to the line",
                DC2 + ESC + b"P",
            ),
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
            line(ESC + b"R\x02", "Germany:     Gr}~e aus M}nchen"),
            line(ESC + b"R\x09", "Norway:      Bl}b{rsyltet|y"),
            line(ESC + b"R\x0a", "Denmark II:  R|dgr|d med fl|de"),
            line(ESC + b"R\x0b", "England II:  `4.99 a pint", ESC + b"R\x00"),
            heading("Bit-image graphics at 144 dots to the inch"),
            waves(mode=7, width=576),
            FF,
        ]
    )  # fmt: skip
