"""Assemble the fitted glyphs into a Papyrium dot font file.

Shapes come from the joint fits of the character tables (fits.json).
Positions in the 9 x 11 matrix come from the printout lines where they
were measured, and otherwise from the font's conventions: capitals,
digits and ascenders on rows 0-6, x-height letters on rows 2-6,
descenders down to row 8, and glyphs centred in columns 0-10.

Usage: build_font.py OUT_TXT
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from cache import DATA_DIRPATH

from papyrium.language.escp.charsets import INTERNATIONAL_CHARACTERS

HERE = Path(__file__).parent
ROWS, COLUMNS = 9, 11

#: First row of glyphs that do not sit with their top on row 0.
TOP_ROW = {
    **{c: 2 for c in "acemnorsuvwxz"},
    **{c: 2 for c in "gpqy"},
    "j": 1,
    "*": 1,
    "+": 1,
    "-": 3,
    "=": 2,
    ",": 5,
    ".": 5,
    ":": 2,
    ";": 2,
    "_": 8,
    chr(0xE6): 2,  # ae
    chr(0xF8): 2,  # o slash
    chr(0xE7): 3,  # c cedilla: the cedilla hangs below the baseline
    chr(0xA8): 1,  # diaeresis
}

#: First column, measured in the printout lines, where it is not the centred one.
LEFT_COLUMN = {"(": 5, ")": 3, ";": 3, ":": 3, ",": 3, ".": 3, ">": 3, "h": 1, "N": 0}


def clean(dots):
    """Drop stray dots far from every other dot, then normalise to row and column 0."""
    dots = set(dots)
    kept = {
        (r, c)
        for r, c in dots
        if any(abs(r - r2) <= 4 and abs(c - c2) <= 6 for r2, c2 in dots if (r2, c2) != (r, c))
        or len(dots) == 1
    }
    r0 = min(r for r, _ in kept)
    c0 = min(c for _, c in kept)
    return {(r - r0, c - c0) for r, c in kept}


def place(character, dots):
    height = max(r for r, _ in dots) + 1
    width = max(c for _, c in dots) + 1
    top = TOP_ROW.get(character, 0)
    left = LEFT_COLUMN.get(character, (COLUMNS - width) // 2)
    if top + height > ROWS or left + width > COLUMNS:
        raise ValueError(f"{character!r} ({height} x {width}) does not fit at {top}, {left}")
    return {(r + top, c + left) for r, c in dots}


def slashed(zero, slash):
    """A slashed zero (switch 2-6): the zero with the slash's dots inside it,
    leaving out any that would strike beside a dot already in its row."""
    inside = [(r, c) for r, c in slash if 0 < r < 6]
    dots = set(zero)
    for r, c in inside:
        if (r, c - 1) not in dots and (r, c + 1) not in dots:
            dots.add((r, c))
    return dots


def glyph_text(character, dots):
    name = " ".join(f"U+{ord(c):04X}" for c in character)
    lines = [name]
    for row in range(ROWS):
        lines.append("".join("#" if (row, c) in dots else "." for c in range(COLUMNS)))
    return "\n".join(lines)


def main(out_filepath):
    fits = json.loads((DATA_DIRPATH / "fits.json").read_text())
    glyphs = {" ": set()}
    for rom, fit in fits.items():
        rom = int(rom)
        character = INTERNATIONAL_CHARACTERS[rom] if rom < 32 else chr(rom)
        if fit["dots"]:
            glyphs[character] = place(character, clean(map(tuple, fit["dots"])))
    glyphs["0\u0338"] = slashed(glyphs["0"], glyphs["/"])
    header = [
        "# m1109-draft: the Brother M-1109's draft characters, as recovered from",
        "# the character tables and printed examples in its owner's manual.",
        f"rows {ROWS}",
        f"columns {COLUMNS}",
        "",
    ]
    body = [glyph_text(c, glyphs[c]) for c in sorted(glyphs)]
    Path(out_filepath).write_text("\n".join(header) + "\n\n".join(body) + "\n", encoding="ascii")
    print(len(glyphs), "glyphs")


if __name__ == "__main__":
    main(sys.argv[1])
