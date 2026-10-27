"""lx800-nlq-roman: the Epson LX-800's near letter quality Roman, from its firmware."""

from __future__ import annotations

from papyrium.core.dotfont import DataDotFont

__all__ = ["LX800NlqRomanFont"]


class LX800NlqRomanFont(DataDotFont):
    """The Epson LX-800's NLQ Roman font, extracted from its firmware ROM.

    18 rows by 24 columns: the pins of the first pass on even rows and of
    the second on odd rows, the ninth pin on rows 16 and 17; columns
    1/240 inch apart, most characters drawn on every other one. Covers
    printable ASCII and the 32 international characters.
    """
