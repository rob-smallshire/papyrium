"""The ESC/P international character sets.

Each set replaces the characters at twelve ASCII positions with national
characters. The tables are the facts listed in Epson's FX-series manuals
for ``ESC R n``.
"""

from __future__ import annotations

import enum

#: The ASCII codes each international set may redefine, in table order.
NATIONAL_CODES = (0x23, 0x24, 0x40, 0x5B, 0x5C, 0x5D, 0x5E, 0x60, 0x7B, 0x7C, 0x7D, 0x7E)


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


def _table(*code_points: int) -> dict[int, str]:
    return {code: chr(code_point) for code, code_point in zip(NATIONAL_CODES, code_points)}


_ASCII = (0x23, 0x24, 0x40, 0x5B, 0x5C, 0x5D, 0x5E, 0x60, 0x7B, 0x7C, 0x7D, 0x7E)

_REPLACEMENTS: dict[CharacterSet, dict[int, str]] = {
    CharacterSet.USA: _table(*_ASCII),
    CharacterSet.FRANCE: _table(
        0x23, 0x24, 0xE0, 0xB0, 0xE7, 0xA7, 0x5E, 0x60, 0xE9, 0xF9, 0xE8, 0xA8
    ),
    CharacterSet.GERMANY: _table(
        0x23, 0x24, 0xA7, 0xC4, 0xD6, 0xDC, 0x5E, 0x60, 0xE4, 0xF6, 0xFC, 0xDF
    ),
    CharacterSet.UK: _table(0xA3, 0x24, 0x40, 0x5B, 0x5C, 0x5D, 0x5E, 0x60, 0x7B, 0x7C, 0x7D, 0x7E),
    CharacterSet.DENMARK: _table(
        0x23, 0x24, 0x40, 0xC6, 0xD8, 0xC5, 0x5E, 0x60, 0xE6, 0xF8, 0xE5, 0x7E
    ),
    CharacterSet.SWEDEN: _table(
        0x23, 0xA4, 0xC9, 0xC4, 0xD6, 0xC5, 0xDC, 0xE9, 0xE4, 0xF6, 0xE5, 0xFC
    ),
    CharacterSet.ITALY: _table(
        0x23, 0x24, 0x40, 0xB0, 0x5C, 0xE9, 0x5E, 0xF9, 0xE0, 0xF2, 0xE8, 0xEC
    ),
    CharacterSet.SPAIN: _table(
        0x20A7, 0x24, 0x40, 0xA1, 0xD1, 0xBF, 0x5E, 0x60, 0xA8, 0xF1, 0x7D, 0x7E
    ),
    CharacterSet.JAPAN: _table(
        0x23, 0x24, 0x40, 0x5B, 0xA5, 0x5D, 0x5E, 0x60, 0x7B, 0x7C, 0x7D, 0x7E
    ),
}


def character_for(code: int, character_set: CharacterSet) -> str:
    """The character a 7-bit printable *code* prints in *character_set*."""
    return _REPLACEMENTS[character_set].get(code, chr(code))


def parse_character_set(value: str | int | CharacterSet) -> CharacterSet:
    """A character set from its number or its name, such as ``uk`` or ``3``."""
    if isinstance(value, CharacterSet):
        return value
    if isinstance(value, int) or str(value).strip().isdigit():
        return CharacterSet(int(value))
    return CharacterSet[str(value).strip().upper()]
