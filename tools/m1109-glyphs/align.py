"""Check how consistently glyphs sit in their table cells, to anchor rows and columns."""

import json

import numpy as np
from cache import DATA_DIRPATH, cached
from extract import SCALE_X, SCALE_Y
from fit import COLUMN_PITCH, ROW_PITCH

PY, PX = ROW_PITCH * SCALE_Y, COLUMN_PITCH * SCALE_X
fits = {int(k): v for k, v in json.loads((DATA_DIRPATH / "fits.json").read_text()).items()}
boxes = {}


def box(table, code):
    if table not in boxes:
        boxes[table] = cached(table)[1]
    return boxes[table][code]


def placements(rom):
    """For each copy: (table, code, y of top dot - cell top, x of lattice col 0 - cell left)."""
    fit = fits[rom]
    top = min(r for r, _ in fit["dots"])
    left = min(c for _, c in fit["dots"])
    result = []
    for copy in fit["used"]:
        x0, y0, _, _ = box(copy["table"], copy["code"])
        result.append(
            (copy["table"], copy["code"], copy["y"] + top * PY - y0, copy["x"] + left * PX - x0)
        )
    return result


if __name__ == "__main__":
    for ch in "HEFTZPBDNM0123":
        p = placements(ord(ch))
        ys = np.array([v[2] for v in p])
        xs = np.array([v[3] for v in p])
        print(
            ch,
            "top-in-cell",
            ys.round(1).min(),
            np.median(ys).round(1),
            ys.max().round(1),
            " left-in-cell",
            xs.min().round(1),
            np.median(xs).round(1),
            xs.max().round(1),
        )


def row_check():
    """Per table and table row, the top-dot y (page) of capitals and digits."""
    tops = {}
    for rom in list(range(ord("A"), ord("Z") + 1)) + list(range(ord("0"), ord("9") + 1)):
        fit = fits[rom]
        top = min(r for r, _ in fit["dots"])
        for copy in fit["used"]:
            tops.setdefault((copy["table"], copy["code"] & 15), []).append(
                (chr(rom), round(copy["y"] + top * PY, 1))
            )
    return tops


def references():
    """Per (table, table row): median top-dot y of capitals and digits, and the
    median x of lattice column 0 relative to the cell for full-width capitals."""
    tops = {key: float(np.median([y for _, y in values])) for key, values in row_check().items()}
    lefts = []
    for ch in "HNUMWAOQ0":
        lefts += [v[3] for v in placements(ord(ch))]
    return tops, float(np.median(lefts))


def anchored(rom, tops, left0):
    """The glyph's dots with rows from the table rows' tops and columns measured."""
    fit = fits[rom]
    top = min(r for r, _ in fit["dots"])
    left = min(c for _, c in fit["dots"])
    row_offsets, column_offsets = [], []
    for copy in fit["used"]:
        key = (copy["table"], copy["code"] & 15)
        if key not in tops:
            continue
        x0, _, _, _ = box(copy["table"], copy["code"])
        row_offsets.append((copy["y"] + top * PY - tops[key]) / PY)
        column_offsets.append((copy["x"] + left * PX - x0 - left0) / PX)
    row = float(np.median(row_offsets))
    column = float(np.median(column_offsets))
    return row, column, float(np.std(row_offsets)), float(np.std(column_offsets))
