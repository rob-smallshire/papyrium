"""Deskew each character table page once and cache its ink array and cells.

Usage: cache.py  (writes ../cache/p-NNN.npz)
"""

from pathlib import Path

import numpy as np
from cells import cells, load

HERE = Path(__file__).parent
#: The M-1109's manuals and their scans, kept out of git.
_PRINTER_DIRPATH = HERE.parent.parent / "docs" / "local" / "brother-m1109"
#: The owner's manual's 400 dpi page scans, p-NNN.png, with their OCR.
PAGES_DIRPATH = _PRINTER_DIRPATH / "m1109-user-guide-pages"
#: The glyph tools' working files: caches, fits, classifications.
DATA_DIRPATH = _PRINTER_DIRPATH / "glyph-work"
#: Character table scans: Mode I national sets, then Mode II sets 1 and 2.
TABLES = {
    "usa": 107,
    "france": 112,
    "germany": 111,
    "england-1": 114,
    "denmark-1": 113,
    "sweden": 116,
    "italy": 115,
    "spain": 120,
    "japan": 119,
    "norway": 122,
    "denmark-2": 121,
    "england-2": 124,
    "mode2-set1": 123,
    "mode2-set2": 128,
}


def cached(name):
    """(ink, cells) for the table called *name*."""
    cache_filepath = DATA_DIRPATH / "cache" / f"{name}.npz"
    if not cache_filepath.exists():
        cache_filepath.parent.mkdir(exist_ok=True)
        ink = load(PAGES_DIRPATH / f"p-{TABLES[name]:03d}.png")
        boxes = cells(ink)
        np.savez_compressed(cache_filepath, ink=ink, boxes=np.array([boxes[c] for c in range(256)]))
    data = np.load(cache_filepath)
    return data["ink"], {code: tuple(int(v) for v in box) for code, box in enumerate(data["boxes"])}


if __name__ == "__main__":
    for name in TABLES:
        cached(name)
        print(name)
