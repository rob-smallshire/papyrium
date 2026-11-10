#!/usr/bin/env python3
"""Extract the Panasonic KX-P1080U's draft and NLQ characters from its firmware.

Reads the 16 KB EPROM (KX-P1080U.BIN) and the CPU's 4 KB internal ROM
(KX-P1080U-internal.bin, transcribed from the printer's own hex dump; see
docs/panasonic-kx-p1080-rom-recovery.md) from docs/local/panasonic-kx-p1080/,
checks they are the images this tool was written for, and writes the dot
font files of papyrium.font.kx_p1080.

The ROMs are Panasonic's and are never committed; using anything in them
was Rob's decision (2026-11-10).

Usage: extract.py [EPROM_FILEPATH [INTERNAL_ROM_FILEPATH]]
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

REPO_DIRPATH = Path(__file__).resolve().parent.parent.parent
LOCAL_DIRPATH = REPO_DIRPATH / "docs" / "local" / "panasonic-kx-p1080"
EPROM_FILEPATH = LOCAL_DIRPATH / "KX-P1080U.BIN"
INTERNAL_ROM_FILEPATH = LOCAL_DIRPATH / "KX-P1080U-internal.bin"
EPROM_SHA1 = "4839aebb1c22222bf43eb4c6de6287909c0d0ce6"
#: With 0x0FF0-0x0FFF, which the printout lacks, taken as 0xFF.
INTERNAL_ROM_SHA1 = "06cf7011e56efb96d840ff4862cb7888d9dc5ba4"

FONT_DIRPATH = REPO_DIRPATH / "src" / "papyrium" / "font" / "kx_p1080"
WIDTHS_FILEPATH = REPO_DIRPATH / "src/papyrium/model/panasonic_kx_p1080/widths.py"

#: The proportional width tables ($43C6) for the ROM characters, by CPU
#: address $4000 on (file offset 0 on): upright, italic, and both double
#: width. The tables for the IBM PC characters are left out.
WIDTH_TABLES = {
    "upright": 0x1C00,
    "italic": 0x1C80,
    "upright_double": 0x1D70,
    "italic_double": 0x1DF0,
}

#: The characters at codes 0-31, as papyrium.language.escp.charsets has
#: them; the firmware keeps them in this order in both qualities.
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
SLASHED_ZERO_CODE = 127

# Draft (internal ROM): nine column bytes a character, codes 0-127, from
# a base the draft path ($4302) takes from its table at $4348.
DRAFT_UPRIGHT = 0x00C0
DRAFT_ITALIC = 0x0540
DRAFT_BYTES = 9
DRAFT_ROWS, DRAFT_COLUMNS = 9, 12

# NLQ (EPROM, CPU addresses $4000 on being file offsets 0 on): an index
# of four bytes a code at $4B00, the builders' kinds at $4524.
NLQ_INDEX = 0x0B00
NLQ_ROWS, NLQ_COLUMNS = 18, 24
#: Each kind's decoding, and how far before the end its mirroring starts.
NLQ_KINDS = {
    0: ("plain", 0), 1: ("pairs", 0), 2: ("plain", 2), 3: ("pairs", 2),
    4: ("plain", 1), 5: ("pairs", 1), 6: ("plain", 0), 7: ("plain", 0),
}  # fmt: skip


def read_rom(filepath: Path, sha1: str, what: str) -> bytes:
    data = filepath.read_bytes()
    digest = hashlib.sha1(data).hexdigest()
    if digest != sha1:
        raise SystemExit(f"{filepath} is not the expected KX-P1080U {what} (SHA-1 {digest})")
    return data


def column_pins(byte: int) -> set[int]:
    """The pins, 0 the top to 8 the ninth, a draft column byte fires.

    As $46CE does for draft: with bit 0 clear, bits 7-0 are pins 0-7; with
    it set, the column is two pins lower, bits 7-1 being pins 2-8.
    """
    if byte & 1:
        return {pin + 2 for pin in range(7) if byte & (0x80 >> pin)}
    return {pin for pin in range(8) if byte & (0x80 >> pin)}


def draft_glyph(rom: bytes, base: int, code: int) -> set[tuple[int, int]]:
    """The dots (column, row) of the draft character *code* in the table at *base*."""
    at = base + DRAFT_BYTES * code
    return {
        (column, pin)
        for column, byte in enumerate(rom[at : at + DRAFT_BYTES])
        for pin in column_pins(byte)
    }


def nlq_pass(eprom: bytes, code: int, pass_: int) -> list[int]:
    """The 24 column bytes of one pass of NLQ character *code*, as the
    builders ($4524) leave them in the column buffer.

    Each byte loses any dot the column before fired. In the "pairs"
    kinds a byte with bit 0 set spreads over two columns: the first fires
    what it can, the second the dots the first could not. The mirrored
    kinds finish the character by copying its columns back out in reverse,
    from one or two before the end.
    """
    start, count, low, high = eprom[NLQ_INDEX + 4 * code : NLQ_INDEX + 4 * code + 4]
    data_at = NLQ_INDEX + ((high & 0x0F) << 8 | low) + (count if pass_ else 0)
    decoding, back = NLQ_KINDS[(high >> 4) & 7]
    columns = [0] * NLQ_COLUMNS
    position = start
    previous = 0

    def put(column: int) -> None:
        nonlocal position
        if position < NLQ_COLUMNS:
            columns[position] = column
        position += 1

    for byte in eprom[data_at : data_at + count]:
        spread = decoding == "pairs" and byte & 1
        if spread:
            byte &= 0xFE
            previous = byte & ~previous & 0xFF
            put(previous)
        previous = byte & ~previous & 0xFF
        put(previous)
    if back:
        source = position - back
        while True:
            put(columns[source] if 0 <= source < NLQ_COLUMNS else 0)
            source -= 1
            if source < 0 or position >= NLQ_COLUMNS:
                break
    return columns


def nlq_lowered(eprom: bytes, code: int) -> bool:
    """Whether NLQ character *code* prints a pin lower ($44F8): bit 7 of
    its index entry's last byte."""
    return bool(eprom[NLQ_INDEX + 4 * code + 3] & 0x80)


