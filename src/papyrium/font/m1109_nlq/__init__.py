"""m1109-nlq: the Brother M-1109's near letter quality characters, reconstructed."""

from __future__ import annotations

from papyrium.core.dotfont import DataDotFont

__all__ = ["M1109NlqFont"]


class M1109NlqFont(DataDotFont):
    """The Brother M-1109's NLQ font, reconstructed from printed output.

    18 rows by 24 columns: the pins of the first pass on even rows and of
    the second, 1/216 inch lower, on odd rows; columns 1/240 inch apart.
    Covers printable ASCII.
    """
