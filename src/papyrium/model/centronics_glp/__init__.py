"""The Centronics GLP (Model 3101) and the printers made from it."""

from __future__ import annotations

from fractions import Fraction

from papyrium.core.model import Interpreter, ModelIdentity, PrinterModel
from papyrium.core.page import inches
from papyrium.exception import ConfigurationError
from papyrium.font.glp import UPPER_HALF
from papyrium.language.escp import CharacterSet, EscpInterpreter, EscpMechanism, options
from papyrium.language.escp.generator import CharacterGenerator
from papyrium.model.centronics_glp import demo

__all__ = ["BrotherM1009", "CentronicsGlp", "SchneiderNlq401"]

#: Skip-over-perforation, when switched on, skips one inch: six lines at 1/6 inch.
_SKIP_PERFORATION_LINES = 6

#: The escape commands the firmware obeys; the rest of ESC - to ESC Z,
#: ESC @ among them, it ignores.
_COMMANDS = frozenset("-0123 6789<=ACDEFGHIJKLNOSTUWYZx".replace(" ", ""))

#: Codes the firmware ignores: below HT ($0294), so BS too, and DEL ($0134).
_IGNORED_CONTROLS = frozenset({*range(0x09), 0x7F})

#: The commands without near letter quality.
_DRAFT_COMMANDS = _COMMANDS - {"I", "x"}

#: Character set 1 is ASCII; set 2 puts the German characters § Ä Ö Ü ä ö ü ß
#: in place of @ [ \ ] { | } ~, as Epson's German set does.
_CHARACTER_SETS = {"1": CharacterSet.USA, "2": CharacterSet.GERMANY}

#: Near letter quality columns are 1/480 inch apart, 48 to the pica cell,
#: of which a character's 39 print; enlarged, each pair prints as one.
#: Emphasized repeats a dot one slot, 1/120 inch, right ($1033); scripts
#: print their even and odd rows on two passes 1/216 inch apart ($0934).
_GENERATOR = CharacterGenerator(
    nlq_cell_columns=48,
    nlq_double_width_pairs=True,
    emphasized_offset=inches(1) // 120,
    script_rows_by_pass=True,
)


class CentronicsGlp(PrinterModel):
    """Centronics GLP (Model 3101): the first Great Little Printer, of 1984.

    Made with Brother, also sold as the Brother M-1009 and, with
    Schneider's near letter quality, as the Schneider NLQ401. Its
    behaviour is the NLQ401's firmware's, the one GLP firmware read: an
    Epson-like command set of its own, with the Amstrad CPC's graphics at
    codes 128-255, which ESC = reaches from seven bits.

    Options model its DIP switches, at their delivered settings by default,
    and its paper: auto-line-feed (no, switch 2-7), character-set (2,
    switch 2-3: set 1 is ASCII, set 2 has German characters in place of
    @ [ \\ ] { | } ~), form-length in inches (11, switch 2-1; 12 with it
    off), skip-perforation (no, switch 2-5), buffer-full-line-feed (yes,
    switch 2-6: a full line wraps to the next; off, it prints over itself), near-letter-quality (no,
    switch 2-4: power on in NLQ), seven-bit (no, switch 1-7: each byte's bit
    7 is dropped), paper-width in inches (8.5: a Letter cut sheet, or 9.5
    with tear-off strips), top-offset in inches (19/36), stationery (sheet;
    or fanfold and the listing papers with the tractor feed), font
    (glp-draft), nlq-font (glp-nlq) and graphics-font (glp-graphics). The
    line is centred across the paper.
    """

    _MANUFACTURER = "Centronics"
    _MODEL_NAME = "GLP"

    def __init__(
        self,
        name: str,
        *,
        auto_line_feed: bool = False,
        character_set: str = "2",
        form_length: str = "11",
        skip_perforation: bool = False,
        buffer_full_line_feed: bool = True,
        near_letter_quality: bool = False,
        seven_bit: bool = False,
        paper_width: str | None = None,
        top_offset: str = "19/36",
        stationery: str = "sheet",
        font: str = "glp-draft",
        nlq_font: str = "glp-nlq",
        graphics_font: str = "glp-graphics",
        **kwargs,
    ) -> None:
        super().__init__(name=name, **kwargs)
        self._mechanism = _glp_mechanism(
            auto_line_feed=auto_line_feed,
            character_set=character_set,
            form_length=form_length,
            skip_perforation=skip_perforation,
            buffer_full_line_feed=buffer_full_line_feed,
            near_letter_quality=near_letter_quality,
            seven_bit=seven_bit,
            line_spacing="1/6",
            paper_width=paper_width,
            top_offset=top_offset,
            stationery=stationery,
            font=font,
            nlq_font=nlq_font,
            graphics_font=graphics_font,
        )

    @property
    def mechanism(self) -> EscpMechanism:
        return self._mechanism

    def identity(self) -> ModelIdentity:
        return ModelIdentity(manufacturer=self._MANUFACTURER, model=self._MODEL_NAME)

    def languages(self) -> tuple[str, ...]:
        return ("escp",)

    def demo(self) -> bytes:
        return demo.demo(self.identity().display_name, nlq=self._mechanism.nlq)

    def create_interpreter(self) -> Interpreter:
        return EscpInterpreter(self._mechanism)


