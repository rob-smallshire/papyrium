"""The Proprinter's proportional spacing: each character's width and offset.

From the IBM Proprinter Family Technical Reference, Figure A-1, the
character width table of the Proprinter II and its kin for code page
437. A character's width is the columns of 1/120 inch it takes in
proportional spacing, and its offset the columns of its cell skipped
before those. Characters not listed take the whole cell, twelve columns
from the first.
"""

from __future__ import annotations

#: Width and offset of a character the figure gives the whole cell.
FULL_CELL = (12, 0)

#: Width and offset, in columns, of the characters narrower than the cell.
_NARROWER = {
    4: (10, 1),
    33: (5, 4), 34: (8, 2), 39: (6, 3), 40: (6, 3), 41: (6, 3), 44: (6, 3),
    46: (6, 3), 47: (10, 1), 49: (8, 2), 58: (6, 3), 59: (6, 3), 60: (10, 1),
    62: (10, 1), 63: (10, 1), 73: (8, 2), 88: (10, 1), 91: (8, 2), 92: (10, 1),
    93: (8, 2), 96: (6, 3), 98: (11, 0), 99: (11, 0), 100: (11, 0), 103: (11, 0),
    105: (8, 2), 106: (8, 2), 107: (10, 1), 108: (8, 2), 111: (11, 0),
    112: (11, 0), 113: (11, 0), 114: (11, 0), 116: (10, 1), 120: (10, 1),
    122: (10, 1), 123: (9, 1), 124: (4, 4), 125: (9, 2),
    139: (9, 1), 140: (10, 1), 141: (8, 2), 147: (11, 0), 148: (11, 0),
    149: (11, 0), 152: (11, 0), 153: (11, 0),
    226: (11, 0), 231: (11, 0), 238: (10, 1), 242: (10, 1), 243: (10, 1),
    247: (11, 0), 248: (8, 2), 249: (6, 3), 250: (6, 3), 252: (10, 1),
    253: (8, 2), 254: (8, 2),
}  # fmt: skip

#: Width and offset of each of the 256 characters, by code.
PROPORTIONAL_WIDTHS: tuple[tuple[int, int], ...] = tuple(
    _NARROWER.get(code, FULL_CELL) for code in range(256)
)
