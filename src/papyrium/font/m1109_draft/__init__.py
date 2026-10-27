"""m1109-draft: the Brother M-1109's draft characters, reconstructed for Papyrium."""

from __future__ import annotations

from papyrium.core.dotfont import DataDotFont

__all__ = ["M1109DraftFont"]


class M1109DraftFont(DataDotFont):
    """The Brother M-1109's draft font, reconstructed from printed output.

    11 columns by 9 rows: capitals 7 dots high, lowercase x-height 5 dots,
    descenders 2 rows. Covers printable ASCII, the 32 international
    characters of the ESC/P national sets, and a slashed zero.
    """
