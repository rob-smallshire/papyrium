"""Cut each printed glyph out of a character table page.

Usage: glyphs.py PAGE_PNG OUT_PNG  (writes a contact sheet of codes 32-255)
"""

import sys

import numpy as np
from cells import cells, load
from PIL import Image
from scipy import ndimage

#: The glyph sits in the upper part of its cell, above and left of the number box.
TOP, BOTTOM = 0.04, 0.72
INSET = 7


def glyph_region(ink, box):
    """The ink of one cell's glyph, with ruled lines and the number box removed."""
    x0, y0, x1, y1 = box
    height = y1 - y0
    region = ink[y0 + INSET : y0 + int(BOTTOM * height), x0 + INSET : x1 - INSET].copy()
    labels, count = ndimage.label(region, structure=np.ones((3, 3)))
    for index, piece in enumerate(ndimage.find_objects(labels), start=1):
        rows = piece[0].stop - piece[0].start
        columns = piece[1].stop - piece[1].start
        area = int((labels[piece] == index).sum())
        # Ruled lines and the number box are long and thin; specks are tiny.
        if (
            rows > 60
            or columns > 70
            or (columns > 50 and rows < 8)
            or (rows > 30 and columns <= 4)
            or area < 12
        ):
            region[labels == index] = False
    return region


def contact_sheet(ink, codes):
    boxes = cells(ink)
    tiles = [glyph_region(ink, boxes[code]) for code in codes]
    tile_height = max(t.shape[0] for t in tiles)
    tile_width = max(t.shape[1] for t in tiles)
    per_row = 16
    sheet = np.zeros(
        ((tile_height + 4) * ((len(tiles) + per_row - 1) // per_row), (tile_width + 4) * per_row),
        bool,
    )
    for index, tile in enumerate(tiles):
        r, c = divmod(index, per_row)
        sheet[
            r * (tile_height + 4) : r * (tile_height + 4) + tile.shape[0],
            c * (tile_width + 4) : c * (tile_width + 4) + tile.shape[1],
        ] = tile
    return Image.fromarray(np.where(sheet, 0, 255).astype(np.uint8))


if __name__ == "__main__":
    ink = load(sys.argv[1])
    contact_sheet(ink, range(32, 128)).save(sys.argv[2])
