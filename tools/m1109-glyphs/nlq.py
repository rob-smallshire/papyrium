"""Fit the M-1109's near letter quality characters to the sample on page 74.

NLQ strikes each character in two passes 1/216 inch apart, so a character
is 18 rows (pin k of the first pass is row 2k, of the second row 2k + 1)
on a horizontal grid of 1/240 inch, 24 columns to the pica cell. The
sample prints each character once and its dots merge into solid strokes,
so many dot patterns would print the same; this finds a sparse one that
reproduces the printed shape, with a cost for every dot.

Usage: nlq.py OUT_JSON
"""

from __future__ import annotations

import json
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np
from cache import PAGES_DIRPATH
from cells import load
from fit import BLUR
from lines import find_lines
from scipy import ndimage

#: The NLQ sample page and the characters on its four NLQ lines, in order.
PAGE_INDEX = 79
LINES = [
    "*NLQMODE*",
    "".join(chr(c) for c in range(33, 65)),
    "".join(chr(c) for c in range(65, 97)),
    "".join(chr(c) for c in range(97, 127)),
]
#: Page rows between which the NLQ lines lie.
NLQ_TOP, NLQ_BOTTOM = 1900, 2200
#: The text column's left edge on the page; marks further left are rules.
TEXT_LEFT = 800
CELL = 40.25  # pixels per pica cell on this page
PX = CELL / 24  # 1/240 inch
PY = 400 / 72 * 66.9 / (400 / 6) / 6 * 6  # 1/72 inch at the page's scale
SUB = PY / 3  # 1/216 inch
DIAMETER = 6.5
DOT_COST = 0.3
#: Pixels kept either side of the cell, and lattice columns before its edge.
MARGIN = 8
MARGIN_COLUMNS = 4


def row_y(row):
    return (row // 2) * PY + (row % 2) * SUB


class NlqFitter:
    def __init__(self, shape):
        self.shape = shape
        self.ys, self.xs = np.ogrid[: shape[0], : shape[1]]

    def render(self, dots, origin):
        image = np.zeros(self.shape, bool)
        r = DIAMETER / 2
        for row, column in dots:
            cx = origin[0] + column * PX
            cy = origin[1] + row_y(row)
            image |= (self.xs - cx) ** 2 + (self.ys - cy) ** 2 <= r * r
        return image

    def cost(self, dots, origin, target):
        rendered = ndimage.gaussian_filter(self.render(dots, origin).astype(float), BLUR)
        return float(((rendered - target) ** 2).sum()) + DOT_COST * len(dots)

    def fit(self, target, origin, rows, columns):
        """Greedy search from the dots whose centres fall on ink."""
        dots = set()
        for row in rows:
            for column in columns:
                x = origin[0] + column * PX
                y = origin[1] + row_y(row)
                value = ndimage.map_coordinates(target, [[y], [x]], order=1)[0]
                # Start sparse: every other column on strongly inked points.
                if value > 0.8 and column % 2 == 0:
                    dots.add((row, column))
        cost = self.cost(dots, origin, target)
        improved = True
        while improved:
            improved = False
            for row in rows:
                for column in columns:
                    position = (row, column)
                    candidates = [dots ^ {position}]
                    if position in dots:
                        for step in (-1, 1):
                            moved = (row, column + step)
                            if moved not in dots and moved[1] in columns:
                                candidates.append((dots - {position}) | {moved})
                    for candidate in candidates:
                        candidate_cost = self.cost(candidate, origin, target)
                        if candidate_cost < cost - 1e-6:
                            dots, cost, improved = candidate, candidate_cost, True
                            break
        return dots, cost


def line_cells(ink, line, count):
    """The x of each inked cell's left edge, in order, for the first *count*."""
    edges = []
    for cell in range(line.first, line.last + 1):
        x0 = line.origin + cell * line.pitch
        if x0 < TEXT_LEFT:
            continue  # The page's left rule.
        region = ink[line.top - 14 : line.bottom + 14, int(x0) : int(x0 + line.pitch)]
        if region.sum() > 15:
            edges.append(x0)
    return edges[:count]


def fit_cell(job):
    """Fit one character: *job* is (character, line index, cell x, page target)."""
    character, line_index, x0, top, target = job
    fitter = NlqFitter(target.shape)
    # Lattice column MARGIN_COLUMNS falls on the cell's left edge; dots stay in the cell.
    origin = (MARGIN + (x0 - int(x0)) - MARGIN_COLUMNS * PX, 4.0)
    columns = range(MARGIN_COLUMNS, MARGIN_COLUMNS + 24)
    dots, cost = fitter.fit(target, origin, range(0, 26), columns)
    return character, {
        "dots": sorted((r, c - MARGIN_COLUMNS) for r, c in dots),
        "cost": cost,
        "y": top + origin[1],
        "cell_x": x0,
        "line": line_index,
    }


def main(out_filepath):
    ink = load(PAGES_DIRPATH / f"p-{PAGE_INDEX:03d}.png")
    blurred = ndimage.gaussian_filter(ink.astype(float), BLUR)
    lines = find_lines(ink, pitch=CELL)
    # The four NLQ lines lie between the heading and the draft sample.
    nlq_lines = [i for i, line in enumerate(lines) if NLQ_TOP < line.top < NLQ_BOTTOM]
    jobs = []
    for text, index in zip(LINES, nlq_lines):
        line = lines[index]
        edges = line_cells(ink, line, len(text))
        if len(edges) != len(text):
            raise ValueError(f"line {index}: {len(edges)} cells for {len(text)} characters")
        top = line.top - 14
        bottom = line.bottom + 14
        for character, x0 in zip(text, edges):
            left = int(x0) - MARGIN
            target = blurred[top:bottom, left : int(x0 + CELL) + MARGIN].copy()
            # Only this cell's ink: the neighbours' is not this character's.
            target[:, :MARGIN] = 0
            target[:, MARGIN + int(CELL) :] = 0
            jobs.append((character, index, x0, top, target))
    results = {}
    with ProcessPoolExecutor(9) as pool:
        for character, result in pool.map(fit_cell, jobs):
            results.setdefault(character, []).append(result)
            print(repr(character), len(result["dots"]), round(result["cost"], 1), flush=True)
    with open(out_filepath, "w") as f:
        json.dump(results, f)


if __name__ == "__main__":
    main(sys.argv[1])
