"""EscpMechanism: what a particular ESC/P printer is, as its model describes it."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from papyrium.core.dotfont import DotFont
from papyrium.core.page import inches
from papyrium.core.stationery import Stationery
from papyrium.language.escp.charsets import FX_CHARACTER_SETS, CharacterSet

#: The codes the FX-80 always obeys as controls, even when ESC I makes the
#: other low codes print: BEL, BS, HT, LF, VT, FF, CR, SO, SI, DC1-DC4, CAN, ESC.
FX_CONTROLS = frozenset({7, 8, 9, 10, 11, 12, 13, 14, 15, 17, 18, 19, 20, 24, 27})


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
    #: The kind of paper; None for a blank sheet.
    stationery: Stationery | None = None
    #: From the paper's left edge to the leftmost print position.
    left_offset: int = inches(Fraction(1, 4))
    #: From the top of the sheet to the top of the first line at power-on:
    #: where the operator wound the paper before switching on.
    top_offset: int = 0
    #: Pica columns the head can reach; the power-on right margin.
    columns: int = 80
    #: Condensed characters in a line at the power-on right margin.
    condensed_columns: int = 132
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
    #: Print zero slashed, using the font's U+0030 U+0338 glyph.
    slashed_zero: bool = False
    #: Power on in condensed mode.
    condensed: bool = False
    #: Power on printing emphasized.
    emphasized: bool = False
    #: Obey DC1 and DC3; otherwise the printer is always selected.
    software_select: bool = False
    #: The RAM holds user-defined characters rather than serving as a buffer.
    user_defined_characters: bool = True
    #: The dot row the underline prints on: 8 is the ninth pin, 9 one row below it.
    underline_row: int = 8
    #: The ESC R international sets the printer has, in its own numbering.
    character_sets: tuple[CharacterSet, ...] = FX_CHARACTER_SETS
    #: Low codes obeyed as controls even when ESC I makes the others print.
    controls: frozenset[int] = FX_CONTROLS
    #: Power on with vertical tab stops every other line; otherwise VT is LF.
    default_vertical_tabs: bool = True
    #: ESC C also clears the vertical tab stops.
    form_length_clears_vertical_tabs: bool = False
    #: CAN also ends SO's one-line enlarged mode.
    cancel_ends_one_line_enlarged: bool = False
    #: Condensed elite prints at 20 characters an inch; otherwise elite masks condensed.
    condensed_elite: bool = False
    #: The ESC * bit-image modes the printer has.
    graphics_modes: frozenset[int] = frozenset(range(7))
    #: ESC x selects near letter quality.
    nlq: bool = False
    #: Power on printing near letter quality.
    near_letter_quality: bool = False
    #: The near letter quality characters: 18 rows, the pins of a first pass
    #: on even rows and of a second pass 1/216 inch lower on odd rows, by 24
    #: columns of 1/240 inch to the pica cell. None prints NLQ as draft
    #: struck twice.
    nlq_font: DotFont | None = None
    #: The ESC command characters this model obeys; None for all that are implemented.
    commands: frozenset[str] | None = None
