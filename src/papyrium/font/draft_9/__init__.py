"""draft-9: a 9-pin dot-matrix font designed for Papyrium."""

from __future__ import annotations

from papyrium.core.dotfont import DataDotFont

__all__ = ["Draft9Font"]


class Draft9Font(DataDotFont):
    """An original 9-pin draft font in the style of 1980s dot-matrix printers.

    11 columns by 9 rows: capitals 7 dots high, lowercase x-height 5 dots,
    descenders 2 rows. Covers printable ASCII and the Epson international
    character sets.
    """
