"""The Star LC-10 9-pin dot-matrix printer."""

from __future__ import annotations

from papyrium.core.dotfont import DotFont
from papyrium.core.model import Interpreter, ModelIdentity, PrinterModel
from papyrium.exception import ConfigurationError
from papyrium.extension import create_extension, namespace_for
from papyrium.language.escp import EscpInterpreter, EscpMechanism, options
from papyrium.language.escp.charsets import LC10_NATIONAL_DIFFERENCES, LX800_CHARACTER_SETS
from papyrium.model.star_lc10 import demo
from papyrium.model.star_lc10.generator import LC10CharacterGenerator

__version__ = "0.1.0"

__all__ = ["StarLC10", "StarLC10Colour"]

#: The commands after ESC in the LC-10's Standard mode, as its firmware's
#: command table lists them (docs/star-lc10-firmware.md).
_COMMANDS = frozenset(
    "\x01\x02\n\x0c\x0e\x0f\x19 !#$%&*+-/0123456789:<=>?@ABCDEFGHJKLMNOPQRSTUWXYZ[\\^_"
    "abcefhijklprtwx~"
)

#: The NLQ typefaces in ESC k order: Courier, Sanserif, Orator with small
#: capitals and Orator with lower case.
_NLQ_TYPEFACES = ("courier", "sanserif", "orator-small-capitals", "orator")


def _font(name: str) -> DotFont:
    font = create_extension("font", namespace_for("font"), name)
    if not isinstance(font, DotFont):
        raise ConfigurationError(f"{name!r} is not a dot font")
    return font


class StarLC10(PrinterModel):
    """Star LC-10: an 80-column, 9-pin dot-matrix printer speaking ESC/P.

    Standard mode, in which the LC-10 follows the Epson LX-800, with the
    LC-10's own characters and character generator, from its firmware:
    draft and four NLQ typefaces (Courier, Sanserif, and Orator with small
    capitals or with lower case), each in pica and elite, and the IBM block
    graphics, twelve dots high so that boxes join. Its black ribbon ignores
    ESC r, and of the embedded commands it obeys only the sheet feeder's.

    Options model its DIP switches, at their factory settings by default,
    and its paper: form-length in inches (11, switch 1-1; 12 with it off),
    auto-carriage-return (yes, switch 1-2: a line feed also returns the
    head to the left margin), graphics-table (no, switch 1-7 off: codes
    128-254 from IBM character set #2 rather than italics),
    auto-line-feed (no, switch 1-8 off), download-characters (no, switch
    2-1 off: the RAM holds download characters rather than a 4K buffer),
    character-set (usa, switches 2-2 to 2-4, or any of the thirteen ESC R
    sets), paper-width in inches (9.5 for fanfold, 8.5 for a sheet),
    top-offset in inches (19/36), stationery (fanfold, or sheet and the
    listing papers), and font and elite-font, the pica and elite draft
    characters (lc10-draft and lc10-draft-elite). The line is centred
    across the paper.
    """

    def __init__(
        self,
        name: str,
        *,
        form_length: str = "11",
        graphics_table: bool = False,
        auto_line_feed: bool = False,
        auto_carriage_return: bool = True,
        download_characters: bool = False,
        character_set: str = "usa",
        paper_width: str | None = None,
        top_offset: str = "19/36",
        stationery: str = "fanfold",
        font: str = "lc10-draft",
        elite_font: str = "lc10-draft-elite",
        **kwargs,
    ) -> None:
        super().__init__(name=name, **kwargs)
        self._mechanism = EscpMechanism(
            colour_ribbon=self._COLOUR_RIBBON,
            embedded_commands=self._EMBEDDED_COMMANDS,
            font=options.nine_row_font(font),
            elite_font=options.nine_row_font(elite_font),
            block_graphics_font=_font("lc10-block-graphics"),
            generator=LC10CharacterGenerator(),
            **options.paper_options(
                paper_width=paper_width,
                form_length=form_length,
                top_offset=top_offset,
                stationery=stationery,
            ),
            columns=80,
            condensed_columns=137,
            auto_line_feed=auto_line_feed,
            line_feed_returns=auto_carriage_return,
            character_set=options.character_set_option(character_set, LX800_CHARACTER_SETS),
            character_sets=LX800_CHARACTER_SETS,
            national_differences=LC10_NATIONAL_DIFFERENCES,
            graphics_table=graphics_table,
            default_vertical_tabs=False,
            condensed_elite=True,
            nlq=True,
            nlq_fonts=tuple(options.nlq_font(f"lc10-nlq-{t}") for t in _NLQ_TYPEFACES),
            nlq_elite=True,
            nlq_elite_fonts=tuple(_font(f"lc10-nlq-{t}-elite") for t in _NLQ_TYPEFACES),
            master_select_italic_underline=True,
            skip_moves_to_column=True,
            proportional_elite=True,
            user_defined_characters=download_characters,
            user_set_arguments=1,
            user_characters_by_quality=True,
            proportional_emphasized=False,
            commands=_COMMANDS,
        )

    #: The LC-10 has a black ribbon; the LC-10 Colour a four-colour one.
    _COLOUR_RIBBON = False
    #: The embedded commands, ((X))n sent as text, it obeys.
    _EMBEDDED_COMMANDS = frozenset("04RT")
    _MODEL_NAME = "LC-10"

    @property
    def mechanism(self) -> EscpMechanism:
        return self._mechanism

    def identity(self) -> ModelIdentity:
        return ModelIdentity(manufacturer="Star", model=self._MODEL_NAME)

    def languages(self) -> tuple[str, ...]:
        return ("escp",)

    def demo(self) -> bytes:
        return demo.demo()

    def create_interpreter(self) -> Interpreter:
        return EscpInterpreter(self._mechanism)


class StarLC10Colour(StarLC10):
    """Star LC-10 Colour: the LC-10 with a four-colour ribbon.

    ESC r prints in seven colours, the ribbon's black, cyan, magenta and
    yellow bands and violet, orange and green struck through two of them,
    and the embedded commands set the type style, size, colour, bold and
    italic from text: ((F))n, ((S))n, ((C))n, ((B))n and ((I))n. The
    options are the LC-10's.
    """

    _COLOUR_RIBBON = True
    _EMBEDDED_COMMANDS = frozenset("FSCBI04RT")
    _MODEL_NAME = "LC-10 Colour"

    def demo(self) -> bytes:
        return demo.colour_demo()
