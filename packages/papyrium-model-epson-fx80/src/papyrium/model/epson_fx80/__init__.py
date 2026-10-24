"""The Epson FX-80 9-pin dot-matrix printer."""

from __future__ import annotations

from fractions import Fraction

from papyrium.core.dotfont import DotFont
from papyrium.core.model import Interpreter, PrinterModel
from papyrium.core.page import inches
from papyrium.exception import ConfigurationError
from papyrium.extension import create_extension, namespace_for
from papyrium.language.escp import EscpInterpreter, EscpMechanism, parse_character_set

__version__ = "0.0.0"

__all__ = ["EpsonFx80"]

#: Skip-over-perforation, when switched on, skips one inch: six lines at 1/6 inch.
_SKIP_PERFORATION_LINES = 6


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
    switch 1-1), emphasized (no, switch 1-5), software-select (no, switch
    2-1 off: obey DC1 and DC3), user-defined-characters (yes, switch 1-4
    off), high-codes-printable (no: power on as if ESC 6 were sent),
    form-length in inches (11), paper-width in inches (8.5), and font
    (draft-9), the dot font standing in for Epson's character ROM.
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
        emphasized: bool = False,
        software_select: bool = False,
        user_defined_characters: bool = True,
        paper_width: str = "8.5",
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
        self._mechanism = EscpMechanism(
            font=dot_font,
            paper_width=_inches_option("paper-width", str(paper_width)),
            sheet_length=_inches_option("form-length", str(form_length)),
            left_offset=inches(Fraction(1, 4)),
            columns=80,
            auto_line_feed=auto_line_feed,
            character_set=charset,
            skip_perforation_lines=_SKIP_PERFORATION_LINES if skip_perforation else 0,
            high_codes_printable=high_codes_printable,
            condensed=condensed,
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
