"""Find the 16 x 16 character cells in a scanned M-1109 character table page.

The table's ruled lines are long dark runs. Find rows and columns whose
dark fraction is high, cluster them into lines, and take the last 17
horizontal and 17 vertical lines as the code grid (the header rows and
columns come first).

Usage: cells.py PAGE_PNG [--show OUT_PNG]
"""

import sys
from pathlib import Path

import numpy as np
from PIL import Image


def _sharpness(image):
    profile = (np.asarray(image) < 128).sum(axis=1).astype(float)
    return (profile**2).sum()


def skew_angle(image, span=2.0, step=0.05):
    """The rotation, in degrees, that makes the ruled lines most horizontal."""
    small = image.reduce(4)
    angles = np.arange(-span, span + step, step)
    scores = [
        _sharpness(small.rotate(angle, resample=Image.BILINEAR, fillcolor=255)) for angle in angles
    ]
    coarse = angles[int(np.argmax(scores))]
    fine = np.arange(coarse - step, coarse + step, step / 10)
    scores = [
        _sharpness(image.rotate(angle, resample=Image.BILINEAR, fillcolor=255)) for angle in fine
    ]
    return float(fine[int(np.argmax(scores))])


def load(page_filepath):
    """The deskewed page as a boolean array, True for ink."""
    image = Image.open(page_filepath).convert("L")
    angle = skew_angle(image)
    image = image.rotate(angle, resample=Image.BILINEAR, fillcolor=255)
    return np.asarray(image) < 128


def _lines(profile, threshold, min_gap=8):
    """Centres of runs of indices where *profile* exceeds *threshold*."""
    indices = np.flatnonzero(profile > threshold)
    lines, start, previous = [], None, None
    for index in indices:
        if start is None:
            start = previous = index
        elif index - previous > min_gap:
            lines.append((start + previous) / 2)
            start = index
        previous = index
    if start is not None:
        lines.append((start + previous) / 2)
    return lines


def grid(ink):
    """(row_lines, column_lines): 17 y positions and 17 x positions bounding the cells."""
    height, width = ink.shape
    # Restrict to the table's bounding box: the longest lines.
    rows = _lines(ink.sum(axis=1), 0.5 * ink.sum(axis=1).max())
    top, bottom = int(rows[0]), int(rows[-1])
    profile = ink[top:bottom].sum(axis=0)
    profile[profile > 0.98 * (bottom - top)] = 0  # The scanner's page edge.
    columns = _lines(profile, 0.6 * (bottom - top))
    left, right = int(columns[0]), int(columns[-1])
    rows = _lines(ink[:, left:right].sum(axis=1), 0.4 * (right - left))
    return _fit(rows, 145.3), _fit(columns, 124.7)


def _fit(found, pitch, count=17, tolerance=12):
    """*count* evenly spaced lines ending at the last found, snapped to found lines."""
    end = found[-1]
    fitted = []
    for index in range(count):
        predicted = end - (count - 1 - index) * pitch
        nearest = min(found, key=lambda line: abs(line - predicted))
        fitted.append(nearest if abs(nearest - predicted) < tolerance else predicted)
    return fitted


def cells(ink):
    """{code: (x0, y0, x1, y1)} for codes 0-255; column is the high nibble."""
    rows, columns = grid(ink)
    result = {}
    for high in range(16):
        for low in range(16):
            result[high * 16 + low] = (
                int(columns[high]),
                int(rows[low]),
                int(columns[high + 1]),
                int(rows[low + 1]),
            )
    return result


if __name__ == "__main__":
    page_filepath = Path(sys.argv[1])
    ink = load(page_filepath)
    rows, columns = grid(ink)
    print("rows", [round(r) for r in rows])
    print("columns", [round(c) for c in columns])
    print("row pitch", np.diff(rows).round(1))
    print("column pitch", np.diff(columns).round(1))
