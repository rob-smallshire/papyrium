"""Correct m1109-draft's ASCII characters from the Centronics GLP's firmware.

m1109-draft was reconstructed from the printed pages of Brother's M-1109
manual, where a character's dots are easily misplaced by a half-dot column.
The Schneider NLQ401's EPROM, the first-edition Centronics GLP's firmware,
holds the same design exactly: eleven columns a character, eight pins, top
pin in bit 7, from code 0x20 at $16FD. This takes each printable ASCII
character's dots from the ROM and places them at the height the M-1109
was seen to print it: on rows 0-7, or a pin lower on rows 1-8 for a
character it prints lower (its descenders, which include , : and j, though
the NLQ401's firmware lowers only ; _ g p q y). Other characters, the
national ones and the slashed zero, are left as they are.

Usage: uv run python tools/nlq401-rom/correct_m1109_draft.py [ROM_FILEPATH]

It rewrites src/papyrium/font/m1109/draft.txt in place and reports each
character it changes.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_DIRPATH = Path(__file__).resolve().parents[2]
ROM_FILEPATH = REPO_DIRPATH / "docs/local/schneider-nlq401/schneider_nlq401_rev004.bin"
FONT_FILEPATH = REPO_DIRPATH / "src/papyrium/font/m1109/draft.txt"

#: The ROM's draft character for code 0x20, eleven bytes a character.
DRAFT_SPACE_OFFSET = 0x16FD
COLUMNS = 11
ROWS = 9

HEADER = """\
# m1109-draft: the Brother M-1109's draft characters, the Centronics GLP
# II's. Recovered from the character tables and printed examples in its
# owner's manual; the printable ASCII characters' dots are corrected from
# the first-edition Centronics GLP's firmware (the Schneider NLQ401's
# EPROM), at the heights the M-1109 prints them
# (tools/nlq401-rom/correct_m1109_draft.py).
"""


def rom_rows(rom: bytes, code: int) -> list[str]:
    """The ROM's character *code* as eight rows of eleven dots."""
    start = DRAFT_SPACE_OFFSET + (code - 0x20) * COLUMNS
    columns = rom[start : start + COLUMNS]
    return [
        "".join("#" if columns[c] & (0x80 >> row) else "." for c in range(COLUMNS))
        for row in range(8)
    ]


def placed(rows: list[str], lowered: bool) -> list[str]:
    blank = "." * COLUMNS
    return [blank, *rows] if lowered else [*rows, blank]


def inked_rows(rows: list[str]) -> list[int]:
    return [index for index, row in enumerate(rows) if "#" in row]


def best_placement(rom_glyph: list[str], font_glyph: list[str]) -> list[str]:
    """The ROM's glyph on the rows the font's glyph is printed on."""
    font_inked = set(inked_rows(font_glyph))
    candidates = [placed(rom_glyph, lowered) for lowered in (False, True)]
    return min(candidates, key=lambda rows: len(set(inked_rows(rows)) ^ font_inked))


def main() -> int:
    rom = Path(sys.argv[1] if len(sys.argv) > 1 else ROM_FILEPATH).read_bytes()
    lines = FONT_FILEPATH.read_text().split("\n")
    body_start = next(index for index, line in enumerate(lines) if not line.startswith("#"))
    body = lines[body_start:]
    changed = []
    index = 0
    while index < len(body):
        line = body[index]
        parts = line.split()
        if len(parts) == 1 and line.startswith("U+"):
            code = int(parts[0][2:], 16)
            if 0x20 <= code <= 0x7E:
                glyph = body[index + 1 : index + 1 + ROWS]
                corrected = best_placement(rom_rows(rom, code), glyph)
                if corrected != glyph:
                    body[index + 1 : index + 1 + ROWS] = corrected
                    changed.append(chr(code))
            index += 1 + ROWS
        else:
            index += 1
    FONT_FILEPATH.write_text(HEADER + "\n".join(body))
    print(f"corrected {len(changed)} characters: {''.join(changed)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
