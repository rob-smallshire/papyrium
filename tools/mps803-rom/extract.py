#!/usr/bin/env python3
"""Extract the Commodore MPS-803's characters from its firmware.

Reads the uPD78C11's internal ROM, docs/local/commodore-mps-803/mps803_78c11.bin,
checks it is the dump this tool was written for, and writes the dot font
of papyrium.font.mps803. docs/commodore-mps-803-firmware.md describes the
character generator.

Usage: extract.py [ROM_FILEPATH]
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

from papyrium.language.cbm.charset import glyph_character

REPO_DIRPATH = Path(__file__).resolve().parent.parent.parent
ROM_FILEPATH = REPO_DIRPATH / "docs/local/commodore-mps-803/mps803_78c11.bin"
ROM_SHA1 = "69ee52b09d87ac3c0a5105a4f0af1e862d2a5814"
FONT_FILEPATH = REPO_DIRPATH / "src/papyrium/font/mps803/glyphs.txt"

#: Glyph $20-$BF is six bytes, one a column left to right, at this address
#: plus six times its index; bit 0 is the top dot, bit 6 the bottom.
GLYPH_BASE = 0x0B7F
COLUMNS = 6
ROWS = 7

HEADER = """\
# mps803: the Commodore MPS-803's characters.
#
# Extracted by tools/mps803-rom/extract.py from the printer's uPD78C11
# internal ROM. The characters are Commodore's. Six columns 1/60 inch
# apart, one to a carriage step, seven rows 1/72 inch apart; letters use
# five columns and graphics all six, so that they join. Each glyph is
# keyed by the character it shows, PETSCII's graphics among Unicode's
# Symbols for Legacy Computing.
rows 7
columns 6
"""


def glyph_rows(rom: bytes, glyph: int) -> list[str]:
    start = GLYPH_BASE + COLUMNS * glyph
    columns = rom[start : start + COLUMNS]
    return [
        "".join("#" if column & (1 << row) else "." for column in columns) for row in range(ROWS)
    ]


def main() -> int:
    rom_filepath = Path(sys.argv[1]) if len(sys.argv) > 1 else ROM_FILEPATH
    rom = rom_filepath.read_bytes()
    if hashlib.sha1(rom).hexdigest() != ROM_SHA1:
        raise SystemExit(f"{rom_filepath} is not the MPS-803's internal ROM")
    entries = [HEADER]
    written = set()
    for glyph in range(0x20, 0xC0):
        character = glyph_character(glyph)
        # Glyphs $60 and $A0 are the same line, U+2500, and written once.
        if character is None or character in written:
            continue
        written.add(character)
        code_points = " ".join(f"U+{ord(c):04X}" for c in character)
        entries.append(code_points + "\n" + "\n".join(glyph_rows(rom, glyph)) + "\n")
    FONT_FILEPATH.write_text("\n".join(entries))
    print(f"wrote {FONT_FILEPATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
