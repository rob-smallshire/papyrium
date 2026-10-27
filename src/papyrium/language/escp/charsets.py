"""The ESC/P character ROM's international characters and national sets.

The FX character ROM keeps 32 international characters at locations 0-31
(and their italics at 128-159). An international set prints them in
place of up to twelve ASCII characters: each national code points at one
of those locations. The tables are the facts listed in Epson's FX-series
manuals for ``ESC R n``; Norway, Denmark II and England II are the
Brother M-1109's additions, and Spain II and Latin America the Epson
LX-800's. Each printer numbers its sets for ``ESC R`` in its own order,
and may depart from a set at a few codes.

Characters some sets need beyond the 32 international ones are at
locations 0x100 and up, and the IBM PC table's at 0x200 and up, clear of
the italic bit (0x80).
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

#: Characters beyond the 32 international ones, at locations 0x100 on.
EXTRA_LOCATION = 0x100
EXTRA_CHARACTERS = ("á", "í", "ó", "ú", "´")
_A_ACUTE, _I_ACUTE, _O_ACUTE, _U_ACUTE, _ACUTE_ACCENT = (EXTRA_LOCATION + i for i in range(5))

#: The upper half of the IBM PC character set (code page 437), which ESC t 1
#: puts at codes 128-255, at locations 0x200 on.
IBM_LOCATION = 0x200

#: The IBM PC's symbols at codes 0-31, the additional set of IBM mode, at
#: locations 0x300 on; code 0 is a slashed zero.
ADDITIONAL_LOCATION = 0x300
#: The low codes IBM character set #2 prints: the card suits and the section sign.
SET_2_LOW_CODES = frozenset({3, 4, 5, 6, 21})

ADDITIONAL_CHARACTERS = ("0\u0338", *"☺☻♥♦♣♠•◘○◙♂♀♪♫☼►◄↕‼¶§▬↨↑↓→←∟↔▲▼")


class CharacterSet(enum.IntEnum):
    """The international character sets.

    The values are the FX-80's and M-1109's ``ESC R`` numbers; each
    printer's own numbering is its mechanism's ``character_sets``.
    """

    USA = 0
    FRANCE = 1
    GERMANY = 2
    UK = 3
    DENMARK = 4
    SWEDEN = 5
    ITALY = 6
    SPAIN = 7
    JAPAN = 8
    NORWAY = 9
    DENMARK_II = 10
    UK_II = 11
    SPAIN_II = 12
    LATIN_AMERICA = 13


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
    CharacterSet.NORWAY: {
        36: 11, 64: 29, 91: 18, 92: 20, 93: 13, 94: 25,
        96: 30, 123: 19, 124: 21, 125: 14, 126: 28,
    },
    CharacterSet.DENMARK_II: {
        64: 29, 91: 18, 92: 20, 93: 13, 94: 25, 96: 30, 123: 19, 124: 21, 125: 14, 126: 28,
    },
    CharacterSet.UK_II: {96: 6},
    CharacterSet.SPAIN_II: {
        64: _A_ACUTE, 91: 7, 92: 9, 93: 8, 94: 30,
        123: _I_ACUTE, 124: 10, 125: _O_ACUTE, 126: _U_ACUTE,
    },
    CharacterSet.LATIN_AMERICA: {
        64: _A_ACUTE, 91: 7, 92: 9, 93: 8, 94: 30, 96: 28,
        123: _I_ACUTE, 124: 10, 125: _O_ACUTE, 126: _U_ACUTE,
    },
}  # fmt: skip

#: Each printer's ``ESC R`` sets, in its numbering.
FX_CHARACTER_SETS = tuple(CharacterSet(n) for n in range(9))
M1109_CHARACTER_SETS = FX_CHARACTER_SETS + (
    CharacterSet.NORWAY, CharacterSet.DENMARK_II, CharacterSet.UK_II,
)  # fmt: skip
LX800_CHARACTER_SETS = FX_CHARACTER_SETS + (
    CharacterSet.NORWAY, CharacterSet.DENMARK_II, CharacterSet.SPAIN_II,
    CharacterSet.LATIN_AMERICA,
)  # fmt: skip


#: A printer's departures from the sets above: for a set, the ROM location
#: a national code prints instead.
NationalDifferences = dict[CharacterSet, dict[int, int]]

#: The Star LC-10 prints an acute accent at 96 in Spain I and Spain II.
LC10_NATIONAL_DIFFERENCES: NationalDifferences = {
    CharacterSet.SPAIN: {96: _ACUTE_ACCENT},
    CharacterSet.SPAIN_II: {96: _ACUTE_ACCENT},
}


def rom_location(
    code: int, character_set: CharacterSet, differences: NationalDifferences | None = None
) -> int:
    """The ROM location a 7-bit *code* prints in *character_set*, on a
    printer that departs from the set by *differences*."""
    different = (differences or {}).get(character_set, {})
    if code in different:
        return different[code]
    return _LOCATIONS[character_set].get(code, code)


def character_at(location: int) -> str:
    """The character at an upright ROM *location*."""
    if location >= ADDITIONAL_LOCATION:
        return ADDITIONAL_CHARACTERS[location - ADDITIONAL_LOCATION]
    if location >= IBM_LOCATION:
        if location - IBM_LOCATION == 0x7F:
            return " "  # IBM code 255 prints blank.
        return bytes([0x80 + location - IBM_LOCATION]).decode("cp437")
    if location >= EXTRA_LOCATION:
        return EXTRA_CHARACTERS[location - EXTRA_LOCATION]
    if location < len(INTERNATIONAL_CHARACTERS):
        return INTERNATIONAL_CHARACTERS[location]
    return chr(location)


def character_for(
    code: int, character_set: CharacterSet, differences: NationalDifferences | None = None
) -> str:
    """The character a 7-bit printable *code* prints in *character_set*."""
    return character_at(rom_location(code, character_set, differences))


def parse_character_set(
    value: str | int | CharacterSet, sets: tuple[CharacterSet, ...] = M1109_CHARACTER_SETS
) -> CharacterSet:
    """One of *sets*, by name, such as ``uk``, or by its number there, such as ``3``.

    Raises:
        KeyError: No set has that name.
        ValueError: *sets* has no such set.
    """
    if isinstance(value, int) or str(value).strip().isdigit():
        number = int(value)
        if not 0 <= number < len(sets):
            raise ValueError(f"no character set {number}")
        return sets[number]
    character_set = (
        value if isinstance(value, CharacterSet) else CharacterSet[str(value).strip().upper()]
    )
    if character_set not in sets:
        raise ValueError(f"no character set {character_set.name.lower()}")
    return character_set
