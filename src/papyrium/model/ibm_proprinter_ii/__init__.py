"""The IBM Proprinter II 9-wire dot-matrix printer."""

from __future__ import annotations

from papyrium.core.dotfont import DotFont
from papyrium.core.model import Interpreter, ModelIdentity, PrinterModel
from papyrium.exception import ConfigurationError
from papyrium.extension import create_extension, namespace_for
from papyrium.language.escp import options
from papyrium.language.proprinter import ProprinterInterpreter, ProprinterMechanism
from papyrium.model.ibm_proprinter_ii import demo

__all__ = ["IBMProprinterII"]


def _font(name: str) -> DotFont:
    font = create_extension("font", namespace_for("font"), name)
    if not isinstance(font, DotFont):
        raise ConfigurationError(f"{name!r} is not a dot font")
    return font


def _nine_row_font_of_columns(name: str, columns: int) -> DotFont:
    font = options.nine_row_font(name)
    if font.columns > columns:
        raise ConfigurationError(f"font {name!r} is wider than {columns} columns")
    return font


class IBMProprinterII(PrinterModel):
    """IBM Proprinter II: an 80-column, 9-wire dot-matrix printer speaking
    the Proprinter's language.

    Draft, Fastfont at 12 cpi, NLQ made from the draft characters, and
    NLQ II; character sets 1 and 2 of the IBM PC characters; block
    graphics twelve dots high; draft download characters.

    No Proprinter II ROM is at hand, so its characters are stand-ins: the
    Star LC-10's draft (lc10-draft), elite draft for Fastfont
    (lc10-draft-elite) and Courier for NLQ II (lc10-nlq-courier), and the
    LC-10's block graphics. NLQ is the Proprinter's own, made from
    whichever draft characters are given.

    Options model its switches, at their U.S. factory settings by default,
    and its paper: ignore-top-form-feed (no, switch 1: ignore a form feed
    at the top of a blank form), auto-line-feed (no, switch 3),
    form-length in inches (11, switch 4; 12 with it on), character-set-2
    (no, switch 5: character set 1, with codes 128-159 as controls),
    auto-carriage-return (no, switch 6: a line feed also returns the
    head), paper-width in inches (9.5 for fanfold, 8.5 for a sheet),
    top-offset in inches (19/36), stationery (fanfold, or sheet and the
    listing papers), and font, fastfont and nlq-ii-font, the characters of
    each face. The line is centred across the paper.
    """

    def __init__(
        self,
        name: str,
        *,
        ignore_top_form_feed: bool = False,
        auto_line_feed: bool = False,
        form_length: str = "11",
        character_set_2: bool = False,
        auto_carriage_return: bool = False,
        paper_width: str | None = None,
        top_offset: str = "19/36",
        stationery: str = "fanfold",
        font: str = "lc10-draft",
        fastfont: str = "lc10-draft-elite",
        nlq_ii_font: str = "lc10-nlq-courier",
        **kwargs,
    ) -> None:
        super().__init__(name=name, **kwargs)
        self._mechanism = ProprinterMechanism(
            font=_nine_row_font_of_columns(font, 12),
            fastfont=_nine_row_font_of_columns(fastfont, 11),
            nlq_ii_font=options.nlq_font(nlq_ii_font),
            block_graphics_font=_font("lc10-block-graphics"),
            **options.paper_options(
                paper_width=paper_width,
                form_length=form_length,
                top_offset=top_offset,
                stationery=stationery,
            ),
            form_feed_at_top_ignored=ignore_top_form_feed,
            auto_line_feed=auto_line_feed,
            ibm_set=2 if character_set_2 else 1,
            line_feed_returns=auto_carriage_return,
        )

    @property
    def mechanism(self) -> ProprinterMechanism:
        return self._mechanism

    def identity(self) -> ModelIdentity:
        return ModelIdentity(manufacturer="IBM", model="Proprinter II")

    def languages(self) -> tuple[str, ...]:
        return ("proprinter",)

    def demo(self) -> bytes:
        return demo.demo()

    def create_interpreter(self) -> Interpreter:
        return ProprinterInterpreter(self._mechanism)
