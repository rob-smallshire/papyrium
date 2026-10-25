"""Identify the characters in lines of pica printout and where their dots sit.

Each fitted table glyph is rendered at listing scale and matched against
every cell over small offsets. A confident match gives the glyph's lattice
position relative to its cell's left edge and to its line's capital
height, which the table scans cannot give.

Usage: classify.py OUT_JSON PAGE_INDEX...
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from cache import DATA_DIRPATH, PAGES_DIRPATH
from cells import load
from fit import BLUR, COLUMN_PITCH, ROW_PITCH, Fitter
from lines import find_lines
from scipy import ndimage, signal

HERE = Path(__file__).parent
SCALE_X, SCALE_Y = 40.25 / 40, 66.9 / (400 / 6)
PX, PY = COLUMN_PITCH * SCALE_X, ROW_PITCH * SCALE_Y
MARGIN = 6


def templates():
    """{rom: (blurred image, (x, y) of lattice (0, 0) in it, dots)}."""
    fits = json.loads((DATA_DIRPATH / "fits.json").read_text())
    fitter = Fitter(SCALE_X, SCALE_Y, 6.5)
    result = {}
    for rom, fit in fits.items():
        dots = [tuple(d) for d in fit["dots"]]
        if not dots:
            continue
        r0 = min(r for r, _ in dots)
        c0 = min(c for _, c in dots)
        dots = [(r - r0, c - c0) for r, c in dots]
        height = int(max(r for r, _ in dots) * PY + 2 * MARGIN + 7)
        width = int(max(c for _, c in dots) * PX + 2 * MARGIN + 7)
        origin = (MARGIN + 3.0, MARGIN + 3.0)
        image = fitter.render(set(dots), origin, (height, width)).astype(float)
        result[int(rom)] = (ndimage.gaussian_filter(image, BLUR), origin, dots)
    return result


def best_match(cell, templates):
    """(rom, cost, second_cost, x, y): the template whose placement best explains *cell*."""
    energy = (cell**2).sum()
    scored = []
    for rom, (image, origin, _) in templates.items():
        if image.shape[0] > cell.shape[0] or image.shape[1] > cell.shape[1]:
            continue
        correlation = signal.correlate(cell, image, mode="valid", method="fft")
        # Squared error of the template placed at each offset, ignoring the
        # cell's ink outside the template, which is then penalised below.
        template_energy = (image**2).sum()
        local = signal.correlate(cell**2, np.ones_like(image), mode="valid", method="fft")
        cost = template_energy - 2 * correlation + local + (energy - local)
        index = np.unravel_index(np.argmin(cost), cost.shape)
        scored.append((float(cost[index]), rom, index[1] + origin[0], index[0] + origin[1]))
    scored.sort()
    (cost, rom, x, y), second = scored[0], scored[1][0]
    return rom, cost, second, x, y


def classify_page(page_filepath, templates):
    ink = load(page_filepath)
    blurred = ndimage.gaussian_filter(ink.astype(float), BLUR)
    found = []
    for line in find_lines(ink, pitch=40.25):
        y0 = max(0, line.top - 14)
        y1 = min(ink.shape[0], line.bottom + 14)
        line_found = []
        for cell in range(line.first, line.last + 1):
            x0 = int(line.origin + cell * line.pitch) - 8
            x1 = int(line.origin + (cell + 1) * line.pitch) + 8
            if x0 < 0 or x1 > ink.shape[1]:
                continue
            core = ink[y0:y1, x0 + 8 : x1 - 8]
            if core.sum() < 15:
                continue
            rom, cost, second, x, y = best_match(blurred[y0:y1, x0:x1], templates)
            line_found.append(
                {
                    "rom": rom,
                    "cost": cost,
                    "margin": second - cost,
                    # Lattice (0, 0) of the glyph's bounding dots, relative to the
                    # cell's left edge, in pixels; and its page y.
                    "x": x0 + x - (line.origin + cell * line.pitch),
                    "y": y0 + y,
                }
            )
        found.append({"top": line.top, "cells": line_found})
    return found


if __name__ == "__main__":
    out_filepath = Path(sys.argv[1])
    result = {}
    t = templates()
    for page_index in sys.argv[2:]:
        page_filepath = PAGES_DIRPATH / f"p-{int(page_index):03d}.png"
        result[page_index] = classify_page(page_filepath, t)
        print(page_index, sum(len(line["cells"]) for line in result[page_index]), flush=True)
    out_filepath.write_text(json.dumps(result))
