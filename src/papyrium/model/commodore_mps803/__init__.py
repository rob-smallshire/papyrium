"""The Commodore MPS-803 dot-matrix printer."""

from __future__ import annotations

from fractions import Fraction

from papyrium.core.model import Interpreter, ModelIdentity, PrinterModel
from papyrium.core.page import inches
from papyrium.exception import ConfigurationError
from papyrium.language.cbm import CbmInterpreter, CbmMechanism
from papyrium.language.escp import options
from papyrium.model.commodore_mps803 import demo

__all__ = ["CommodoreMps803"]

#: The line: 480 dots 1/60 inch apart.
_LINE_LENGTH = inches(8)


class CommodoreMps803(PrinterModel):
    """Commodore MPS-803: a 7-wire dot-matrix printer for Commodore's serial bus.

    Made by Brother on the mechanism of the first Great Little Printer.
    It prints PETSCII in its graphic set (upper case and graphics) or its
    business set (lower and upper case), 80 characters of six dots to a
    480-dot line, with double width, reverse, quote mode, bit images and
    positioning. Its behaviour follows its firmware, read from its uPD78C11's
    ROM (docs/commodore-mps-803-firmware.md).

    Options: secondary-address (0: the graphic set; 7: the business set;
    the serial bus's addressing does not reach Papyrium, so the job's set
    is chosen here), line-spacing (1/6; 1/8 with the rear switch),
    form-length in inches (11), paper-width in inches (9.5, fanfold with
    tear-off strips), top-offset in inches (1/3), stationery (fanfold;
    sheet, and the listing papers) and font (mps803). The line is centred
    across the paper.
    """

    def __init__(
        self,
        name: str,
        *,
        secondary_address: str = "0",
        line_spacing: str = "1/6",
        form_length: str = "11",
        paper_width: str | None = None,
        top_offset: str = "1/3",
        stationery: str = "fanfold",
        font: str = "mps803",
        **kwargs,
    ) -> None:
        super().__init__(name=name, **kwargs)
        if secondary_address not in ("0", "7"):
            raise ConfigurationError(f"secondary-address must be 0 or 7, not {secondary_address!r}")
        if line_spacing not in ("1/6", "1/8"):
            raise ConfigurationError(f"line-spacing must be 1/6 or 1/8, not {line_spacing!r}")
        paper = options.paper_options(
            paper_width=paper_width,
            form_length=form_length,
            top_offset=top_offset,
            stationery=stationery,
        )
        self._mechanism = CbmMechanism(
            font=options.dot_font(font),
            business_set=secondary_address == "7",
            line_feed_steps=int(216 * Fraction(line_spacing)),
            paper_width=paper["paper_width"],
            sheet_length=paper["sheet_length"],
            left_offset=max(0, (paper["paper_width"] - _LINE_LENGTH) // 2),
            top_offset=paper["top_offset"],
            stationery=paper["stationery"],
        )

    @property
    def mechanism(self) -> CbmMechanism:
        return self._mechanism

    def identity(self) -> ModelIdentity:
        return ModelIdentity(manufacturer="Commodore", model="MPS-803")

    def languages(self) -> tuple[str, ...]:
        return ("cbm",)

    def demo(self) -> bytes:
        return demo.demo()

    def create_interpreter(self) -> Interpreter:
        return CbmInterpreter(self._mechanism)
