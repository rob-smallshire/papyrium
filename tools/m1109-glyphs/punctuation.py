"""Rows of small glyphs, measured from ink extents in the printout lines.

Usage: punctuation.py
"""

import json
from collections import Counter
from pathlib import Path

import numpy as np
from cache import DATA_DIRPATH
from cells import load
from classify import PX, PY
from lines import find_lines
from positions import CAPITALS, confident

HERE = Path(__file__).parent
RADIUS = 3.25


def measure(page_index, page):
    ink = load(DATA_DIRPATH / "pages" / f"p-{int(page_index):03d}.png")
    lines = {line.top: line for line in find_lines(ink, pitch=40.25)}
    found = []
    for entry in page:
        line = lines.get(entry["top"])
        cells = entry["cells"]
        tops = [c["y"] for c in cells if confident(c) and c["rom"] in CAPITALS]
        if line is None or len(tops) < 3:
            continue
        reference = float(np.median(tops))
        for c in cells:
            # Recover the cell from its x relative to the cell edge is not
            # possible here, so search the cells of the line for this match.
            pass
        for cell in range(line.first, line.last + 1):
            x0 = int(line.origin + cell * line.pitch)
            x1 = int(line.origin + (cell + 1) * line.pitch)
            region = ink[max(0, line.top - 14) : line.bottom + 14, x0:x1]
            ys, xs = np.nonzero(region)
            if len(ys) < 15:
                continue
            top = ys.min() + max(0, line.top - 14) + RADIUS
            bottom = ys.max() + max(0, line.top - 14) - RADIUS
            left = xs.min() + RADIUS
            found.append(
                (
                    round((top - reference) / PY),
                    round((bottom - top) / PY) + 1,
                    round(left / PX),
                    round((xs.max() - xs.min() - 2 * RADIUS) / PX) + 1,
                )
            )
    return found


if __name__ == "__main__":
    shapes = Counter()
    for path in sorted((DATA_DIRPATH / "classified").glob("*.json")):
        for page_index, page in json.loads(path.read_text()).items():
            for top, height, left, width in measure(page_index, page):
                if height <= 5:
                    shapes[(top, height, left, width)] += 1
    for key, count in shapes.most_common(60):
        print(key, count)
