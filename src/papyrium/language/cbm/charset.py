"""The Commodore printers' character sets: PETSCII codes to the glyphs of the character generator.

The MPS-803's firmware turns a PETSCII code into the index of one of its
160 glyphs, $20-$BF, by a rule for each set: the graphic set (upper case
and graphics, secondary address 0) and the business set (lower and upper
case, secondary address 7). These follow its routines at $08EC and
$090B. Each glyph is named by the Unicode character it shows, PETSCII's
graphics among the Symbols for Legacy Computing.
"""

from __future__ import annotations

__all__ = ["GLYPH_CHARACTERS", "business_glyph", "glyph_character", "graphic_glyph"]


def graphic_glyph(code: int) -> int:
    """The glyph a printable *code* prints in the graphic set."""
    if code <= 0x60:
        return code
    if code <= 0x7F:
        return code + 0x40
    if code <= 0xDF:
        return code - 0x20
    if code <= 0xFE:
        return code - 0x60
    return 0xBE


def business_glyph(code: int) -> int:
    """The glyph a printable *code* prints in the business set."""
    if code < 0x80:
        return _business_low(code)
    # Codes $A0-$FF: the graphic set's arrangement, with the business
    # set's letters and three of its own symbols.
    glyph = code - 0x20
    while True:
        if glyph == 0x89:
            return 0x7D
        if glyph == 0x9A:
            return 0x7E
        if glyph <= 0xA0:
            return glyph
        glyph -= 0x40
        if glyph <= 0x7F:
            return _business_low(glyph)
        if glyph == 0x9F:
            return 0x7B


def _business_low(code: int) -> int:
    if code <= 0x40:
        return code
    if code <= 0x5A:
        return code + 0x20
    if code <= 0x60:
        return code
    if code <= 0x7A:
        return code - 0x20
    if code <= 0x7D:
        return code + 0x40
    return code - 0x03


def glyph_character(glyph: int) -> str | None:
    """The character glyph *glyph* shows; None for the one no code reaches."""
    return GLYPH_CHARACTERS[glyph - 0x20]


#: The characters of glyphs $20-$BF, from the PETSCII codes that reach
#: them: the graphic set's as PETSCII's unshifted characters, the business
#: set's as its shifted ones. Glyph $7F is never used.
GLYPH_CHARACTERS = (
    " ",
    "!",
    '"',
    "#",
    "$",
    "%",
    "&",
    "'",
    "(",
    ")",
    "*",
    "+",
    ",",
    "-",
    ".",
    "/",
    "0",
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    ":",
    ";",
    "<",
    "=",
    ">",
    "?",
    "@",
    "A",
    "B",
    "C",
    "D",
    "E",
    "F",
    "G",
    "H",
    "I",
    "J",
    "K",
    "L",
    "M",
    "N",
    "O",
    "P",
    "Q",
    "R",
    "S",
    "T",
    "U",
    "V",
    "W",
    "X",
    "Y",
    "Z",
    "[",
    "£",
    "]",
    "↑",
    "←",
    "─",
    "a",
    "b",
    "c",
    "d",
    "e",
    "f",
    "g",
    "h",
    "i",
    "j",
    "k",
    "l",
    "m",
    "n",
    "o",
    "p",
    "q",
    "r",
    "s",
    "t",
    "u",
    "v",
    "w",
    "x",
    "y",
    "z",
    "🮖",
    "🮘",
    "🮙",
    "✓",
    None,
    "\xa0",
    "▌",
    "▄",
    "▔",
    "▁",
    "▏",
    "▒",
    "▕",
    "🮏",
    "◤",
    "🮇",
    "├",
    "▗",
    "└",
    "┐",
    "▂",
    "┌",
    "┴",
    "┬",
    "┤",
    "▎",
    "▍",
    "🮈",
    "🮂",
    "🮃",
    "▃",
    "🭿",
    "▖",
    "▝",
    "┘",
    "▘",
    "▚",
    "─",
    "♠",
    "🭲",
    "🭸",
    "🭷",
    "🭶",
    "🭺",
    "🭱",
    "🭴",
    "╮",
    "╰",
    "╯",
    "🭼",
    "╲",
    "╱",
    "🭽",
    "🭾",
    "●",
    "🭻",
    "♥",
    "🭰",
    "╭",
    "╳",
    "○",
    "♣",
    "🭵",
    "♦",
    "┼",
    "🮌",
    "│",
    "π",
    "◥",
)
