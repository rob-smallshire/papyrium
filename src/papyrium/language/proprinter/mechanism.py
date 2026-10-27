"""ProprinterMechanism: what a particular Proprinter is, as its model describes it."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from papyrium.core.dotfont import DotFont
from papyrium.core.page import inches
from papyrium.language.escp.generator import CharacterGenerator
from papyrium.language.escp.mechanism import EscpMechanism

#: The 9-wire Proprinters' character generator: draft prints a dot that
#: follows a printed one in its row only once, and NLQ's second pass is
#: half a dot, 1/144 inch, below its first.
PROPRINTER_GENERATOR = CharacterGenerator(
    prints_adjacent_dots_once=True,
    nlq_pass_offset=inches(1) // 144,
)


@dataclass(frozen=True)
class ProprinterMechanism(EscpMechanism):
    """A 9-wire IBM Proprinter's characters, paper, head and switches.

    The fields it shares with :class:`EscpMechanism` mean the same here,
    with the defaults of a Proprinter II at its U.S. factory settings: an
    8-inch line, character set 1 (switch 5 off), and a line feed that only
    feeds (switch 6 off). *nlq_fonts* is unused: NLQ is made from the
    draft characters, and NLQ II has a field of its own.
    """

    #: Fastfont, the Proprinter II's 12 cpi draft face, ten columns wide;
    #: None for a printer without it, on which ESC I 1 prints draft.
    fastfont: DotFont | None = None
    #: NLQ II, the Proprinter II's second NLQ face, 24 columns by 18 rows in
    #: two passes; None for a printer without it, on which ESC I 3 prints NLQ.
    nlq_ii_font: DotFont | None = None
    #: Switch 1: a form feed at the top of a form with nothing printed on it
    #: is ignored.
    form_feed_at_top_ignored: bool = False

    generator: CharacterGenerator = PROPRINTER_GENERATOR
    paper_width: int = inches(Fraction(17, 2))
    columns: int = 80
    condensed_columns: int = 137
    ibm_set: int = 1
    line_feed_returns: bool = False
    default_vertical_tabs: bool = False
    carriage_return_ends_one_line_enlarged: bool = True
    cancel_ends_one_line_enlarged: bool = True
    proportional_emphasized: bool = False