class SchneiderNlq401(CentronicsGlp):
    """Schneider NLQ401: the Centronics GLP with Schneider's NLQ, for the CPC.

    Sold with the Schneider CPC computers, whose printer port sends seven
    bits: the printer keeps seven bits of every byte, and prints codes
    128-255, the CPC's graphics, after ESC =. It powers on in near letter
    quality (switch 4, on as delivered), and switch 2 chooses 1/8 inch
    line spacing at power on.

    Options as the GLP's, less seven-bit, which is always on, with
    near-letter-quality (yes, switch 4), line-spacing (1/6; 1/8 with switch
    2 on) and paper-width (8.3, A4 as the manual gives it).
    """

    _MANUFACTURER = "Schneider"
    _MODEL_NAME = "NLQ 401"

    def __init__(
        self,
        name: str,
        *,
        auto_line_feed: bool = False,
        character_set: str = "2",
        form_length: str = "11",
        skip_perforation: bool = False,
        buffer_full_line_feed: bool = True,
        near_letter_quality: bool = True,
        line_spacing: str = "1/6",
        paper_width: str | None = "8.3",
        top_offset: str = "19/36",
        stationery: str = "sheet",
        font: str = "glp-draft",
        nlq_font: str = "glp-nlq",
        graphics_font: str = "glp-graphics",
        **kwargs,
    ) -> None:
        super(CentronicsGlp, self).__init__(name=name, **kwargs)
        self._mechanism = _glp_mechanism(
            auto_line_feed=auto_line_feed,
            character_set=character_set,
            form_length=form_length,
            skip_perforation=skip_perforation,
            buffer_full_line_feed=buffer_full_line_feed,
            near_letter_quality=near_letter_quality,
            seven_bit=True,
            line_spacing=line_spacing,
            paper_width=paper_width,
            top_offset=top_offset,
            stationery=stationery,
            font=font,
            nlq_font=nlq_font,
            graphics_font=graphics_font,
        )


class BrotherM1009(CentronicsGlp):
    """Brother M-1009: the Centronics GLP under Brother's badge, without NLQ.

    Brother's firmware for the GLP has no NLQ; otherwise it is modelled as
    the GLP's, an assumption until its own firmware or manual is read.
    Options as the GLP's, less near-letter-quality and nlq-font.
    """

    _MANUFACTURER = "Brother"
    _MODEL_NAME = "M-1009"

    def __init__(
        self,
        name: str,
        *,
        auto_line_feed: bool = False,
        character_set: str = "2",
        form_length: str = "11",
        skip_perforation: bool = False,
        buffer_full_line_feed: bool = True,
        seven_bit: bool = False,
        paper_width: str | None = None,
        top_offset: str = "19/36",
        stationery: str = "sheet",
        font: str = "glp-draft",
        graphics_font: str = "glp-graphics",
        **kwargs,
    ) -> None:
        super(CentronicsGlp, self).__init__(name=name, **kwargs)
        self._mechanism = _glp_mechanism(
            auto_line_feed=auto_line_feed,
            character_set=character_set,
            form_length=form_length,
            skip_perforation=skip_perforation,
            buffer_full_line_feed=buffer_full_line_feed,
            near_letter_quality=False,
            seven_bit=seven_bit,
            line_spacing="1/6",
            paper_width=paper_width,
            top_offset=top_offset,
            stationery=stationery,
            font=font,
            nlq_font=None,
            graphics_font=graphics_font,
        )


def _glp_mechanism(
    *,
    auto_line_feed: bool,
    character_set: str,
    form_length: str,
    skip_perforation: bool,
    buffer_full_line_feed: bool,
    near_letter_quality: bool,
    seven_bit: bool,
    line_spacing: str,
    paper_width: str | None,
    top_offset: str,
    stationery: str,
    font: str,
    nlq_font: str | None,
    graphics_font: str,
) -> EscpMechanism:
    """The GLP's mechanism as its switches set it; *nlq_font* None for no NLQ."""
    if character_set not in _CHARACTER_SETS:
        raise ConfigurationError(f"character-set must be 1 or 2, not {character_set!r}")
    if line_spacing not in ("1/6", "1/8"):
        raise ConfigurationError(f"line-spacing must be 1/6 or 1/8, not {line_spacing!r}")
    nlq = nlq_font is not None
    return EscpMechanism(
        font=options.nine_row_font(font),
        block_graphics_font=options.dot_font(graphics_font),
        nlq_fonts=(options.nlq_font(nlq_font, columns=39),) if nlq else (),
        generator=_GENERATOR,
        **options.paper_options(
            paper_width=paper_width,
            form_length=form_length,
            top_offset=top_offset,
            stationery=stationery,
        ),
        columns=80,
        condensed_columns=132,
        auto_line_feed=auto_line_feed,
        character_set=_CHARACTER_SETS[character_set],
        skip_perforation_lines=_SKIP_PERFORATION_LINES if skip_perforation else 0,
        wrap_feeds_line=buffer_full_line_feed,
        near_letter_quality=near_letter_quality and nlq,
        nlq=nlq,
        power_on_line_spacing=inches(Fraction(line_spacing)),
        default_vertical_tabs=False,
        cancel_ends_one_line_enlarged=True,
        carriage_return_ends_one_line_enlarged=True,
        user_defined_characters=False,
        high_codes_printable=True,
        high_characters=UPPER_HALF,
        seven_bit_input=seven_bit,
        high_shift_until_nul=True,
        esc_6_and_7_select=(CharacterSet.GERMANY, CharacterSet.USA),
        esc_i_selects_nlq=nlq,
        esc_a_stores_for_esc_2=True,
        esc_3_ignores_zero=True,
        flags_by_lowest_bit=True,
        underline_trims_spaces=True,
        underline_skips_high_characters=True,
        nlq_masks_scripts=True,
        horizontal_tab_stops=28,
        graphics_wrap_whole=True,
        graphics_count_high_bits=3,
        ignored_controls=_IGNORED_CONTROLS,
        tab_stops_skip_out_of_order=True,
        tab_inserts_spaces=True,
        commands=_COMMANDS if nlq else _DRAFT_COMMANDS,
    )