def sheared(columns: list[int]) -> list[int]:
    """One pass's columns slanted for italic, as $4534 does: each column
    takes its top two pins from the column three before, the next two from
    two before, the next two from the one before, and keeps its lowest two.
    """

    def at(index: int) -> int:
        return columns[index] if index >= 0 else 0

    return [
        at(j - 3) & 0xC0 | at(j - 2) & 0x30 | at(j - 1) & 0x0C | at(j) & 0x03
        for j in range(NLQ_COLUMNS)
    ]


def nlq_glyph(eprom: bytes, code: int, italic: bool = False) -> set[tuple[int, int]]:
    """The dots (column, row) of NLQ character *code*: the first pass's
    pins on even rows and the second's on odd rows, a lowered character a
    pin (two rows) down."""
    lowered = 2 if nlq_lowered(eprom, code) else 0
    dots = set()
    for pass_ in range(2):
        columns = nlq_pass(eprom, code, pass_)
        if italic:
            columns = sheared(columns)
        for column, byte in enumerate(columns):
            for pin in range(8):
                if byte & (0x80 >> pin):
                    dots.add((column, 2 * pin + pass_ + lowered))
    return dots


def characters() -> dict[int, str]:
    """The character each code 0-127 holds in both qualities."""
    result = {code: character for code, character in enumerate(INTERNATIONAL)}
    result.update({code: chr(code) for code in range(0x20, 0x7F)})
    result[SLASHED_ZERO_CODE] = SLASHED_ZERO
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
    "Extracted by tools/kx-p1080-rom/extract.py from the KX-P1080U's firmware.",
    "The characters are Panasonic's.",
]


