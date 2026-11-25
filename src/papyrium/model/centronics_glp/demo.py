"""The Centronics GLP's demonstration page: Papyrium's own job in its commands.

The job keeps to seven bits, as the Schneider NLQ401 receives them, so it
prints the same on every GLP: codes 128-255 are reached with ESC =, and
bit images use the seven pins below the top one.
"""

from __future__ import annotations

import math

from papyrium.font.glp import UPPER_HALF
from papyrium.language.escp.writing import CR_LF, ESC, line

NUL, SO, SI, DC2, DC4 = b"\x00", b"\x0e", b"\x0f", b"\x12", b"\x14"

#: Character set 2's German characters and the codes that print them.
_GERMAN = str.maketrans("§ÄÖÜäöüß", "@[\\]{|}~")


def demo(name: str, *, nlq: bool) -> bytes:
    """The demonstration page for the GLP sold as *name*, showing NLQ with *nlq*."""
    nlq_on, nlq_off = (ESC + b"x\x01", ESC + b"x\x00") if nlq else (b"", b"")
    quality = "near letter quality" if nlq else "draft"
    return b"".join(
        [
            ESC + b"7" + nlq_on,
            line(SO, name),
            line(f"Papyrium's demonstration of the {name}, the first Great Little"),
            line(f"Printer, made by Brother for Centronics in 1984. This is {quality}."),
            nlq_off,
            _heading("Draft, and its widths"),
            line("Pica: 10 characters to the inch, 80 to the line"),
            line(SI, "Condensed: 17 characters to the inch, 132 to the line", DC2),
            line(ESC + b"W\x01", "Enlarged: 5 to the inch", ESC + b"W\x00"),
            line(SI + ESC + b"W\x01", "Condensed enlarged: 8.5", ESC + b"W\x00" + DC2),
            _heading("Styles"),
            line(
                ESC + b"E",
                "Emphasized",
                ESC + b"F",
                ", ",
                ESC + b"G",
                "double strike",
                ESC + b"H",
                ", ",
                ESC + b"-\x01",
                "underlined",
                ESC + b"-\x00",
                ", E = mc",
                ESC + b"S\x00",
                "2",
                ESC + b"T",
                " and H",
                ESC + b"S\x01",
                "2",
                ESC + b"T",
                "O",
            ),
            _heading("Character set 2"),
            line(ESC + b"6", "Grüße aus München: Ä Ö Ü ä ö ü ß §".translate(_GERMAN), ESC + b"7"),
            _heading("The Amstrad CPC's graphics, after ESC ="),
            _graphics_box(),
            _heading("Bit image, seven pins at a time"),
            _waves(),
            *(
                [
                    _heading("Near letter quality"),
                    nlq_on,
                    line("Two passes, the second 1/216 inch below the first, on a grid"),
                    line("of 1/480 inch: The quick brown fox jumps over the lazy dog."),
                    nlq_off,
                ]
                if nlq
                else []
            ),
        ]
    )


def _heading(text: str) -> bytes:
    """A section heading: emphasized and underlined, a blank line above."""
    return line() + line(ESC + b"E" + ESC + b"-\x01", text, ESC + b"-\x00" + ESC + b"F")


def _graphics(text: str) -> bytes:
    """*text* with its CPC graphics characters reached through ESC =.

    Inside ESC = every byte prints a graphics character, so a space or
    any other ASCII character is printed after a NUL ends it.
    """
    out = bytearray()
    shifted = False
    for character in text:
        code = UPPER_HALF.find(character)
        if code > 0:
            if not shifted:
                out += ESC + b"="
                shifted = True
            out.append(code)
        else:
            if shifted:
                out += NUL
                shifted = False
            out += character.encode("ascii")
    if shifted:
        out += NUL
    return bytes(out)


def _graphics_box() -> bytes:
    rows = (
        "┌──────────────────────────────┐ ▘▝▀▖▌▞▛ ",
        "│ ☺ ☹  ♣ ♦ ♥ ♠  ○ ● □ ■  ♂ ♀ ♩ ♪ │ ▗▚▐▜▄▙▟█",
        "│ αβγδεθλμπσφψχωΣΩ  ¼ ½ ¾ ± ÷ │ ◤◥◢◣╱╲╳▒",
        "└──────────────────────────────┘ ⭡⭣⭠⭢▲▼▶◀",
    )
    return b"".join(_graphics(row) + CR_LF for row in rows)


#: Columns in each ESC K image: a count the seven-bit port can send.
_IMAGE_COLUMNS = 120


def _waves(width: int = 480, rows: int = 28) -> bytes:
    """Two crossing waves as ESC K bit images in bands of seven pins, the
    paper fed 7/72 inch between them; then the 1/6 inch spacing again."""

    def ink(x: int, y: int) -> bool:
        phase = 4 * math.pi * x / width
        first = rows / 2 - (rows / 2 - 3) * math.sin(phase)
        second = rows / 2 - (rows / 2 - 3) * math.cos(phase / 2)
        return abs(y - first) < 1.2 or abs(y - second) < 1.2 or y == rows - 1

    out = bytearray(ESC + b"3\x15")
    for top in range(0, rows, 7):
        columns = bytes(
            sum(0x40 >> pin for pin in range(7) if top + pin < rows and ink(x, top + pin))
            for x in range(width)
        )
        # A count of seven bits a byte: images of at most 127 columns.
        for start in range(0, width, _IMAGE_COLUMNS):
            image = columns[start : start + _IMAGE_COLUMNS]
            out += ESC + b"K" + bytes([len(image), 0]) + image
        out += CR_LF
    return bytes(out + ESC + b"2")
