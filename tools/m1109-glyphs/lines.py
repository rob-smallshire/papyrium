"""Find lines of pica printout on a manual page and their 1/10-inch cells.

A listing printed by the M-1109 at actual size has lines 1/6 inch apart
and characters 1/10 inch apart (66.7 and 40 pixels at 400 dpi, give or
take the reproduction scale). For each line, find the cell phase that puts
the gaps between characters at cell edges.

Usage: lines.py PAGE_PNG [OUT_PNG]  (OUT_PNG marks the cells found)
"""

from __future__ import annotations

import sys
from dataclasses import dataclass

import numpy as np
from cells import load
from PIL import Image, ImageDraw
from scipy import ndimage

#: Pica cell width and line pitch at 400 dpi.
CELL = 40.0
LINE = 400 / 6


@dataclass
class Line:
    top: int  # first ink row of the line's band
    bottom: int
    origin: float  # x of a cell boundary
    pitch: float  # cell width in pixels
    first: int  # index of the first inked cell from origin
    last: int


def bands(ink, min_height=20, max_height=60):
    """Horizontal bands of ink that look like one line of text."""
    profile = ink.sum(axis=1)
    rows = profile > 3
    labels, count = ndimage.label(rows)
    result = []
    for index in range(1, count + 1):
        ys = np.flatnonzero(labels == index)
        if min_height <= len(ys) <= max_height:
            result.append((int(ys[0]), int(ys[-1]) + 1))
    return result


def cell_phase(band_ink, pitch):
    """The x origin, modulo *pitch*, that best puts low ink at cell edges."""
    profile = ndimage.gaussian_filter1d(band_ink.sum(axis=0).astype(float), 2)
    positions = np.arange(len(profile))
    best, best_score = 0.0, None
    for phase in np.arange(0, pitch, 0.5):
        edges = np.arange(phase, len(profile) - 1, pitch)
        score = np.interp(edges, positions, profile).sum()
        if best_score is None or score < best_score:
            best, best_score = phase, score
    return best


def find_lines(ink, pitch=CELL * 1.05):
    lines = []
    for top, bottom in bands(ink):
        band = ink[top:bottom]
        columns = np.flatnonzero(band.any(axis=0))
        if len(columns) < 3 * pitch:
            continue
        origin = cell_phase(band, pitch)
        first = int((columns[0] - origin) // pitch)
        last = int((columns[-1] - origin) // pitch)
        lines.append(Line(top, bottom, origin, pitch, first, last))
    return lines


if __name__ == "__main__":
    ink = load(sys.argv[1])
    lines = find_lines(ink)
    for line in lines:
        print(line.top, line.bottom, round(line.origin, 1), line.first, line.last)
    if len(sys.argv) > 2:
        image = Image.fromarray(np.where(ink, 0, 255).astype(np.uint8)).convert("RGB")
        draw = ImageDraw.Draw(image)
        for line in lines:
            for cell in range(line.first, line.last + 2):
                x = line.origin + cell * line.pitch
                draw.line((x, line.top - 5, x, line.bottom + 5), fill=(255, 0, 0), width=2)
        image.save(sys.argv[2])
