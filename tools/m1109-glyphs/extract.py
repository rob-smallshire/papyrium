"""Fit every Mode I roman glyph, grouping its copies across the national tables.

Each group is a ROM location: ASCII 32-126, or one of the 32 international
characters at 0-31. Writes ../fits.json with each group's dots on the fitted
lattice and, for each copy used, where lattice (0, 0) falls on its page.

Usage: extract.py [WORKERS]
"""

import json
import sys
from concurrent.futures import ProcessPoolExecutor

from cache import DATA_DIRPATH, TABLES, cached
from fit import JointFitter, crop
from glyphs import INSET, glyph_region

from papyrium.language.escp.charsets import CharacterSet, rom_location

SCALE_X, SCALE_Y, DIAMETER = 1.05, 1.02, 6.5
MODE_1 = list(TABLES)[:12]
#: ROM locations of the national codes for the sets the FX-80 lacks (ESC R 9-11).
EXTRA_LOCATIONS = {
    9: {36: 11, 64: 29, 91: 18, 92: 20, 93: 13, 94: 25, 96: 30, 123: 19, 124: 21, 125: 14, 126: 28},
    10: {64: 29, 91: 18, 92: 20, 93: 13, 94: 25, 96: 30, 123: 19, 124: 21, 125: 14, 126: 28},
    11: {96: 6},
}


def location(set_number, code):
    if set_number in EXTRA_LOCATIONS:
        return EXTRA_LOCATIONS[set_number].get(code, code)
    return rom_location(code, CharacterSet(set_number))


def groups():
    result = {}
    for set_number, name in enumerate(MODE_1):
        for code in range(33, 127):
            result.setdefault(location(set_number, code), []).append((name, code))
    return result


def fit_group(item):
    rom, copies = item
    fitter = JointFitter(SCALE_X, SCALE_Y, DIAMETER)
    glyphs, offsets = [], []
    for name, code in copies:
        ink, boxes = cached(name)
        glyph, (cx, cy) = crop(glyph_region(ink, boxes[code]))
        if glyph is None:
            continue
        x0, y0, _, _ = boxes[code]
        glyphs.append(glyph)
        offsets.append((name, code, x0 + INSET + cx, y0 + INSET + cy))
    fit, origins, kept = fitter.fit_all(glyphs)
    used = []
    for (ox, oy), index in zip(origins, kept):
        name, code, x, y = offsets[index]
        used.append({"table": name, "code": code, "x": x + ox, "y": y + oy})
    return rom, {
        "dots": sorted(fit.dots),
        "cost": fit.cost,
        "copies": len(glyphs),
        "used": used,
    }


if __name__ == "__main__":
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    for name in TABLES:
        cached(name)
    results = {}
    with ProcessPoolExecutor(workers) as pool:
        for rom, result in pool.map(fit_group, sorted(groups().items())):
            results[rom] = result
            print(
                rom,
                len(result["used"]),
                "/",
                result["copies"],
                round(result["cost"], 1),
                flush=True,
            )
    out_filepath = DATA_DIRPATH / "fits.json"
    out_filepath.write_text(json.dumps(results, indent=1))
