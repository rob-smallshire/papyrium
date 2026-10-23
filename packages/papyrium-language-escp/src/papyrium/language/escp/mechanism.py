"""EscpMechanism: what a particular ESC/P printer is, as its model describes it."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from papyrium.core.dotfont import DotFont
from papyrium.core.page import inches
from papyrium.language.escp.charsets import CharacterSet


@dataclass(frozen=True)
class EscpMechanism:
    """A 9-pin ESC/P printer's character ROM, paper, head and switch settings.

    A printer model builds one of these from its options and hands it to
    :class:`~papyrium.language.escp.interpreter.EscpInterpreter`.

    Lengths are in page units (1/4320 inch).
    """

    #: The character ROM.
    font: DotFont
    #: Width of the paper.
    paper_width: int = inches(Fraction(17, 2))
    #: Length of each fanfold sheet, perforation to perforation, which is also
    #: the power-on form length.
    sheet_length: int = inches(11)
    #: From the paper's left edge to the leftmost print position.
    left_offset: int = inches(Fraction(1, 4))
    #: Pica columns the head can reach; the power-on right margin.
    columns: int = 80
    #: Vertical distance between adjacent pins.
    pin_pitch: int = inches(Fraction(1, 72))
    #: Diameter of a printed dot.
    dot_diameter: int = inches(Fraction(1, 72))
    #: Treat each carriage return as carriage return and line feed.
    auto_line_feed: bool = False
    #: The power-on international character set.
    character_set: CharacterSet = CharacterSet.USA
    #: Power-on skip-over-perforation, in lines; 0 for none.
    skip_perforation_lines: int = 0
    #: Print codes 128-159 as italic characters rather than obey them as controls.
    high_codes_printable: bool = False
    #: Power on in condensed mode.
    condensed: bool = False
    #: The ESC command characters this model obeys; None for all that are implemented.
    commands: frozenset[str] | None = None
