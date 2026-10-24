"""The Epson FX-80 9-pin dot-matrix printer."""

from __future__ import annotations

from fractions import Fraction

from papyrium.core.dotfont import DotFont
from papyrium.core.model import Interpreter, PrinterModel
from papyrium.core.page import inches
from papyrium.core.stationery import STATIONERY
from papyrium.exception import ConfigurationError
from papyrium.extension import create_extension, namespace_for
from papyrium.language.escp import EscpInterpreter, EscpMechanism, parse_character_set

__version__ = "0.0.0"

__all__ = ["EpsonFx80"]

#: Skip-over-perforation, when switched on, skips one inch: six lines at 1/6 inch.
_SKIP_PERFORATION_LINES = 6

#: The head's reach: 80 pica columns.
_LINE_LENGTH = inches(8)


def _inches_option(option: str, value: str) -> int:
    try:
        return inches(Fraction(value))
    except (ValueError, ZeroDivisionError) as error:
        raise ConfigurationError(f"{option} must be a length in inches, not {value!r}") from error


class EpsonFx80(PrinterModel):
    """Epson FX-80: an 80-column, 9-pin dot-matrix printer speaking ESC/P.

    Options model its DIP switches, at their factory settings by default,
    and its paper: auto-line-feed (no, switch 2-4), character-set (usa,
    switches 1-6 to 1-8), skip-perforation (no, switch 2-3), condensed (no,
    switch 1-1), slashed-zero (no, switch 1-2), emphasized (no, switch
    1-5), software-select (no, switch 2-1 off: obey DC1 and DC3),
    user-defined-characters (yes, switch 1-4 off), high-codes-printable (no: power on as if ESC 6 were sent),
    form-length in inches (11), paper-width in inches (9.5: standard
    fanfold, 8.5 inches between its tear-off strips), top-offset in inches
    (0: how far below the perforation the operator wound the paper before
    switching on), stationery (fanfold: plain, with tear-off strips; also
    sheet, green-bar, blue-bar and music-ruled), and font (draft-9), the dot font standing in for
    Epson's character ROM. The line is centred across the paper.
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
        paper_width: str = "9.5",
        top_offset: str = "0",
        stationery: str = "fanfold",
        font: str = "draft-9",
        **kwargs,
    ) -> None:
        super().__init__(name=name, **kwargs)
        try:
            charset = parse_character_set(character_set)
        except (KeyError, ValueError) as error:
            raise ConfigurationError(f"unknown character set {character_set!r}") from error
        dot_font = create_extension("font", namespace_for("font"), font)
        if not isinstance(dot_font, DotFont) or dot_font.rows != 9:
            raise ConfigurationError(f"font {font!r} is not a 9-row dot font")
        width = _inches_option("paper-width", str(paper_width))
        length = _inches_option("form-length", str(form_length))
        top = _inches_option("top-offset", str(top_offset))
        if not 0 <= top < length:
            raise ConfigurationError(
                f"top-offset must be at least 0 and less than the form length, not {top_offset!r}"
            )
        if stationery not in STATIONERY:
            raise ConfigurationError(
                f"unknown stationery {stationery!r}; choose from {', '.join(STATIONERY)}"
            )
        self._mechanism = EscpMechanism(
            font=dot_font,
            paper_width=width,
            sheet_length=length,
            left_offset=max(0, (width - _LINE_LENGTH) // 2),
            top_offset=top,
            stationery=STATIONERY[stationery],
            columns=80,
            auto_line_feed=auto_line_feed,
            character_set=charset,
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

    def create_interpreter(self) -> Interpreter:
        return EscpInterpreter(self._mechanism)
