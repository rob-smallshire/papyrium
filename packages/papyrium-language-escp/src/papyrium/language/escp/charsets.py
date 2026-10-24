"""The ESC/P character ROM's international characters and national sets.

The FX character ROM keeps 32 international characters at locations 0-31
(and their italics at 128-159). An international set prints them in
place of up to twelve ASCII characters: each national code points at one
of those locations. The tables are the facts listed in Epson's FX-series
manuals for ``ESC R n``.
"""

from __future__ import annotations

import enum

#: The ASCII codes each international set may redefine.
NATIONAL_CODES = (0x23, 0x24, 0x40, 0x5B, 0x5C, 0x5D, 0x5E, 0x60, 0x7B, 0x7C, 0x7D, 0x7E)

#: The characters at ROM locations 0-31, by Unicode code point.
INTERNATIONAL_CHARACTERS = tuple(
    chr(code_point)
    for code_point in (
        0xE0, 0xE8, 0xF9, 0xF2, 0xEC, 0xB0, 0xA3, 0xA1,
        0xBF, 0xD1, 0xF1, 0xA4, 0x20A7, 0xC5, 0xE5, 0xE7,
        0xA7, 0xDF, 0xC6, 0xE6, 0xD8, 0xF8, 0xA8, 0xC4,
        0xD6, 0xDC, 0xE4, 0xF6, 0xFC, 0xC9, 0xE9, 0xA5,
    )
)  # fmt: skip


class CharacterSet(enum.IntEnum):
    """The ``ESC R n`` international character sets, by their ``n``."""

    USA = 0
    FRANCE = 1
    GERMANY = 2
    UK = 3
    DENMARK = 4
    SWEDEN = 5
    ITALY = 6
    SPAIN = 7
    JAPAN = 8


#: For each set, the ROM location each redefined national code prints.
_LOCATIONS: dict[CharacterSet, dict[int, int]] = {
    CharacterSet.USA: {},
    CharacterSet.FRANCE: {64: 0, 91: 5, 92: 15, 93: 16, 123: 30, 124: 2, 125: 1, 126: 22},
    CharacterSet.GERMANY: {64: 16, 91: 23, 92: 24, 93: 25, 123: 26, 124: 27, 125: 28, 126: 17},
    CharacterSet.UK: {35: 6},
    CharacterSet.DENMARK: {91: 18, 92: 20, 93: 13, 123: 19, 124: 21, 125: 14},
    CharacterSet.SWEDEN: {
        36: 11, 64: 29, 91: 23, 92: 24, 93: 13, 94: 25,
        96: 30, 123: 26, 124: 27, 125: 14, 126: 28,
    },
    CharacterSet.ITALY: {91: 5, 93: 30, 96: 2, 123: 0, 124: 3, 125: 1, 126: 4},
    CharacterSet.SPAIN: {35: 12, 91: 7, 92: 9, 93: 8, 123: 22, 124: 10},
    CharacterSet.JAPAN: {92: 31},
}  # fmt: skip


def rom_location(code: int, character_set: CharacterSet) -> int:
    """The ROM location a 7-bit *code* prints in *character_set*."""
    return _LOCATIONS[character_set].get(code, code)


def character_at(location: int) -> str:
    """The character at a 7-bit ROM *location*."""
    if location < len(INTERNATIONAL_CHARACTERS):
        return INTERNATIONAL_CHARACTERS[location]
    return chr(location)


def character_for(code: int, character_set: CharacterSet) -> str:
    """The character a 7-bit printable *code* prints in *character_set*."""
    return character_at(rom_location(code, character_set))


def parse_character_set(value: str | int | CharacterSet) -> CharacterSet:
    """A character set from its number or its name, such as ``uk`` or ``3``."""
    if isinstance(value, CharacterSet):
        return value
    if isinstance(value, int) or str(value).strip().isdigit():
        return CharacterSet(int(value))
    return CharacterSet[str(value).strip().upper()]
