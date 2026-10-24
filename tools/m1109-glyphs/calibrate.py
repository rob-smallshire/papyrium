"""Find the reproduction scale and dot diameter that best explain the scans.

Usage: calibrate.py
"""

import numpy as np
from cache import cached
from fit import Fitter, crop
from glyphs import glyph_region

SAMPLE = "HMEW=_|1Ax8%k"

if __name__ == "__main__":
    ink, boxes = cached("usa")
    glyphs = [crop(glyph_region(ink, boxes[ord(c)]))[0] for c in SAMPLE]
    results = []
    for scale in np.arange(0.86, 1.0, 0.02):
        for diameter in (5.5, 6.0, 6.5):
            fitter = Fitter(scale, diameter)
            total = sum(fitter.fit(g).cost for g in glyphs)
            results.append((total, scale, diameter))
            print(f"scale {scale:.2f} diameter {diameter}: {total:.1f}", flush=True)
    print("best", min(results))
