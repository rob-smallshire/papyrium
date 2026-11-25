"""The Centronics GLP's draft and graphics fonts, from its firmware."""

from __future__ import annotations

from papyrium.core.dotfont import DataDotFont

__all__ = ["GlpDraftFont", "GlpGraphicsFont", "GlpNlqFont"]


class GlpDraftFont(DataDotFont):
    """The Centronics GLP's draft characters (Model 3101), from its firmware.

    Extracted from the Schneider NLQ401's EPROM: 9 rows by 11 columns 1/120
    inch apart in a 12-column pica cell, no pin striking in two successive
    columns. ; _ g p q y sit a pin lower, as the firmware prints them.
    Covers ASCII and character set 2's German characters § Ä Ö Ü ä ö ü ß.
    """

    font_filename = "draft.txt"


class GlpGraphicsFont(DataDotFont):
    """The Centronics GLP's graphics characters, the Amstrad CPC's codes 129-255.

    Extracted from the Schneider NLQ401's EPROM: 8 rows by 11 columns, the
    dots on the even columns, 1/60 inch apart, so that neighbouring cells
    join. Block and line drawing, accents and symbols, Greek, diagonals and
    shades, faces, card suits, arrows and stick figures.
    """

    font_filename = "graphics.txt"


class GlpNlqFont(DataDotFont):
    """The Schneider NLQ401's near letter quality characters, from its firmware.

    Schneider's addition to the Centronics GLP. Two passes of eight pins,
    the first's on even rows and the second's, 1/216 inch lower, on odd
    rows: 18 rows by 39 columns 1/360 inch apart, 36 to the pica cell, so a
    character may reach into the next. ; _ g p q y sit a pin lower, as the
    firmware prints them. Covers ASCII and § Ä Ö Ü ä ö ü ß.
    """

    font_filename = "nlq.txt"
