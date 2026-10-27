#!/usr/bin/env python3
"""Extract the Star LC-10's draft and NLQ fonts from its firmware ROM.

Reads the 64K program ROM (IC4, a 27512) from
docs/local/star-lc10/LC10-NX1P-1.5CL.bin, checks it is the dump this tool
was written for, and writes the dot font files of papyrium-font-lc10.

The ROM is Star's and is never committed; using it was Rob's decision
(see docs/star-lc10-firmware.md).

Usage: extract.py [ROM_FILEPATH]
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

REPO_DIRPATH = Path(__file__).resolve().parent.parent.parent
ROM_FILEPATH = REPO_DIRPATH / "docs" / "local" / "star-lc10" / "LC10-NX1P-1.5CL.bin"
#: The LC-10 Colour's firmware, version 1.5 (CRC32 d0a807ec).
ROM_SHA1 = "d2fc05e55ee2b112d6ea3517cc9e554d996c8156"

FONT_DIRPATH = REPO_DIRPATH / "packages/papyrium-font-lc10/src/papyrium/font/lc10"

SLASHED_ZERO = "0̸"
#: The character at each of the 211 locations every table holds: the
#: slashed zero, the IBM PC's low symbols, ASCII, the IBM PC's upper half
#: to 0xAF, its Greek and mathematical signs from 0xE0 (with Ø for its
#: phi, an acute accent for its lower integral half and the degree sign
#: for its upper one, which print from the block graphics instead), then
#: the diaeresis for its blank, and ø, ¤ and ß.
LOCATIONS = (
    SLASHED_ZERO,
    *"☺☻♥♦♣♠•◘○◙♂♀♪♫☼►◄↕‼¶§▬↨↑↓→←∟↔▲▼",
    *(chr(code) for code in range(0x20, 0x7F)),
    *"⌂ÇüéâäàåçêëèïîìÄÅÉæÆôöòûùÿÖÜ¢£¥₧ƒáíóúñÑªº¿⌐¬½¼¡«»",
    *"αβΓπΣσµτΦΘΩδ∞Øε∩≡±≥≤°´÷≈°∙·√ⁿ²■¨",
    *"ø¤ß",
)
#: Location 0xC8, the IBM PC's degree sign, repeats 0xC4's.
DUPLICATE_LOCATIONS = {0xC8: 0xC4}

# Elite draft: a header byte then 9 columns of 8 dots, bit 7 the top and a 1
# bit a dot. Header bit 7 set puts the character on the upper eight pins,
# clear on the lower eight; bits 4-6 and 0-3 are the first and last columns
# that proportional spacing allows for.
DRAFT_TABLE = 0x1A60
DRAFT_RECORD = 10
DRAFT_ROWS, DRAFT_COLUMNS = 9, 11

# Block graphics: 11 columns of 8 dots, no header, for IBM codes 0xB0-0xDF
# and, at indices 0x30 and 0x31, the integral halves 0xF4 and 0xF5. The
# printer's cell is 12 dots high: after the line it feeds four dots and
# prints the column's two lowest dots twice more beneath it.
BLOCK_TABLE = 0x229E
BLOCK_RECORD = 11
BLOCK_CHARACTERS = "░▒▓│┤╡╢╖╕╣║╗╝╜╛┐└┴┬├─┼╞╟╚╔╩╦╠═╬╧╨╤╥╙╘╒╓╫╪┘┌█▄▌▐▀⌠⌡"
BLOCK_ROWS = 12

# NLQ: eight tables of 211 four-byte entries from 0: header, width and a
# big-endian address of the first pass's columns; the second pass's are a
# fixed distance on. The header is bit 7 as for draft, then the left space
# (bits 4-6) and the right space (bits 0-3) about the width, in 1/240 inch
# columns, filling 23 columns (pica) or 19 (elite).
NLQ_ENTRY = 4
NLQ_TABLE_ENTRIES = 211
NLQ_ADDRESS_BASE = 0x8000
NLQ_SECOND_PASS = 0x2C23
NLQ_ROWS = 18
NLQ_TABLES = {
    "courier": 0,
    "orator-small-capitals": 1,
    "orator": 2,
    "sanserif": 3,
}
NLQ_ELITE_TABLE_OFFSET = 4
NLQ_COLUMNS = {"pica": 24, "elite": 20}


def read_rom(filepath: Path) -> bytes:
    data = filepath.read_bytes()
    digest = hashlib.sha1(data).hexdigest()
    if digest != ROM_SHA1:
        raise SystemExit(f"{filepath} is not the expected LC-10 ROM (SHA-1 {digest})")
    return data


def draft_glyph(rom: bytes, location: int) -> set[tuple[int, int]]:
    """The dots (column, row) of the draft character at *location*."""
    at = DRAFT_TABLE + location * DRAFT_RECORD
    lower = 0 if rom[at] & 0x80 else 1
    return {
        (column, row + lower)
        for column, byte in enumerate(rom[at + 1 : at + DRAFT_RECORD])
        for row in range(8)
        if byte & (0x80 >> row)
    }


def block_glyph(rom: bytes, index: int) -> set[tuple[int, int]]:
    """The dots (column, row) of the block graphics character at *index*."""
    at = BLOCK_TABLE + index * BLOCK_RECORD
    dots = set()
    for column, byte in enumerate(rom[at : at + BLOCK_RECORD]):
        for row in range(BLOCK_ROWS):
            # Rows 8-11 repeat the two lowest dots, bits 1 and 0.
            bit = row if row < 8 else 6 + row % 2
            if byte & (0x80 >> bit):
                dots.add((column, row))
    return dots


def pica_draft_glyph(rom: bytes, location: int) -> set[tuple[int, int]]:
    """The dots (column, row) of the pica draft character at *location*.

    Pica draft is made from Sanserif's second NLQ pass at half width: each
    column ORs two of its columns, less any dot in the column before, and
    the left space is halved too.
    """
    at = (NLQ_TABLES["sanserif"] * NLQ_TABLE_ENTRIES + location) * NLQ_ENTRY
    header, width = rom[at], rom[at + 1]
    start = int.from_bytes(rom[at + 2 : at + 4], "big") - NLQ_ADDRESS_BASE + NLQ_SECOND_PASS
    lower = 0 if header & 0x80 else 1
    left = ((header >> 4) & 0x07) // 2
    dots, previous = set(), 0
    for column in range(width // 2):
        byte = rom[start + 2 * column] | rom[start + 2 * column + 1]
        byte &= ~previous
        previous = byte
        for row in range(8):
            if byte & (0x80 >> row):
                dots.add((left + column, row + lower))
    return dots


def nlq_glyph(rom: bytes, table: int, location: int) -> set[tuple[int, int]]:
    """The dots (column, row) of an NLQ character, placed in its cell."""
    at = (table * NLQ_TABLE_ENTRIES + location) * NLQ_ENTRY
    header, width = rom[at], rom[at + 1]
    first = int.from_bytes(rom[at + 2 : at + 4], "big") - NLQ_ADDRESS_BASE
    lower = 0 if header & 0x80 else 2
    left = (header >> 4) & 0x07
    dots = set()
    for pass_, start in enumerate((first, first + NLQ_SECOND_PASS)):
        for column, byte in enumerate(rom[start : start + width]):
            for pin in range(8):
                if byte & (0x80 >> pin):
                    dots.add((left + column, 2 * pin + pass_ + lower))
    return dots


def check_duplicates(name: str, glyph_at) -> None:
    for location, same in DUPLICATE_LOCATIONS.items():
        if glyph_at(location) != glyph_at(same):
            raise SystemExit(f"{name}: location {location:#x} differs from {same:#x}")


def glyphs(glyph_at) -> dict[str, set]:
    result = {}
    for location, character in enumerate(LOCATIONS):
        if location not in DUPLICATE_LOCATIONS:
            result[character] = glyph_at(location)
    return result


def font_text(header: list[str], rows: int, columns: int, glyphs: dict[str, set]) -> str:
    lines = [f"# {line}" if line else "#" for line in header]
    lines += [f"rows {rows}", f"columns {columns}", ""]
    for character in sorted(glyphs, key=lambda c: [ord(x) for x in c]):
        lines.append(" ".join(f"U+{ord(x):04X}" for x in character))
        dots = glyphs[character]
        for row in range(rows):
            cells = ("#" if (column, row) in dots else "." for column in range(columns))
            lines.append("".join(cells))
        lines.append("")
    return "\n".join(lines)


PROVENANCE = [
    "",
    "Extracted by tools/lc10-rom/extract.py from the LC-10 Colour's firmware",
    "ROM, version 1.5. The characters are Star's.",
]


def main(rom_filepath: Path) -> None:
    rom = read_rom(rom_filepath)
    assert len(LOCATIONS) == NLQ_TABLE_ENTRIES

    check_duplicates("draft", lambda location: pica_draft_glyph(rom, location))
    (FONT_DIRPATH / "draft.txt").write_text(
        font_text(
            ["lc10-draft: the Star LC-10's pica draft characters.", *PROVENANCE,
             "The printer makes them from Sanserif's second NLQ pass at half",
             "width. Columns are 1/120 inch apart; the cell is 12 columns, the last",
             "always blank. A character with a descender sits a pin lower."],
            DRAFT_ROWS, DRAFT_COLUMNS, glyphs(lambda location: pica_draft_glyph(rom, location)),
        ),
        encoding="ascii",
    )  # fmt: skip
    check_duplicates("draft-elite", lambda location: draft_glyph(rom, location))
    (FONT_DIRPATH / "draft-elite.txt").write_text(
        font_text(
            ["lc10-draft-elite: the Star LC-10's elite draft characters.", *PROVENANCE,
             "Columns are 1/120 inch apart; the cell is 10 columns, the last always",
             "blank. A character with a descender sits a pin lower."],
            DRAFT_ROWS, DRAFT_COLUMNS, glyphs(lambda location: draft_glyph(rom, location)),
        ),
        encoding="ascii",
    )  # fmt: skip

    (FONT_DIRPATH / "block-graphics.txt").write_text(
        font_text(
            ["lc10-block-graphics: the Star LC-10's IBM block graphics.", *PROVENANCE,
             "Columns are 1/120 inch apart, joining the next pica cell; rows are",
             "1/72 inch apart, rows 8-11 repeating rows 6 and 7, so that lines at",
             "1/6 inch spacing join."],
            BLOCK_ROWS, BLOCK_RECORD,
            {c: block_glyph(rom, index) for index, c in enumerate(BLOCK_CHARACTERS)},
        ),
        encoding="ascii",
    )  # fmt: skip

    for pitch, columns in NLQ_COLUMNS.items():
        for typeface, table in NLQ_TABLES.items():
            if pitch == "elite":
                table += NLQ_ELITE_TABLE_OFFSET
            name = typeface if pitch == "pica" else f"{typeface}-elite"

            def glyph_at(location, table=table):
                return nlq_glyph(rom, table, location)

            check_duplicates(name, glyph_at)
            (FONT_DIRPATH / f"nlq-{name}.txt").write_text(
                font_text(
                    [f"lc10-nlq-{name}: the Star LC-10's NLQ {typeface.replace('-', ' ')},",
                     f"{pitch}.", *PROVENANCE,
                     "Even rows are the pins of the first pass, odd rows of the second,",
                     "half a dot lower; a character with a descender sits two rows lower.",
                     f"Columns are 1/240 inch apart, {columns} to the {pitch} cell."],
                    NLQ_ROWS, columns, glyphs(glyph_at),
                ),
                encoding="ascii",
            )  # fmt: skip
    fonts = 2 * len(NLQ_TABLES) + 3
    print(f"{fonts} fonts written, the text fonts of {len(LOCATIONS) - 1} characters")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else ROM_FILEPATH)
