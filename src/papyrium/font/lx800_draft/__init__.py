"""lx800-draft: the Epson LX-800's draft characters, from its firmware."""

from __future__ import annotations

from papyrium.core.dotfont import DataDotFont

__all__ = ["LX800DraftFont"]


class LX800DraftFont(DataDotFont):
    """The Epson LX-800's draft font, extracted from its firmware ROM.

    9 rows by 11 columns 1/120 inch apart, the last two left for spacing;
    a character with a descender sits a pin lower, on the ninth pin.
    Successive columns may both hold a dot, as in the ROM; the printer
    prints such a dot once. Covers printable ASCII, the 32 international
    characters and the slashed zero.
    """
