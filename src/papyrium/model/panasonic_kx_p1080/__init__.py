"""The Panasonic KX-P1080 and KX-P1080U 9-pin dot-matrix printers."""

from __future__ import annotations

from papyrium.core.model import Interpreter, ModelIdentity, PrinterModel
from papyrium.exception import ConfigurationError
from papyrium.language.escp import CharacterSet, EscpMechanism, options
from papyrium.language.escp.mechanism import FX_COMMANDS, FX_CONTROLS
from papyrium.model.panasonic_kx_p1080 import demo
from papyrium.model.panasonic_kx_p1080.interpreter import (
    PRINT_MODES,
    KXP1080CharacterGenerator,
    KXP1080Interpreter,
)

__all__ = ["PanasonicKXP1080", "PanasonicKXP1080U"]

#: Skip-over-perforation, switch 4, skips one inch: six lines at 1/6 inch.
_SKIP_PERFORATION_LINES = 6

#: The KX-P1080's escape commands, those of its manual and of its
#: firmware's dispatch table: the FX-80's less ESC &, %, :, j, I, i, b and
#: /, plus justification (ESC a), regular tabs (ESC e), skipping (ESC f),
#: NLQ (ESC x, n, o), Panasonic's pitch (ESC w) and download characters
#: (ESC y, z).
_COMMANDS = (FX_COMMANDS - set("&%:jIib/")) | set("aefnowxyz")

#: ESC R's eleven sets, the FX-80's nine with Norway and Denmark II, in
#: the order of the firmware's table at 0x286E.
CHARACTER_SETS = tuple(CharacterSet(n) for n in range(11))

#: The FX-80's control codes less BEL, which the KX-P1080 lacks.
_CONTROLS = FX_CONTROLS - {7}


class PanasonicKXP1080(PrinterModel):
    """Panasonic KX-P1080: an 80-column, 9-pin dot-matrix printer speaking ESC/P.

    The Epson FX-80's command set with Epson's NLQ commands and Panasonic's
    own: ESC w selects 10, 12, 15 or 17 characters to the inch, ESC n and
    ESC o NLQ in pica and elite, and ESC y and ESC z download characters.
    Proportional spacing in draft and NLQ, by the widths in its firmware.

    Options model its DIP switches, its print mode selector and its paper:
    print-mode (std; nlq or comp, the selector's NLQ and Comp. positions),
    form-length in inches (11, switch 2; 12 with it on), auto-line-feed
    (no, switch 3), skip-perforation (no, switch 4), character-set (usa,
    switches 5-7, or any of the eleven ESC R sets), data-bits (8, switch 8;
    7 clears bit 7 of everything received), paper-width in inches (9.5 for
    fanfold, 8.5 for a sheet), top-offset in inches (19/36), stationery
    (fanfold, or sheet and the listing papers), and the fonts: font
    (kx-p1080-draft), italic-font (kx-p1080-draft-italic), nlq-font
    (kx-p1080-nlq) and nlq-italic-font (kx-p1080-nlq-italic), all from the
    KX-P1080U's firmware. The line is centred across the paper.
    """

    model_name = "KX-P1080"
    default_character_set = "usa"

    def __init__(
        self,
        name: str,
        *,
        print_mode: str = "std",
        form_length: str = "11",
        auto_line_feed: bool = False,
        skip_perforation: bool = False,
        character_set: str | None = None,
        data_bits: str = "8",
        paper_width: str | None = None,
        top_offset: str = "19/36",
        stationery: str = "fanfold",
        font: str = "kx-p1080-draft",
        italic_font: str = "kx-p1080-draft-italic",
        nlq_font: str = "kx-p1080-nlq",
        nlq_italic_font: str = "kx-p1080-nlq-italic",
        **kwargs,
    ) -> None:
        super().__init__(name=name, **kwargs)
        if print_mode not in PRINT_MODES:
            raise ConfigurationError(
                f"print-mode must be one of {', '.join(PRINT_MODES)}, not {print_mode!r}"
            )
        if str(data_bits) not in ("7", "8"):
            raise ConfigurationError(f"data-bits must be 7 or 8, not {data_bits!r}")
        self._print_mode = print_mode
        self._seven_bit = str(data_bits) == "7"
        self._italic_font = options.nine_row_font(italic_font)
        self._nlq_italic_font = options.nlq_font(nlq_italic_font)
        self._mechanism = EscpMechanism(
            font=options.nine_row_font(font),
            nlq_fonts=(options.nlq_font(nlq_font),),
            **options.paper_options(
                paper_width=paper_width,
                form_length=form_length,
                top_offset=top_offset,
                stationery=stationery,
            ),
            columns=80,
            condensed_columns=132,
            auto_line_feed=auto_line_feed,
            character_set=options.character_set_option(
                character_set or self.default_character_set, CHARACTER_SETS
            ),
            character_sets=CHARACTER_SETS,
            skip_perforation_lines=_SKIP_PERFORATION_LINES if skip_perforation else 0,
            near_letter_quality=print_mode == "nlq",
            condensed=print_mode == "comp",
            default_vertical_tabs=False,
            form_length_clears_vertical_tabs=True,
            nlq=True,
            nlq_elite=True,
            # The KX-P1080 underlines with the ninth pin.
            underline_row=8,
            generator=KXP1080CharacterGenerator(),
            controls=frozenset(_CONTROLS),
            commands=frozenset(_COMMANDS),
        )

    @property
    def mechanism(self) -> EscpMechanism:
        return self._mechanism

    def identity(self) -> ModelIdentity:
        return ModelIdentity(manufacturer="Panasonic", model=self.model_name)

    def languages(self) -> tuple[str, ...]:
        return ("escp",)

    def demo(self) -> bytes:
        return demo.demo()

    def create_interpreter(self) -> Interpreter:
        return KXP1080Interpreter(
            self._mechanism,
            italic_font=self._italic_font,
            nlq_italic_font=self._nlq_italic_font,
            print_mode=self._print_mode,
            seven_bit=self._seven_bit,
        )


class PanasonicKXP1080U(PanasonicKXP1080):
    """Panasonic KX-P1080U: the KX-P1080 for the UK, its firmware Papyrium's source.

    As the KX-P1080, but shipped with the England character set, switches
    5 and 6 off: its character-set defaults to uk.
    """

    model_name = "KX-P1080U"
    default_character_set = "uk"
