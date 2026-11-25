"""The Commodore MPS-803's characters, from its firmware."""

from __future__ import annotations

from papyrium.core.dotfont import DataDotFont

__all__ = ["Mps803Font"]


class Mps803Font(DataDotFont):
    """The Commodore MPS-803's characters, extracted from its firmware ROM.

    159 glyphs, 7 rows by 6 columns: full dots 1/60 inch apart, one to a
    carriage step, so successive columns may both hold a dot; letters use
    five columns and graphics all six, joining their neighbours. Covers
    both of the printer's sets, PETSCII's upper case and graphics and its
    lower and upper case, each glyph keyed by its Unicode character.
    """

    font_filename = "glyphs.txt"
