"""The Panasonic KX-P1080U's draft and near letter quality fonts, from its firmware."""

from __future__ import annotations

from papyrium.core.dotfont import DataDotFont

__all__ = [
    "KXP1080DraftFont",
    "KXP1080DraftItalicFont",
    "KXP1080NlqFont",
    "KXP1080NlqItalicFont",
]


class KXP1080DraftFont(DataDotFont):
    """The KX-P1080U's draft font, extracted from its CPU's internal ROM.

    9 rows, pins 1-9, by 12 columns 1/120 inch apart, the last three
    blank. The ROM lowers a character two pins column by column, so a j's
    hook reaches the ninth pin while its stem does not. A few characters
    have a dot in successive columns, as in the ROM. Covers printable
    ASCII, the 32 international characters and the slashed zero.
    """

    font_filename = "draft.txt"


class KXP1080DraftItalicFont(DataDotFont):
    """The KX-P1080U's draft italics, extracted from its CPU's internal ROM.

    The ROM stores them drawn slanted. Laid out as kx-p1080-draft.
    """

    font_filename = "draft-italic.txt"


class KXP1080NlqFont(DataDotFont):
    """The KX-P1080U's near letter quality font, extracted from its EPROM.

    18 rows: the pins of the first pass on even rows and of the second on
    odd rows, a character with a descender a pin (two rows) lower; 24
    columns 1/240 inch apart. Built as the printer builds it, so no pin
    fires in successive columns. Covers the same characters as draft.
    """

    font_filename = "nlq.txt"


class KXP1080NlqItalicFont(DataDotFont):
    """The KX-P1080U's NLQ italics, slanted as the printer slants them.

    kx-p1080-nlq slanted as the printer does at print time: each pass's
    pins taken in pairs from the bottom, each pair one column further right
    than the pair below. Laid out as kx-p1080-nlq.
    """

    font_filename = "nlq-italic.txt"
