"""The Epson FX-80 9-pin dot-matrix printer."""

from __future__ import annotations

from papyrium.core.model import Interpreter, ModelIdentity, PrinterModel
from papyrium.language.escp import EscpInterpreter, EscpMechanism
from papyrium.language.escp.options import character_set_option, nine_row_font, paper_options

__version__ = "0.0.0"

__all__ = ["EpsonFx80"]

#: Skip-over-perforation, when switched on, skips one inch: six lines at 1/6 inch.
_SKIP_PERFORATION_LINES = 6


class EpsonFx80(PrinterModel):
    """Epson FX-80: an 80-column, 9-pin dot-matrix printer speaking ESC/P.

    Options model its DIP switches, at their factory settings by default,
    and its paper: auto-line-feed (no, switch 2-4), character-set (usa,
    switches 1-6 to 1-8), skip-perforation (no, switch 2-3), condensed (no,
    switch 1-1), slashed-zero (no, switch 1-2), emphasized (no, switch
    1-5), software-select (no, switch 2-1 off: obey DC1 and DC3),
    user-defined-characters (yes, switch 1-4 off), high-codes-printable
    (no: power on as if ESC 6 were sent), form-length in inches (11),
    paper-width in inches (9.5: standard fanfold, 8.5 inches between its
    tear-off strips; 8.5 for a sheet), top-offset in inches (19/36: how
    far below the perforation the operator wound the paper before
    switching on, centring lines in listing paper's bands),
    stationery (fanfold: plain, with tear-off strips; also sheet,
    green-bar, blue-bar and music-ruled), and font (draft-9), the dot font
    standing in for Epson's character ROM. The line is centred across the
    paper.
    """

    def __init__(
        self,
        name: str,
        *,
        auto_line_feed: bool = False,
        character_set: str = "usa",
        form_length: str = "11",
        skip_perforation: bool = False,
        high_codes_printable: bool = False,
        condensed: bool = False,
        slashed_zero: bool = False,
        emphasized: bool = False,
        software_select: bool = False,
        user_defined_characters: bool = True,
        paper_width: str | None = None,
        top_offset: str = "19/36",
        stationery: str = "fanfold",
        font: str = "draft-9",
        **kwargs,
    ) -> None:
        super().__init__(name=name, **kwargs)
        self._mechanism = EscpMechanism(
            font=nine_row_font(font),
            **paper_options(
                paper_width=paper_width,
                form_length=form_length,
                top_offset=top_offset,
                stationery=stationery,
            ),
            columns=80,
            auto_line_feed=auto_line_feed,
            character_set=character_set_option(character_set),
            skip_perforation_lines=_SKIP_PERFORATION_LINES if skip_perforation else 0,
            high_codes_printable=high_codes_printable,
            condensed=condensed,
            slashed_zero=slashed_zero,
            emphasized=emphasized,
            software_select=software_select,
            user_defined_characters=user_defined_characters,
            # The FX-80 feeds down a row to underline below the descenders.
            underline_row=9,
        )

    @property
    def mechanism(self) -> EscpMechanism:
        return self._mechanism

    def identity(self) -> ModelIdentity:
        return ModelIdentity(manufacturer="Epson", model="FX-80")

    def languages(self) -> tuple[str, ...]:
        return ("escp",)

    def create_interpreter(self) -> Interpreter:
        return EscpInterpreter(self._mechanism)
