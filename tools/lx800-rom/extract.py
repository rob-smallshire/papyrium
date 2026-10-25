#!/usr/bin/env python3
"""Extract the Epson LX-800's draft and NLQ Roman characters from its firmware ROM.

Reads the 32K program ROM (IC3C) from docs/local/epson-lx800/lx800.ic3c,
checks it is the dump this tool was written for, and writes the dot font
files of papyrium-font-lx800-draft and papyrium-font-lx800-nlq-roman.

The ROM is Epson's and is never committed; using its characters is Rob's
decision for this ROM (see README.md). This dump is a Cyrillic variant:
where the Western firmware has NLQ Sans Serif it has NLQ Cyrillic, so
Sans Serif cannot come from it.

Usage: extract.py [ROM_FILEPATH]
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

REPO_DIRPATH = Path(__file__).resolve().parent.parent.parent
ROM_FILEPATH = REPO_DIRPATH / "docs" / "local" / "epson-lx800" / "lx800.ic3c"
#: The dump MAME lists as lx800.ic3c (CRC32 da06c45b).
ROM_SHA1 = "9618c940dd10d5b43cd1edd5763b90e6447de667"

DRAFT_FILEPATH = (
    REPO_DIRPATH / "packages/papyrium-font-lx800-draft/src/papyrium/font/lx800_draft/glyphs.txt"
)
NLQ_FILEPATH = (
    REPO_DIRPATH
    / "packages/papyrium-font-lx800-nlq-roman/src/papyrium/font/lx800_nlq_roman/glyphs.txt"
)

#: The characters at ROM locations 0-31, as papyrium.language.escp.charsets
#: has them; the ROM keeps them in this order in both qualities.
INTERNATIONAL = tuple(
    chr(code_point)
    for code_point in (
        0xE0, 0xE8, 0xF9, 0xF2, 0xEC, 0xB0, 0xA3, 0xA1,
        0xBF, 0xD1, 0xF1, 0xA4, 0x20A7, 0xC5, 0xE5, 0xE7,
        0xA7, 0xDF, 0xC6, 0xE6, 0xD8, 0xF8, 0xA8, 0xC4,
        0xD6, 0xDC, 0xE4, 0xF6, 0xFC, 0xC9, 0xE9, 0xA5,
    )
)  # fmt: skip
SLASHED_ZERO = "0̸"

# Draft: 10-byte records, one per ROM location from location -10: a byte
# whose use is not known, then 9 columns of 8 dots, bit 7 the top, a 0 bit
# a dot. Location 127 holds the slashed zero.
DRAFT_TABLE = 0x2804
DRAFT_RECORD = 10
DRAFT_FIRST_LOCATION = -10
DRAFT_ROWS, DRAFT_COLUMNS = 9, 11

# NLQ: little-endian pointer tables to variable-length records.
NLQ_ASCII_POINTERS = 0x3278  # 94 records, "!" to "~"
NLQ_INTERNATIONAL_POINTERS = 0x3236  # locations 0-31 (and one more)
NLQ_IBM_POINTERS = 0x3336
#: The IBM PC characters NLQ_IBM_POINTERS points to, in order: those of the
#: upper half of code page 437 that are neither box drawing nor among the
#: international characters, except that the degree sign is here too and
#: phi is not.
NLQ_IBM_CHARACTERS = "Çâêëïîôûÿ¢ƒáíóúªº⌐¬½¼«»αΓπΣσµτΦΘΩδ∞ε∩≡±≥≤⌠⌡÷≈°∙·√ⁿ²■"
NLQ_ROWS, NLQ_COLUMNS = 18, 24


def read_rom(filepath: Path) -> bytes:
    data = filepath.read_bytes()
    digest = hashlib.sha1(data).hexdigest()
    if digest != ROM_SHA1:
        raise SystemExit(f"{filepath} is not the expected LX-800 ROM (SHA-1 {digest})")
    return data


def draft_glyph(rom: bytes, location: int) -> set[tuple[int, int]]:
    """The dots (column, row) of the draft character at *location*.

    A character that leaves its top row empty and uses its bottom row is
    printed a pin lower, so that its descender reaches the ninth pin.
    """
    at = DRAFT_TABLE + (location - DRAFT_FIRST_LOCATION) * DRAFT_RECORD
    columns = rom[at + 1 : at + DRAFT_RECORD]
    dots = {
        (column, row)
        for column, byte in enumerate(columns)
        for row in range(8)
        if not byte & (0x80 >> row)
    }
    rows = {row for _, row in dots}
    if dots and 0 not in rows and 7 in rows:
        dots = {(column, row + 1) for column, row in dots}
    return dots


def _pointer(rom: bytes, table: int, index: int) -> int:
    return int.from_bytes(rom[table + 2 * index : table + 2 * index + 2], "little")


def nlq_glyph(rom: bytes, at: int) -> set[tuple[int, int]]:
    """The dots (column, row) of the NLQ record at *at*, on the 1/240 inch grid.

    A record is a header byte, then for each pass in turn the ninth pin's
    dots (when the header asks for them) and the eight upper pins' columns.
    A header of 0xFF is followed by a flags byte and a width, and the
    columns are 1/240 inch apart; otherwise bits 0-3 are the width, bits
    4-6 a left offset, both in 1/120 inch columns, and bit 7 asks for the
    ninth pin, whose dots take two bytes a pass. The first pass's pins print
    the even rows, the second's the odd rows, the ninth pin rows 16 and 17.
    """
    head = rom[at]
    p = at + 1
    if head == 0xFF:
        flags, width = rom[p], rom[p + 1]
        p += 2
        offset, scale = 0, 1
        ninth_pin = bool(flags & 0x80)
        ninth_bytes = (width + 7) // 8
    else:
        width, offset, scale = head & 0x0F, (head >> 4) & 0x07, 2
        ninth_pin = bool(head & 0x80)
        ninth_bytes = 2
    dots = set()
    for pass_ in range(2):
        if ninth_pin:
            bits = int.from_bytes(rom[p : p + ninth_bytes], "big")
            p += ninth_bytes
            for column in range(width):
                if not (bits >> (8 * ninth_bytes - 1 - column)) & 1:
                    dots.add(((offset + column) * scale, 16 + pass_))
        for column in range(width):
            byte = rom[p + column]
            for pin in range(8):
                if not byte & (0x80 >> pin):
                    dots.add(((offset + column) * scale, 2 * pin + pass_))
        p += width
    return dots


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


def clipped(name: str, glyphs: dict[str, set], columns: int) -> dict[str, set]:
    """Drop, and say so, any dot beyond the matrix's last column."""
    result = {}
    for character, dots in glyphs.items():
        inside = {(c, r) for c, r in dots if c < columns}
        if inside != dots:
            lost = len(dots - inside)
            print(f"{name} {character!r}: {lost} dots beyond column {columns} dropped")
        result[character] = inside
    return result


