"""CbmMechanism: how a Commodore printer model sets up the language."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from papyrium.core.dotfont import DotFont
from papyrium.core.page import inches
from papyrium.core.stationery import Stationery


@dataclass(frozen=True)
class CbmMechanism:
    """A Commodore printer's characters, paper and switches.

    Lengths are in page units (1/4320 inch). *left_offset* is from the
    paper's left edge to the line's first dot; *top_offset* from the top
    of the first sheet to the first line's top wire.
    """

    font: DotFont
    #: The business set (secondary address 7) rather than the graphic set (0).
    business_set: bool = False
    #: Paper steps of 1/216 inch a text line feeds: 36 (1/6 inch) or 27 (1/8).
    line_feed_steps: int = 36
    paper_width: int = inches(Fraction(19, 2))
    sheet_length: int = inches(11)
    left_offset: int = inches(Fraction(3, 4))
    top_offset: int = 0
    stationery: Stationery | None = None
    dot_diameter: int = inches(1) // 72