def widths_text(eprom: bytes) -> str:
    lines = [
        '"""The KX-P1080U\'s proportional widths, from its firmware.',
        "",
        "Written by tools/kx-p1080-rom/extract.py from the EPROM's tables at $5C00,",
        "$5C80, $5D70 and $5DF0: one byte for each code 0-127, the width in 1/120",
        "inch in the low nibble and in the high nibble where printing starts:",
        "with bit 3 clear, that many columns into the character, moving it left;",
        "with it set, bits 0-2 columns before it, moving it right.",
        '"""',
        "",
        "WIDTH_TABLES = {",
    ]
    for name, at in WIDTH_TABLES.items():
        data = eprom[at : at + 128].hex()
        lines.append(f'    "{name}": bytes.fromhex(')
        lines.extend(f'        "{data[i : i + 64]}"' for i in range(0, 256, 64))
        lines.append("    ),")
    lines.append("}")
    return "\n".join(lines) + "\n"


def main(eprom_filepath: Path, internal_rom_filepath: Path) -> None:
    eprom = read_rom(eprom_filepath, EPROM_SHA1, "EPROM")
    internal = read_rom(internal_rom_filepath, INTERNAL_ROM_SHA1, "internal ROM")
    codes = characters()
    fonts = [
        ("draft.txt", "kx-p1080-draft: the Panasonic KX-P1080U's draft characters.",
         DRAFT_ROWS, DRAFT_COLUMNS,
         {c: draft_glyph(internal, DRAFT_UPRIGHT, code) for code, c in codes.items()},
         ["From the CPU's internal ROM. Columns are 1/120 inch apart, the last",
          "three blank; rows are pins 1-9. A character's columns are lowered",
          "two pins one by one, as the ROM marks them."]),
        ("draft-italic.txt", "kx-p1080-draft-italic: the KX-P1080U's draft italics.",
         DRAFT_ROWS, DRAFT_COLUMNS,
         {c: draft_glyph(internal, DRAFT_ITALIC, code) for code, c in codes.items()},
         ["From the CPU's internal ROM, which stores the italics slanted, laid",
          "out as kx-p1080-draft."]),
        ("nlq.txt", "kx-p1080-nlq: the Panasonic KX-P1080U's near letter quality.",
         NLQ_ROWS, NLQ_COLUMNS,
         {c: nlq_glyph(eprom, code) for code, c in codes.items()},
         ["From the EPROM, built as the printer builds them. Even rows are the",
          "pins of the first pass, odd rows of the second; a lowered character",
          "is a pin (two rows) down. Columns are 1/240 inch apart."]),
        ("nlq-italic.txt", "kx-p1080-nlq-italic: the KX-P1080U's NLQ italics.",
         NLQ_ROWS, NLQ_COLUMNS,
         {c: nlq_glyph(eprom, code, italic=True) for code, c in codes.items()},
         ["The NLQ characters slanted as the printer slants them at print time,",
          "each pass's pins in pairs moving one column further right for each",
          "pair above the lowest; laid out as kx-p1080-nlq."]),
    ]  # fmt: skip
    FONT_DIRPATH.mkdir(parents=True, exist_ok=True)
    for filename, title, rows, columns, glyphs, notes in fonts:
        text = font_text([title, *PROVENANCE, *notes], rows, columns, glyphs)
        (FONT_DIRPATH / filename).write_text(text + "\n", encoding="utf-8")
        print(f"{filename}: {len(glyphs)} characters")
    WIDTHS_FILEPATH.parent.mkdir(parents=True, exist_ok=True)
    WIDTHS_FILEPATH.write_text(widths_text(eprom), encoding="utf-8")
    print(f"{WIDTHS_FILEPATH.name}: {len(WIDTH_TABLES)} width tables")


if __name__ == "__main__":
    arguments = [Path(argument) for argument in sys.argv[1:3]]
    defaults = [EPROM_FILEPATH, INTERNAL_ROM_FILEPATH]
    main(*(arguments + defaults[len(arguments) :]))