PROVENANCE = [
    "",
    "Extracted by tools/lx800-rom/extract.py from the LX-800 firmware ROM",
    "(IC3C, the dump MAME lists as lx800.ic3c). The characters are Epson's.",
]


def main(rom_filepath: Path) -> None:
    rom = read_rom(rom_filepath)

    draft = {chr(code): draft_glyph(rom, code) for code in range(0x20, 0x7F)}
    draft.update({c: draft_glyph(rom, location) for location, c in enumerate(INTERNATIONAL)})
    draft[SLASHED_ZERO] = draft_glyph(rom, 127)
    # The ROM's draft a, i, o and u acute are not decoded yet: compose them
    # from its vowels and the acute accent of its own e acute.
    # The vowel keeps only its dots from row 2 down, so the i loses its dot.
    acute = draft["é"] - draft["e"]
    for accented, plain in zip("áíóú", "aiou"):
        draft[accented] = {(c, r) for c, r in draft[plain] if r >= 2} | acute
    DRAFT_FILEPATH.write_text(
        font_text(
            ["lx800-draft: the Epson LX-800's draft characters.", *PROVENANCE,
             "Columns are 1/120 inch apart; the last two are spacing. A character",
             "with a descender sits a pin lower. Dots in successive columns are",
             "kept as the ROM has them; the printer prints such a dot once.",
             "The a, i, o and u acute are composed from the ROM's vowels and the",
             "accent of its e acute."],
            DRAFT_ROWS, DRAFT_COLUMNS, clipped("draft", draft, DRAFT_COLUMNS),
        ),
        encoding="ascii",
    )  # fmt: skip

    nlq = {" ": set()}
    for index in range(94):
        nlq[chr(0x21 + index)] = nlq_glyph(rom, _pointer(rom, NLQ_ASCII_POINTERS, index))
    for location, character in enumerate(INTERNATIONAL):
        nlq[character] = nlq_glyph(rom, _pointer(rom, NLQ_INTERNATIONAL_POINTERS, location))
    for index, character in enumerate(NLQ_IBM_CHARACTERS):
        if character not in nlq:
            nlq[character] = nlq_glyph(rom, _pointer(rom, NLQ_IBM_POINTERS, index))
    NLQ_FILEPATH.write_text(
        font_text(
            ["lx800-nlq-roman: the Epson LX-800's near letter quality Roman.", *PROVENANCE,
             "Even rows are the pins of the first pass, odd rows of the second;",
             "rows 16 and 17 are the ninth pin. Columns are 1/240 inch apart."],
            NLQ_ROWS, NLQ_COLUMNS, clipped("nlq", nlq, NLQ_COLUMNS),
        ),
        encoding="ascii",
    )  # fmt: skip
    print(f"{len(draft)} draft and {len(nlq)} NLQ characters written")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else ROM_FILEPATH)
