"""The Epson LX-800's draft and near letter quality Roman fonts, from its firmware."""

from __future__ import annotations

from papyrium.core.dotfont import DataDotFont

__all__ = ["LX800DraftFont", "LX800NlqRomanFont"]


class LX800DraftFont(DataDotFont):
    """The Epson LX-800's draft font, extracted from its firmware ROM.

    9 rows by 11 columns 1/120 inch apart, the last two left for spacing;
    a character with a descender sits a pin lower, on the ninth pin.
    Successive columns may both hold a dot, as in the ROM; the printer
    prints such a dot once. Covers printable ASCII, the 32 international
    characters and the slashed zero.
    """

    font_filename = "draft.txt"


class LX800NlqRomanFont(DataDotFont):
    """The Epson LX-800's NLQ Roman font, extracted from its firmware ROM.

    18 rows by 24 columns: the pins of the first pass on even rows and of
    the second on odd rows, the ninth pin on rows 16 and 17; columns
    1/240 inch apart, most characters drawn on every other one. Covers
    printable ASCII and the 32 international characters.
    """

    font_filename = "nlq-roman.txt"
