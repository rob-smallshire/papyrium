"""Recover a glyph's dot matrix by fitting rendered dots to the scanned glyph.

The scan cannot resolve neighbouring dots, so instead of reading dots off
the image, search for the set of dots which, rendered as discs at the
printer's dot pitch and blurred like the scan, best matches it. Dots lie on
a lattice of rows 1/72 inch apart and half-columns 1/120 inch apart, and no
row has dots in two adjacent half-columns.

The lattice origin returned is the image position of row 0, half-column 0
of the fitted lattice, so glyphs can be aligned to each other afterwards.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import ndimage

#: Dot pitches at 400 dpi for a print at actual size; *scale* adjusts for the reproduction.
ROW_PITCH = 400 / 72
COLUMN_PITCH = 400 / 120
BLUR = 1.5


@dataclass
class Fit:
    dots: set[tuple[int, int]]  # (row, half_column) on the fitted lattice
    origin: tuple[float, float]  # image (x, y) of lattice row 0, half-column 0
    cost: float


class Fitter:
    def __init__(self, scale_x: float, scale_y: float, diameter: float):
        self.row_pitch = ROW_PITCH * scale_y
        self.column_pitch = COLUMN_PITCH * scale_x
        self.radius = diameter / 2

    def render(self, dots, origin, shape):
        height, width = shape
        image = np.zeros(shape, bool)
        r = self.radius
        ys, xs = np.ogrid[:height, :width]
        for row, column in dots:
            cx = origin[0] + column * self.column_pitch
            cy = origin[1] + row * self.row_pitch
            y0, y1 = max(0, int(cy - r - 1)), min(height, int(cy + r + 2))
            x0, x1 = max(0, int(cx - r - 1)), min(width, int(cx + r + 2))
            if y0 >= y1 or x0 >= x1:
                continue
            patch = (xs[:, x0:x1] - cx) ** 2 + (ys[y0:y1, :] - cy) ** 2 <= r * r
            image[y0:y1, x0:x1] |= patch
        return image

    def cost(self, dots, origin, target_blurred):
        rendered = ndimage.gaussian_filter(
            self.render(dots, origin, target_blurred.shape).astype(float), BLUR
        )
        return float(((rendered - target_blurred) ** 2).sum())

    def _lattice(self, shape, origin):
        rows = int((shape[0] - origin[1]) / self.row_pitch) + 1
        columns = int((shape[1] - origin[0]) / self.column_pitch) + 1
        return rows, columns

    def _initial(self, target_blurred, origin):
        """Threshold the blurred scan at lattice points, keeping no two adjacent in a row."""
        rows, columns = self._lattice(target_blurred.shape, origin)
        dots = set()
        for row in range(rows):
            y = origin[1] + row * self.row_pitch
            values = []
            for column in range(columns):
                x = origin[0] + column * self.column_pitch
                values.append(
                    ndimage.map_coordinates(target_blurred, [[y], [x]], order=1, mode="constant")[0]
                )
            # Best non-adjacent subset with value above threshold: DP over columns.
            gain = [v - 0.45 for v in values]
            best = [0.0] * (columns + 2)
            take = [False] * (columns + 2)
            for column in range(columns - 1, -1, -1):
                with_it = gain[column] + best[column + 2]
                if with_it > best[column + 1]:
                    best[column], take[column] = with_it, True
                else:
                    best[column] = best[column + 1]
            column = 0
            while column < columns:
                if take[column] and gain[column] > 0:
                    dots.add((row, column))
                    column += 2
                else:
                    column += 1
        return dots

    def _improve(self, dots, origin, target_blurred):
        rows, columns = self._lattice(target_blurred.shape, origin)
        cost = self.cost(dots, origin, target_blurred)
        improved = True
        while improved:
            improved = False
            for row in range(rows):
                for column in range(columns):
                    candidates = []
                    if (row, column) in dots:
                        candidates.append(dots - {(row, column)})
                        for step in (-1, 1):
                            moved = (row, column + step)
                            if 0 <= moved[1] < columns and (row, column + 2 * step) not in dots:
                                candidates.append((dots - {(row, column)}) | {moved})
                    elif (row, column - 1) not in dots and (row, column + 1) not in dots:
                        candidates.append(dots | {(row, column)})
                    for candidate in candidates:
                        candidate_cost = self.cost(candidate, origin, target_blurred)
                        if candidate_cost < cost - 1e-6:
                            dots, cost, improved = candidate, candidate_cost, True
                            break
        return dots, cost

    def fit(self, glyph):
        """Fit *glyph*, a boolean ink array cropped with a margin around the glyph."""
        target = ndimage.gaussian_filter(glyph.astype(float), BLUR)
        best = None
        for oy in np.arange(0, self.row_pitch, 1.0):
            for ox in np.arange(0, self.column_pitch, 0.75):
                origin = (ox, oy)
                dots = self._initial(target, origin)
                cost = self.cost(dots, origin, target)
                if best is None or cost < best.cost:
                    best = Fit(dots, origin, cost)
        # Refine the phase finely around the best, then improve the dots.
        for oy in np.arange(best.origin[1] - 0.5, best.origin[1] + 0.51, 0.25):
            for ox in np.arange(best.origin[0] - 0.375, best.origin[0] + 0.38, 0.25):
                cost = self.cost(best.dots, (ox, oy), target)
                if cost < best.cost:
                    best = Fit(best.dots, (ox, oy), cost)
        dots, cost = self._improve(best.dots, best.origin, target)
        return Fit(dots, best.origin, cost)


def crop(ink, margin=8):
    """*ink* cropped to its bounding box plus *margin*, and the crop's offset."""
    ys, xs = np.nonzero(ink)
    if len(ys) == 0:
        return None, (0, 0)
    y0, x0 = max(0, ys.min() - margin), max(0, xs.min() - margin)
    y1, x1 = ys.max() + margin + 1, xs.max() + margin + 1
    padded = np.zeros((y1 - y0, x1 - x0), bool)
    region = ink[y0:y1, x0:x1]
    padded[: region.shape[0], : region.shape[1]] = region
    return padded, (x0, y0)


