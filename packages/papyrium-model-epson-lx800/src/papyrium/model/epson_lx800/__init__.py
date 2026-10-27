"""The Epson LX-800 9-pin dot-matrix printer."""

from __future__ import annotations

from papyrium.core.model import Interpreter, ModelIdentity, PrinterModel
from papyrium.language.escp import EscpInterpreter, EscpMechanism, options
from papyrium.language.escp.charsets import LX800_CHARACTER_SETS
from papyrium.language.escp.generator import CharacterGenerator
from papyrium.language.escp.mechanism import FX_COMMANDS
from papyrium.model.epson_lx800 import demo

__version__ = "0.1.0"

__all__ = ["EpsonLX800"]

#: Skip-over-perforation, when switched on, skips one inch: six lines at 1/6 inch.
_SKIP_PERFORATION_LINES = 6

#: The LX-800's escape commands: the FX-80's less ESC I, ESC i, ESC j,
#: ESC p, ESC =, ESC > and ESC #, plus near letter quality and its typeface
#: (ESC x, ESC k), justification (ESC a), the character table (ESC t),
#: regular tabs (ESC e), skipping (ESC f) and the cut sheet feeder (ESC EM).
_COMMANDS = (FX_COMMANDS - set("Iijp=>#")) | set("xkatef\x19")


class EpsonLX800(PrinterModel):
    """Epson LX-800: an 80-column, 9-pin dot-matrix printer speaking ESC/P.

    An FX-80 descendant with near letter quality in Roman and Sans Serif,
    condensed elite, the IBM PC character table, thirteen national sets
    and justification, and without proportional spacing.

    Options model its DIP switches, at their factory settings by default,
    and its paper: condensed (no, switch 1-1), slashed-zero (no, 1-2),
    graphics-table (no, 1-3: codes 128-255 from the IBM PC table rather
    than italics), near-letter-quality (no, 1-5), character-set (usa,
    1-6 to 1-8, or any of the thirteen ESC R sets), form-length in inches
    (11, switch 2-1; 12 with it on), skip-perforation (no, 2-3),
    auto-line-feed (no, 2-4), paper-width in inches (9.5 for fanfold, 8.5
    for a sheet), top-offset in inches (19/36), stationery (fanfold, or
    sheet and the listing papers), font (lx800-draft) and nlq-font
    (lx800-nlq-roman), both from the LX-800's firmware, and
    nlq-sans-serif-font (none: the firmware dump at hand has Cyrillic in
    its place, so Sans Serif prints as Roman). The line is centred across
    the paper.
    """

    def __init__(
        self,
        name: str,
        *,
        condensed: bool = False,
        slashed_zero: bool = False,
        graphics_table: bool = False,
        near_letter_quality: bool = False,
        character_set: str = "usa",
        form_length: str = "11",
        skip_perforation: bool = False,
        auto_line_feed: bool = False,
        paper_width: str | None = None,
        top_offset: str = "19/36",
        stationery: str = "fanfold",
        font: str = "lx800-draft",
        nlq_font: str = "lx800-nlq-roman",
        nlq_sans_serif_font: str = "",
        **kwargs,
    ) -> None:
        super().__init__(name=name, **kwargs)
        sans_serif = options.nlq_font(nlq_sans_serif_font) if nlq_sans_serif_font else None
        self._mechanism = EscpMechanism(
            font=options.nine_row_font(font),
            nlq_fonts=(options.nlq_font(nlq_font), sans_serif),
            **options.paper_options(
                paper_width=paper_width,
                form_length=form_length,
                top_offset=top_offset,
                stationery=stationery,
            ),
            columns=80,
            condensed_columns=132,
            auto_line_feed=auto_line_feed,
            character_set=options.character_set_option(character_set, LX800_CHARACTER_SETS),
            character_sets=LX800_CHARACTER_SETS,
            skip_perforation_lines=_SKIP_PERFORATION_LINES if skip_perforation else 0,
            slashed_zero=slashed_zero,
            condensed=condensed,
            near_letter_quality=near_letter_quality,
            graphics_table=graphics_table,
            default_vertical_tabs=False,
            condensed_elite=True,
            nlq=True,
            # The LX-800 underlines with the ninth pin, in the same pass.
            underline_row=8,
            master_select_italic_underline=True,
            carriage_return_ends_one_line_enlarged=True,
            margins_clear_tabs=True,
            generator=CharacterGenerator(prints_adjacent_dots_once=True, nlq_emphasized=True),
            justify_nlq_only=True,
            commands=frozenset(_COMMANDS),
        )

    @property
    def mechanism(self) -> EscpMechanism:
        return self._mechanism

    def identity(self) -> ModelIdentity:
        return ModelIdentity(manufacturer="Epson", model="LX-800")

    def languages(self) -> tuple[str, ...]:
        return ("escp",)

    def demo(self) -> bytes:
        return demo.demo()

    def create_interpreter(self) -> Interpreter:
        return EscpInterpreter(self._mechanism)
