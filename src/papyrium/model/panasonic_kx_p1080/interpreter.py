"""KXP1080Interpreter: the Panasonic KX-P1080's ESC/P, as its firmware has it.

Taken from the KX-P1080U's firmware and its manuals; see
docs/panasonic-kx-p1080.md.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass

from papyrium.core.dotfont import DotFont, Glyph
from papyrium.core.page import inches
from papyrium.language.escp.generator import CharacterGenerator
from papyrium.language.escp.interpreter import (
    CONDENSED_WIDTH,
    DC2,
    DEL,
    ITALIC,
    SI,
    SLASHED_ZERO,
    ArgumentReader,
    EscpInterpreter,
    UserCharacter,
)
from papyrium.model.panasonic_kx_p1080.widths import WIDTH_TABLES

logger = logging.getLogger(__name__)

#: 15 characters per inch: Panasonic's semi-compressed pitch.
SEMI_COMPRESSED_WIDTH = inches(1) // 15

#: The print mode selector's positions: Std. Pgm., NLQ and Comp.
PRINT_MODES = ("std", "nlq", "comp")

#: Where download characters are kept, by the code they replace: apart
#: from the ROM's locations, since a download replaces the code received,
#: before the national set and the italic table are applied.
DOWNLOAD_LOCATION = 0x400

#: The most download characters the RAM holds at once.
_MOST_DOWNLOADS = 40

#: A download character's columns: nine of dots and three of space.
_DOWNLOAD_COLUMNS = 9


@dataclass(frozen=True)
class KXP1080CharacterGenerator(CharacterGenerator):
    """The KX-P1080's character generator.

    Italics are fonts of their own, the ROM's draft italics and NLQ slanted
    as the firmware slants it, so the generator leans nothing. The second
    NLQ pass prints 1/216 inch below the first, as double strike's does
    ($4850 feeds pass 2 one 1/216 inch step). A compressed cell is 14
    columns, 1/240 inch apart ($4382); every other pitch's is 12.
    """

    prints_adjacent_dots_once: bool = True
    nlq_emphasized: bool = True
    nlq_pass_offset: int = inches(1) // 216

    def cell_columns(self, pitch: int) -> int:
        return 14 if pitch == CONDENSED_WIDTH else super().cell_columns(pitch)

    def italic_offset(self, glyph: Glyph, row: int, step: int) -> int:
        return 0

    def nlq_italic_offset(self, glyph: Glyph, row: int, step: int) -> int:
        return 0


def _proportional_layout(entry: int) -> tuple[int, int]:
    """The width, in 1/120 inch columns, and the glyph's move right, in
    columns, of a width table *entry*: its high nibble says where printing
    starts, that many columns into the character with bit 3 clear, bits 0-2
    columns before it with bit 3 set ($4615)."""
    start = entry >> 4
    move = start & 0x07 if start & 0x08 else -start
    return entry & 0x0F, move


class KXP1080Interpreter(EscpInterpreter):
    """The KX-P1080's ESC/P.

    *print_mode* is the selector switch's position: "std", "nlq" or "comp".
    *seven_bit*: DIP switch 8, which clears bit 7 of everything received.
    *italic_font* and *nlq_italic_font* are the italics.
    """

    def __init__(
        self,
        mechanism,
        *,
        italic_font: DotFont,
        nlq_italic_font: DotFont,
        print_mode: str = "std",
        seven_bit: bool = False,
    ) -> None:
        self._italic_font = italic_font
        self._nlq_italic_font = nlq_italic_font
        self._print_mode = print_mode
        self._seven_bit = seven_bit
        super().__init__(mechanism)

    def _initialise(self) -> None:
        super()._initialise()
        # Panasonic's pitches beside Epson's elite and compressed: ESC w 2's
        # 15 cpi, and ESC w 3's 17 cpi, which emphasized does not mask.
        self._semi_compressed = False
        self._hard_condensed = False
        # A download replaces the ROM's character at once, with no set to select.
        self._user_set_selected = True
        self._ram_holds_rom = True
        if self._print_mode == "nlq":
            self._nlq = True
        elif self._print_mode == "comp":
            self._condensed = True
        if self._seven_bit:
            self._msb = 0

    def _escape_table(self) -> dict[str, Callable[[], ArgumentReader | None]]:
        table = super()._escape_table()
        table.update(
            {
                "w": self._esc_pitch,
                "n": lambda: self._select_nlq(elite=False),
                "o": lambda: self._select_nlq(elite=True),
                "M": lambda: self._select_draft(elite=True),
                "P": lambda: self._select_draft(elite=False),
                "E": self._esc_emphasized,
                "y": self._esc_download,
                "z": self._esc_release_download,
            }
        )
        return table

    @staticmethod
    def _flag(value: int) -> bool:
        """Arguments are taken as the code or the digit, with or without bit 7."""
        return value & 0x7F in (1, ord("1"))

    # -- The selector switch ----------------------------------------------------

    def _quality_locked(self) -> bool:
        """In the selector's NLQ position, commands cannot leave NLQ."""
        return self._print_mode == "nlq"

    def _compressed_locked(self) -> bool:
        """In the selector's Comp. position, compressed stays."""
        return self._print_mode == "comp"

    def _control(self, code: int) -> ArgumentReader:
        if code == DC2 and self._compressed_locked():
            logger.debug("ignoring DC2: the selector is at Comp.")
            return
        if code == SI:
            self._hard_condensed = False
        yield from super()._control(code)

    # -- Pitch and quality ------------------------------------------------------

    def _clear_pitch(self) -> None:
        self._elite = False
        self._semi_compressed = False
        self._hard_condensed = False
        if not self._compressed_locked():
            self._condensed = False

    def _esc_pitch(self) -> ArgumentReader:
        """ESC w n, Panasonic's pitch: 0 pica, 1 elite, 2 15 cpi, 3 17 cpi."""
        n = (yield) & 0x7F
        n = n - ord("0") if ord("0") <= n <= ord("3") else n
        if not 0 <= n <= 3:
            logger.debug("ignoring pitch %d", n)
            return
        self._clear_pitch()
        if n == 1:
            self._elite = True
        elif n == 2:
            # Semi-compressed and emphasized: whichever came last.
            self._semi_compressed = True
            self._emphasized = False
        elif n == 3:
            self._condensed = self._hard_condensed = True

    def _esc_emphasized(self) -> None:
        if self._compressed_locked():
            logger.debug("ignoring ESC E: the selector is at Comp.")
            return
        self._emphasized = True
        self._semi_compressed = False

    def _esc_master_select(self) -> ArgumentReader:
        yield from super()._esc_master_select()
        self._semi_compressed = self._hard_condensed = False
        if self._compressed_locked():
            self._condensed = True

    def _select_draft(self, *, elite: bool) -> None:
        """ESC M and ESC P: elite or pica draft, cancelling compressed,
        proportional and NLQ."""
        self._clear_pitch()
        self._elite = elite
        self._proportional = False
        if not self._quality_locked():
            self._nlq = False

    def _select_nlq(self, *, elite: bool) -> None:
        """ESC n and ESC o: NLQ in pica or elite."""
        self._clear_pitch()
        self._elite = elite
        self._nlq = True

    def _esc_nlq(self) -> ArgumentReader:
        """ESC x: NLQ or draft, keeping the pitch."""
        nlq = self._flag((yield))
        if not nlq and self._quality_locked():
            logger.debug("ignoring ESC x 0: the selector is at NLQ")
            return
        self._nlq = nlq

    def _esc_proportional(self) -> ArgumentReader:
        on = self._flag((yield))
        if self._compressed_locked():
            logger.debug("ignoring ESC p: the selector is at Comp.")
            return
        self._proportional = on

    def _column_width(self) -> int:
        if not self._nlq and not self._elite:
            if self._hard_condensed:
                return CONDENSED_WIDTH
            if self._semi_compressed:
                return SEMI_COMPRESSED_WIDTH
        return super()._column_width()

    def _is_emphasized(self) -> bool:
        return not self._hard_condensed and super()._is_emphasized()

    # -- Italics ----------------------------------------------------------------

    @staticmethod
    def _rom_character(location: int) -> str:
        """The character at a ROM location: 127, which code 255 prints after
        ESC 6, is the slashed zero."""
        if location >= DOWNLOAD_LOCATION:
            # A download is recorded as the character it replaces.
            location = (location - DOWNLOAD_LOCATION) & ~ITALIC
            return " " if location < 0x20 else EscpInterpreter._rom_character(location)
        if location & ~ITALIC == DEL:
            return SLASHED_ZERO
        return EscpInterpreter._rom_character(location)

    def _italic_glyph(self, font: DotFont, location: int) -> Glyph | None:
        character = self._rom_character(location)
        if character == "0" and self._slashed_zero:
            character = SLASHED_ZERO
        return font.glyph(character)

    def _glyph(self, location: int) -> Glyph:
        if self._glyph_source(location)[0] == "rom" and self._is_italic(location):
            glyph = self._italic_glyph(self._italic_font, location)
            if glyph is not None:
                return glyph
        return super()._glyph(location)

    def _nlq_glyph(self, location: int) -> Glyph | None:
        glyph = super()._nlq_glyph(location)
        if glyph is not None and self._is_italic(location):
            return self._italic_glyph(self._nlq_italic_font, location) or glyph
        return glyph

    # -- Proportional spacing -----------------------------------------------------

    def _width_entry(self, location: int, *, nlq: bool) -> int:
        """The width table entry of the ROM character at *location*: draft
        or NLQ, upright or italic ($43C6)."""
        name = "italic" if self._is_italic(location) else "upright"
        if nlq:
            name += "_nlq"
        return WIDTH_TABLES[name][location & 0x7F]

    def _proportional_cell(self, location: int, glyph: Glyph) -> tuple[int, int]:
        return _proportional_layout(self._width_entry(location, nlq=False))

    def _nlq_proportional_cell(self, location: int, glyph: Glyph) -> tuple[int, int] | None:
        # The width and start are in 1/120 inch, two of NLQ's columns
        # ($4382 and $4615 double them in NLQ).
        columns, move = _proportional_layout(self._width_entry(location, nlq=True))
        return 2 * columns, 2 * move

    # -- Download characters ---------------------------------------------------------

    def _esc_download(self) -> ArgumentReader:
        """ESC y c d1...d9 ($3AC8): the character for code c from nine
        columns of eight dots, bit 7 the top pin, a dot following one in its
        row not stored. A code up to 31 or 127, or a forty-first download,
        ends the command at the code, leaving the nine bytes to print."""
        code = yield
        location = DOWNLOAD_LOCATION + code
        if code <= 0x1F or code == DEL:
            logger.debug("ignoring a download at code %d", code)
            return
        downloads = sum(1 for held in self._ram if held >= DOWNLOAD_LOCATION)
        if location not in self._ram and downloads >= _MOST_DOWNLOADS:
            logger.warning("ignoring a download at code %d: %d are held", code, downloads)
            return
        columns = []
        for _ in range(_DOWNLOAD_COLUMNS):
            columns.append((yield))
        character = self._draft_user_character(0x80, columns)
        self._ram[location] = UserCharacter(character.glyph, first_column=0, last_column=11)

    def _esc_release_download(self) -> ArgumentReader:
        """ESC z c ($3B3E): the ROM's character for code c again."""
        code = yield
        self._ram.pop(DOWNLOAD_LOCATION + code, None)

    def _character(self, byte: int) -> None:
        """A download replaces the code as received, before the national
        set; under ESC 4 the code with bit 7 set ($2656)."""
        location = DOWNLOAD_LOCATION + (byte | 0x80 if self._italic else byte)
        if location in self._ram:
            self._print_location(location)
        else:
            super()._character(byte)

    def _character_layout(self, location: int) -> tuple[int, int, int, tuple]:
        """A download keeps the fixed pitch in proportional spacing ($29D8
        clears the proportional bit)."""
        if location >= DOWNLOAD_LOCATION and self._is_proportional():
            pitch = self._column_width()
            width = pitch * (2 if self._is_double_width() else 1)
            return width, width // self._cell_columns(pitch), 0, self._glyph_source(location)
        return super()._character_layout(location)
