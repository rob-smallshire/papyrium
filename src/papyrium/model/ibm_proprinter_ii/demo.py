"""The Proprinter II's demonstration page: Papyrium's own Proprinter job."""

from __future__ import annotations

import textwrap

from papyrium.language.escp.demo_parts import heading, waves
from papyrium.language.escp.writing import ESC, FF, line

SO, SI, DC2 = b"\x0e", b"\x0f", b"\x12"

LETTER = (
    "The Proprinter II is IBM's 9-wire printer of 1986 for the Personal "
    "Computer. Besides draft it prints Fastfont, quicker at 12 to the inch, "
    "and two near letter qualities: NLQ, which the printer makes from the "
    "draft characters by filling in their lines, and NLQ II, characters of "
    "their own on a finer grid."
)

SAMPLE = "The quick brown fox jumps over the lazy dog"

#: A diamond for ESC =: an ordinary character with every column printed
#: in proportional spacing, and eleven columns, bit 7 the top wire.
DIAMOND = bytes([0x00, 0x00, 0x00, 0x00, 0x10, 0x28, 0x44, 0x82, 0x44, 0x28, 0x10, 0x00, 0x00])


def _download(code: int, character: bytes) -> bytes:
    """ESC = defining one draft character at *code*."""
    count = len(character) + 2
    return ESC + b"=" + bytes([count % 256, count // 256, 20, code]) + character


def _face(n: int, name: str) -> bytes:
    return line(ESC + b"I" + bytes([n]), f"{name:<22}", SAMPLE, ESC + b"I\x00")


def demo() -> bytes:
    return b"".join(
        [
            line(ESC + b"W\x01", "IBM Proprinter II", ESC + b"W\x00"),
            line(),
            ESC + b"I\x02",
            *(line(text) for text in textwrap.wrap(LETTER, 72)),
            ESC + b"I\x00",
            heading("Print faces"),
            _face(0, "Draft"),
            _face(1, "Fastfont"),
            _face(2, "NLQ"),
            _face(3, "NLQ II"),
            heading("Pitches and styles"),
            line(
                "Pica, 10 to the inch  ", ESC + b":", "Elite, 12 to the inch  ", DC2,
                SI, "Condensed, 17.1 to the inch", DC2,
            ),
            line(
                ESC + b"E", "Emphasized", ESC + b"F", "  ",
                ESC + b"G", "Double strike, in NLQ", ESC + b"H", "  ",
                SO, "Double width",
            ),
            line(
                ESC + b"-\x01", "Underscore", ESC + b"-\x00", "  ",
                ESC + b"_\x01", "Overscore", ESC + b"_\x00", "  ",
                "H", ESC + b"S\x01", "2", ESC + b"T", "O and E = mc",
                ESC + b"S\x00", "2", ESC + b"T",
            ),
            line(ESC + b"P\x01", "Proportional spacing: a slim i, a broad W.", ESC + b"P\x00"),
            heading("Character sets"),
            line(
                ESC + b"6", "Set 2 prints 128-159 and the card suits:  ",
                b"\x80\x81\x82\x83\x84\x85\x87\x8e\x8f\x90\x91\x9b\x9c\x9d  \x03\x04\x05\x06\x15",
                ESC + b"7",
            ),
            line(
                "Both sets print 160-254:  ",
                b"\xa0\xa1\xa2\xa3\xa4\xa5\xe0\xe1\xe2\xe3\xe4\xe5\xe6\xf1\xf2\xf3\xfb\xfd",
            ),
            heading("Block graphics, joining at 1/6 inch"),
            line(b"\xc9" + b"\xcd" * 20 + b"\xcb" + b"\xcd" * 10 + b"\xbb"),
            line(b"\xba", " Line drawing       ", b"\xba \xb0\xb1\xb2\xdb\xdb\xb2\xb1\xb0 \xba"),
            line(b"\xc8" + b"\xcd" * 20 + b"\xca" + b"\xcd" * 10 + b"\xbc"),
            heading("A download character, in draft and NLQ"),
            _download(ord("~"), DIAMOND),
            line(
                ESC + b"I\x04", "Draft  ~ ~ ~ ~     ",
                ESC + b"I\x06", "NLQ  ~ ~ ~ ~", ESC + b"I\x00",
            ),
            heading("Bit-image graphics"),
            waves(command=b"L"),
            FF,
        ]
    )  # fmt: skip