def ascii_art(dots):
    if not dots:
        return "(blank)"
    rows = [r for r, _ in dots]
    columns = [c for _, c in dots]
    lines = []
    for row in range(min(rows), max(rows) + 1):
        lines.append(
            "".join("#" if (row, c) in dots else "." for c in range(min(columns), max(columns) + 1))
        )
    return "\n".join(lines)


def _align(reference, dots):
    """The lattice shift (rows, columns) that best overlays *dots* on *reference*."""
    best, best_overlap = (0, 0), -1
    for dr in range(-3, 4):
        for dc in range(-6, 7):
            overlap = len(reference & {(r + dr, c + dc) for r, c in dots})
            if overlap > best_overlap:
                best, best_overlap = (dr, dc), overlap
    return best


class JointFitter(Fitter):
    """Fit one dot matrix to several scans of the same glyph."""

    def joint_cost(self, dots, origins, targets):
        return sum(self.cost(dots, origin, target) for origin, target in zip(origins, targets))

    def fit_all(self, glyphs):
        """Fit all of *glyphs*, then again without any that fit much worse than the rest."""
        fit, origins, costs = self._fit_all(glyphs)
        median = float(np.median(costs))
        kept = [i for i, c in enumerate(costs) if c <= 2.5 * median + 5]
        if 3 <= len(kept) < len(glyphs):
            fit, origins, costs = self._fit_all([glyphs[i] for i in kept])
        else:
            kept = list(range(len(glyphs)))
        return fit, origins, kept

    def _fit_all(self, glyphs):
        fits = [self.fit(glyph) for glyph in glyphs]
        targets = [ndimage.gaussian_filter(g.astype(float), BLUR) for g in glyphs]
        reference = min(fits, key=lambda f: f.cost)
        origins = []
        for fit in fits:
            dr, dc = _align(reference.dots, fit.dots)
            # Re-express this fit's origin on the reference lattice.
            origins.append(
                (fit.origin[0] - dc * self.column_pitch, fit.origin[1] - dr * self.row_pitch)
            )
        votes = {}
        for fit in fits:
            dr, dc = _align(reference.dots, fit.dots)
            for r, c in fit.dots:
                votes[(r + dr, c + dc)] = votes.get((r + dr, c + dc), 0) + 1
        dots = {position for position, count in votes.items() if 2 * count > len(fits)}
        # Remove adjacent pairs the vote may have produced, keeping the stronger.
        for r, c in sorted(dots):
            if (r, c) in dots and (r, c + 1) in dots:
                dots.discard((r, c) if votes[(r, c)] < votes[(r, c + 1)] else (r, c + 1))
        rows = range(min(r for r, _ in votes) - 1, max(r for r, _ in votes) + 2)
        columns = range(min(c for _, c in votes) - 1, max(c for _, c in votes) + 2)
        cost = self.joint_cost(dots, origins, targets)
        improved = True
        while improved:
            improved = False
            for row in rows:
                for column in columns:
                    candidates = []
                    if (row, column) in dots:
                        candidates.append(dots - {(row, column)})
                        for step in (-1, 1):
                            if (row, column + 2 * step) not in dots:
                                candidates.append((dots - {(row, column)}) | {(row, column + step)})
                    elif (row, column - 1) not in dots and (row, column + 1) not in dots:
                        candidates.append(dots | {(row, column)})
                    for candidate in candidates:
                        candidate_cost = self.joint_cost(candidate, origins, targets)
                        if candidate_cost < cost - 1e-6:
                            dots, cost, improved = candidate, candidate_cost, True
                            break
            # Let each scan's phase settle against the shared matrix.
            for index, target in enumerate(targets):
                ox, oy = origins[index]
                for dx in (-0.5, -0.25, 0.25, 0.5):
                    for dy in (-0.5, -0.25, 0.25, 0.5):
                        trial = (ox + dx, oy + dy)
                        old = self.cost(dots, origins[index], target)
                        if self.cost(dots, trial, target) < old - 1e-6:
                            origins[index] = trial
                            cost = self.joint_cost(dots, origins, targets)
                            improved = True
        costs = [self.cost(dots, o, t) for o, t in zip(origins, targets)]
        return Fit(dots, origins[0], cost / len(glyphs)), origins, costs
