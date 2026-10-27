"""The Brother M-1109's draft and NLQ fonts, reconstructed from its printed output."""

from __future__ import annotations

from papyrium.core.dotfont import DataDotFont

__all__ = ["M1109DraftFont", "M1109NlqFont"]


class M1109DraftFont(DataDotFont):
    """The Brother M-1109's draft font, reconstructed from printed output.

    11 columns by 9 rows: capitals 7 dots high, lowercase x-height 5 dots,
    descenders 2 rows. Covers printable ASCII, the 32 international
    characters of the ESC/P national sets, and a slashed zero.
    """

    font_filename = "draft.txt"


class M1109NlqFont(DataDotFont):
    """The Brother M-1109's NLQ font, reconstructed from printed output.

    18 rows by 24 columns: the pins of the first pass on even rows and of
    the second, 1/216 inch lower, on odd rows; columns 1/240 inch apart.
    Covers printable ASCII.
    """

    font_filename = "nlq.txt"
