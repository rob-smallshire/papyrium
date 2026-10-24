"""Assemble the fitted NLQ characters into an 18 x 24 Papyrium dot font.

Each sample line's fit has its own vertical origin, so the lines are
aligned by their baselines (the bottom of H, of the digits, and of the
x-height letters), with the top of the capitals at row 0. Columns keep
each character's measured place in its cell, shifted together so that
the capitals sit centred in the 24 columns.

Usage: build_nlq_font.py OUT_TXT
"""

from __future__ import annotations

import json
import sys
from statistics import median

from cache import DATA_DIRPATH

ROWS, COLUMNS = 18, 24
#: The row the capitals start on.
CAP_TOP_ROW = 2

#: Characters whose bottom is the baseline, by sample line.
BASELINE_CHARACTERS = "0123456789HEFIKLMNTXZacemnorsuvwxz"


def best_copies(fits):
    """For each character, its copy from the character lines (not the heading)."""
    result = {}
    for character, copies in fits.items():
        result[character] = max(copies, key=lambda copy: copy["line"])
    return result


def main(out_filepath):
    fits = json.loads((DATA_DIRPATH / "nlq-fits.json").read_text())
    copies = best_copies(fits)
    # Per line, the row of the baseline.
    baselines = {}
    for character, copy in copies.items():
        if character in BASELINE_CHARACTERS and copy["dots"]:
            baselines.setdefault(copy["line"], []).append(max(r for r, _ in copy["dots"]))
    baseline = {line: median(rows) for line, rows in baselines.items()}
    cap_line = copies["H"]["line"]
    cap_top = min(r for r, _ in copies["H"]["dots"])
    cap_baseline = baseline[cap_line]
    placed = {}
    for character, copy in copies.items():
        # Shift whole pins (two rows) so the passes stay on their rows; the
        # capitals start on row 2, leaving a pin above them for accents and
        # quotes, and their baseline falls on pin 6 as in draft.
        shift = round((baseline[copy["line"]] - cap_baseline) / 2) * 2 + cap_top - CAP_TOP_ROW
        dots = {(r - shift, c) for r, c in copy["dots"]}
        overhang = max(r for r, _ in dots) - (ROWS - 1)
        if overhang > 0:
            # Only the underscore lies so low; raise it whole pins to fit.
            raise_rows = overhang + overhang % 2
            print(f"{character!r}: raised {raise_rows} rows to fit")
            dots = {(r - raise_rows, c) for r, c in dots}
        placed[character] = dots
    centres = [
        (min(c for _, c in placed[ch]) + max(c for _, c in placed[ch])) / 2
        for ch in "ABCDEFGHJKLNOPRSTUVXYZ"
    ]
    column_shift = round(median(centres) - (COLUMNS - 1) / 2)
    placed[" "] = set()
    lines = [
        "# m1109-nlq: the Brother M-1109's near letter quality characters, as",
        "# recovered from the NLQ sample in its owner's manual. Even rows are the",
        "# pins of the first pass, odd rows of the second, 1/216 inch lower;",
        "# columns are 1/240 inch apart.",
        f"rows {ROWS}",
        f"columns {COLUMNS}",
        "",
    ]
    for character in sorted(placed):
        dots = {(r, c - column_shift) for r, c in placed[character]}
        outside = {(r, c) for r, c in dots if not (0 <= r < ROWS and 0 <= c < COLUMNS)}
        if outside:
            print(f"{character!r}: dropping {len(outside)} dots outside the matrix")
        dots -= outside
        lines.append(f"U+{ord(character):04X}")
        for row in range(ROWS):
            lines.append("".join("#" if (row, c) in dots else "." for c in range(COLUMNS)))
        lines.append("")
    with open(out_filepath, "w", encoding="ascii") as f:
        f.write("\n".join(lines))
    print(len(placed), "glyphs; columns shifted by", column_shift)


if __name__ == "__main__":
    main(sys.argv[1])
