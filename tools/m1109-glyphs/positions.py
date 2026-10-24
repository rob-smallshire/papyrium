"""Absolute rows and columns of each glyph, from the classified printout lines.

Row 0 is the top of the capitals in each line; column 0 is the cell's left
edge, both in dot lattice units.

Usage: positions.py
"""

import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from cache import DATA_DIRPATH
from classify import PX, PY

HERE = Path(__file__).parent
CAPITALS = set(range(ord("A"), ord("Z") + 1)) | set(range(ord("0"), ord("9") + 1))


def confident(cell):
    return cell["margin"] > 15 and cell["cost"] < 60


def gather():
    rows = defaultdict(list)
    columns = defaultdict(list)
    for path in sorted((DATA_DIRPATH / "classified").glob("*.json")):
        for page in json.loads(path.read_text()).values():
            for line in page:
                cells = [c for c in line["cells"] if confident(c)]
                tops = [c["y"] for c in cells if c["rom"] in CAPITALS]
                if len(tops) < 3:
                    continue
                reference = float(np.median(tops))
                if max(abs(t - reference) for t in tops) > PY / 2:
                    continue  # Mixed sizes or scripts on this line.
                for c in cells:
                    rows[c["rom"]].append((c["y"] - reference) / PY)
                    columns[c["rom"]].append(c["x"] / PX)
    return rows, columns


if __name__ == "__main__":
    rows, columns = gather()
    for rom in sorted(rows):
        r = np.array(rows[rom])
        c = np.array(columns[rom])
        rr = np.round(r).astype(int)
        cc = np.round(c).astype(int)
        rv, rn = np.unique(rr, return_counts=True)
        cv, cn = np.unique(cc, return_counts=True)
        label = chr(rom) if rom >= 32 else rom
        row_counts = dict(zip(rv.tolist(), rn.tolist()))
        column_counts = dict(zip(cv.tolist(), cn.tolist()))
        print(f"{label!r:5} n={len(r):4d} rows {row_counts} cols {column_counts}")
