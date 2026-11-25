#!/usr/bin/env python3
"""Extract the Centronics GLP's draft and graphics fonts from the NLQ401's firmware.

Reads the Schneider NLQ401's 16K EPROM, Rev 004, from
docs/local/schneider-nlq401/schneider_nlq401_rev004.bin, checks it is the
dump this tool was written for, and writes the dot font files of
papyrium.font.glp. What the tables hold is described in
docs/schneider-nlq401-firmware.md.

Usage: extract.py [ROM_FILEPATH]
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

from papyrium.font.glp import UPPER_HALF

REPO_DIRPATH = Path(__file__).resolve().parent.parent.parent
ROM_FILEPATH = REPO_DIRPATH / "docs/local/schneider-nlq401/schneider_nlq401_rev004.bin"
ROM_SHA1 = "b6374abaebb8e484e573caa21b1cc87f1554c8d6"

FONT_DIRPATH = REPO_DIRPATH / "src/papyrium/font/glp"

#: A character's entry is eleven bytes from this address plus eleven times
#: its location; the firmware prints its eleven columns from the entry's
#: second byte ($0925 points at $159E), so the last column is the next
#: entry's first byte, which text leaves blank.
CHARACTER_BASE = 0x159D
CHARACTER_BYTES = 11

#: A near letter quality character is two passes of 39 columns, the
#: second pass's at 39 bytes on, from this address plus 78 times its
#: location ($143E), for locations 0x18-0x7E.
NLQ_BASE = 0x194E
NLQ_COLUMNS = 39

#: Locations 0x18-0x1F hold character set 2's German characters, which
#: replace @ [ \ ] { | } ~ (the conversion table at $15F4).
GERMAN = "§ÄÖÜäöüß"

#: The locations the firmware prints a pin lower ($08FD).
DESCENDERS = frozenset(";_gpqy")

DRAFT_HEADER = """\
# glp-draft: the Centronics GLP's draft characters (Model 3101).
#
# Extracted by tools/nlq401-rom/extract.py from the Schneider NLQ401's
# firmware, EPROM Rev 004. The characters are Centronics'.
# Columns are 1/120 inch apart, in a 12-column pica cell; rows are 1/72
# inch apart. The firmware prints ; _ g p q y a pin lower, on rows 1-8.
"""

NLQ_HEADER = """\
# glp-nlq: the Schneider NLQ401's near letter quality characters, which
# Schneider added to the Centronics GLP's firmware.
#
# Extracted by tools/nlq401-rom/extract.py from the NLQ401's EPROM Rev 004.
# Two passes of eight pins: even rows are the first pass's pins, odd rows
# the second's, 1/216 inch lower. Columns are 1/480 inch apart, 48 to the
# pica cell, of which a character's 39 print. The
# firmware prints ; _ g p q y a pin lower, on rows 2-17.
"""

GRAPHICS_HEADER = """\
# glp-graphics: the Centronics GLP's graphics characters, the Amstrad CPC's
# codes 129-255, which the Schneider NLQ401 prints after ESC =.
#
# Extracted by tools/nlq401-rom/extract.py from the Schneider NLQ401's
# firmware, EPROM Rev 004. Six columns 1/60 inch apart, on the even columns
# of a 12-column pica cell, so that neighbouring cells join; eight rows
# 1/72 inch apart. U+E0EF, U+E0FC and U+E0FD stand for the three
# characters Unicode encodes only from version 16.
"""


def columns(rom: bytes, location: int) -> bytes:
    """The eleven columns the firmware prints for *location*, left to right."""
    start = CHARACTER_BASE + location * CHARACTER_BYTES + 1
    return rom[start : start + CHARACTER_BYTES]


def draft_rows(rom: bytes, location: int, lowered: bool) -> list[str]:
    columns_ = columns(rom, location)
    rows = [
        "".join("#" if column & (0x80 >> pin) else "." for column in columns_) for pin in range(8)
    ]
    blank = "." * CHARACTER_BYTES
    return [blank, *rows] if lowered else [*rows, blank]


def nlq_rows(rom: bytes, location: int, lowered: bool) -> list[str]:
    start = NLQ_BASE + location * 2 * NLQ_COLUMNS
    passes = (rom[start : start + NLQ_COLUMNS], rom[start + NLQ_COLUMNS : start + 2 * NLQ_COLUMNS])
    rows = [
        "".join("#" if column & (0x80 >> pin) else "." for column in passes[row % 2])
        for pin in range(8)
        for row in (2 * pin, 2 * pin + 1)
    ]
    blank = "." * NLQ_COLUMNS
    return [blank, blank, *rows] if lowered else [*rows, blank, blank]


def graphics_rows(rom: bytes, location: int) -> list[str]:
    # A graphics character's six columns are the even ones of the eleven.
    data = columns(rom, location)
    return [
        "".join(
            "#" if column % 2 == 0 and data[column] & (0x80 >> pin) else "." for column in range(11)
        )
        for pin in range(8)
    ]


def entry(character_text: str, rows: list[str]) -> str:
    code_points = " ".join(f"U+{ord(c):04X}" for c in character_text)
    return code_points + "\n" + "\n".join(rows) + "\n"


def main() -> int:
    rom_filepath = Path(sys.argv[1]) if len(sys.argv) > 1 else ROM_FILEPATH
    rom = rom_filepath.read_bytes()
    if hashlib.sha1(rom).hexdigest() != ROM_SHA1:
        raise SystemExit(f"{rom_filepath} is not the NLQ401's EPROM Rev 004")
    draft = [DRAFT_HEADER, "rows 9\ncolumns 11\n"]
    for code in range(0x20, 0x7F):
        draft.append(entry(chr(code), draft_rows(rom, code, chr(code) in DESCENDERS)))
    for index, german in enumerate(GERMAN):
        draft.append(entry(german, draft_rows(rom, 0x18 + index, False)))
    nlq = [NLQ_HEADER, f"rows 18\ncolumns {NLQ_COLUMNS}\n"]
    for code in range(0x20, 0x7F):
        nlq.append(entry(chr(code), nlq_rows(rom, code, chr(code) in DESCENDERS)))
    for index, german in enumerate(GERMAN):
        nlq.append(entry(german, nlq_rows(rom, 0x18 + index, False)))
    graphics = [GRAPHICS_HEADER, "rows 8\ncolumns 11\n"]
    for index, text in enumerate(UPPER_HALF[1:]):
        graphics.append(entry(text, graphics_rows(rom, 0x81 + index)))
    FONT_DIRPATH.mkdir(parents=True, exist_ok=True)
    (FONT_DIRPATH / "draft.txt").write_text("\n".join(draft))
    (FONT_DIRPATH / "graphics.txt").write_text("\n".join(graphics))
    (FONT_DIRPATH / "nlq.txt").write_text("\n".join(nlq))
    print(f"wrote draft.txt, graphics.txt and nlq.txt in {FONT_DIRPATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
