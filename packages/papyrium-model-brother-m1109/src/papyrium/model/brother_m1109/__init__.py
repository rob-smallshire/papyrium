"""The Brother M-1109 9-pin dot-matrix printer."""

from __future__ import annotations

from papyrium.core.model import Interpreter, ModelIdentity, PrinterModel
from papyrium.language.escp import EscpInterpreter, EscpMechanism, options

__version__ = "0.1.0"

__all__ = ["BrotherM1109"]

#: Skip-over-perforation, when switched on, skips one inch: six lines at 1/6 inch.
_SKIP_PERFORATION_LINES = 6

#: Low codes Mode I obeys as controls even when ESC I makes the others print:
#: BS, HT, LF, VT, FF, CR, SO, SI, DC2, DC3, DC4 and ESC. BEL, DC1 and CAN print.
_CONTROLS = frozenset({8, 9, 10, 11, 12, 13, 14, 15, 18, 19, 20, 27})

#: The Mode I escape commands: the FX-80's, less ESC ^, ESC ?, ESC j, ESC i
#: and the escaped SO and SI, plus ESC x for near letter quality.
_COMMANDS = frozenset("!#=>%&:*KLYZ-/0123A J456I789<@BCDEFGHMNOQlRSTUWbpsx".replace(" ", ""))


class BrotherM1109(PrinterModel):
    """Brother M-1109: an 80-column, 9-pin dot-matrix printer in its Mode I.

    Mode I (switch 2-2 on, the factory setting) is Epson FX-80 compatible,
    with near letter quality, condensed elite, three more national sets and
    a 144 dpi bit-image mode; Mode II, its IBM personality, is not modelled.

    Options model its DIP switches, at their factory settings by default,
    and its paper: auto-line-feed (no, switch 2-9), character-set (usa,
    switches 2-3 to 2-5, or any of the twelve ESC R sets), form-length in
    inches (11, switch 2-1; 12 with it off), skip-perforation (no, switch
    1-9), slashed-zero (no, switch 2-6 off), near-letter-quality (no,
    switch 1-10: power on in NLQ), paper-width in inches (8.5: a Letter cut
    sheet, or 9.5 for stationery with tear-off strips), top-offset in
    inches (19/36), stationery (sheet: no tear-off strips; fanfold and the
    listing papers with the PF-50 pin feed unit), font (m1109-draft,
    Brother's characters reconstructed from printed output) and nlq-font
    (m1109-nlq, its near letter quality characters, likewise). The line is
    centred across the paper.
    """

    def __init__(
        self,
        name: str,
        *,
        auto_line_feed: bool = False,
        character_set: str = "usa",
        form_length: str = "11",
        skip_perforation: bool = False,
        slashed_zero: bool = False,
        near_letter_quality: bool = False,
        paper_width: str | None = None,
        top_offset: str = "19/36",
        stationery: str = "sheet",
        font: str = "m1109-draft",
        nlq_font: str = "m1109-nlq",
        **kwargs,
    ) -> None:
        super().__init__(name=name, **kwargs)
        self._mechanism = EscpMechanism(
            font=options.nine_row_font(font),
            nlq_font=options.nlq_font(nlq_font),
            **options.paper_options(
                paper_width=paper_width,
                form_length=form_length,
                top_offset=top_offset,
                stationery=stationery,
            ),
            columns=80,
            condensed_columns=136,
            auto_line_feed=auto_line_feed,
            character_set=options.character_set_option(character_set),
            skip_perforation_lines=_SKIP_PERFORATION_LINES if skip_perforation else 0,
            slashed_zero=slashed_zero,
            near_letter_quality=near_letter_quality,
            character_sets=12,
            controls=_CONTROLS,
            default_vertical_tabs=False,
            form_length_clears_vertical_tabs=True,
            cancel_ends_one_line_enlarged=True,
            condensed_elite=True,
            graphics_modes=frozenset(range(8)),
            nlq=True,
            commands=_COMMANDS,
        )

    @property
    def mechanism(self) -> EscpMechanism:
        return self._mechanism

    def identity(self) -> ModelIdentity:
        return ModelIdentity(manufacturer="Brother", model="M-1109")

    def languages(self) -> tuple[str, ...]:
        return ("escp",)

    def create_interpreter(self) -> Interpreter:
        return EscpInterpreter(self._mechanism)
