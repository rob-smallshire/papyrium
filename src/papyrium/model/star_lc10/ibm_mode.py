"""The LC-10's IBM mode: the Proprinter II's language on the LC-10.

With switch 1-6 off the LC-10 emulates an IBM Proprinter II, and per the
emulation rule this is built on the Proprinter's language as a variant.
From the Proprinter it takes its character sets 1 and 2 and the commands
whose letters mean something else there (``ESC 2``, ``4``, ``5``, ``6``,
``7``, ``:``, ``=``, ``A``, ``J``, ``P``, ``Q``, ``R``, ``\\``, ``^``). It
keeps everything else of its own (``docs/star-lc-10.md``,
``docs/star-lc10-firmware.md``):

- its typefaces and character generator, which ``ESC I`` chooses among
  in place of the Proprinter's faces, ``ESC G`` being double strike;
- the commands its manual marks for both modes, with their Standard mode
  handlers, among them NLQ (``ESC x``, ``ESC k``), master select,
  character sizes, colour and its tabs, counted as in Standard mode;
- Star's commands after FS, which give back the Standard mode commands
  whose letters the Proprinter's took.
"""

from __future__ import annotations

import logging
from collections.abc import Callable

from papyrium.core.dotfont import DotFont, Glyph
from papyrium.language.escp.interpreter import DEL, FEED_STEP, ArgumentReader, EscpInterpreter
from papyrium.language.proprinter.interpreter import DRAFT, ProprinterInterpreter

logger = logging.getLogger(__name__)

#: The ESC/P commands the LC-10 obeys in both modes, beyond those the
#: Proprinter shares, with their Standard mode handlers.
_COMMANDS_OF_BOTH_MODES = "\n\x0c\x0e\x0f!$%&*-/89?BDWabcefhjklprwx~"

#: ESC I n, for each n the LC-10 accepts: NLQ, its typeface (Courier 0,
#: Sanserif 1, or None to keep it), elite (None to keep the pitch), and
#: download characters.
_PRINT_MODES: dict[int, tuple[bool, int | None, bool | None, bool]] = {
    0: (False, None, False, False),
    1: (False, None, True, False),
    2: (True, 1, None, False),
    3: (True, 0, None, False),
    4: (False, None, False, True),
    5: (False, None, True, True),
    6: (True, None, None, True),
    7: (True, 0, None, False),
}


class LC10IbmModeInterpreter(ProprinterInterpreter):
    """The Proprinter's language as the Star LC-10 speaks it in IBM mode."""

    def _escape_table(self) -> dict[str, Callable[[], ArgumentReader | None]]:
        table = super()._escape_table()
        escp = EscpInterpreter._escape_table(self)
        table.update({letter: escp[letter] for letter in _COMMANDS_OF_BOTH_MODES})
        table["3"] = self._esc_line_spacing_216_not_zero
        table["D"] = self._esc_up_to_28_horizontal_tabs
        table["I"] = self._esc_lc10_print_mode
        table["M"] = self._esc_elite_dropping_condensed
        return table

    def _fs_table(self) -> dict[str, Callable[[], ArgumentReader | None]]:
        """Star's commands after FS: the Standard mode commands whose letters
        the Proprinter's commands took."""
        return {
            "4": self._esc_italic,
            "5": lambda: setattr(self, "_italic", False),
            ":": self._esc_copy_rom,
            "=": lambda: setattr(self, "_msb", 0),
            "Q": self._esc_right_margin,
            "R": self._esc_character_set,
            "\\": self._esc_relative_position,
        }

    def _control(self, code: int) -> ArgumentReader:
        if code == DEL:
            # DEL removes the last character, as in Standard mode.
            yield from EscpInterpreter._control(self, code)
        else:
            yield from super()._control(code)

    # -- The LC-10's own characters, as in Standard mode ---------------------

    def _print_face(self) -> int:
        # ESC I chooses the LC-10's typefaces, through Standard mode's NLQ.
        return DRAFT

    def _print_location(self, location: int) -> None:
        EscpInterpreter._print_location(self, location)

    def _nlq_font(self) -> DotFont | None:
        return EscpInterpreter._nlq_font(self)

    def _nlq_columns(self) -> int:
        return EscpInterpreter._nlq_columns(self)

    def _draft_font(self) -> DotFont:
        return EscpInterpreter._draft_font(self)

    def _is_emphasized(self) -> bool:
        return EscpInterpreter._is_emphasized(self)

    def _proportional_cell(self, location: int, glyph: Glyph) -> tuple[int, int]:
        return EscpInterpreter._proportional_cell(self, location, glyph)

    def _nlq_proportional_cell(self, location: int, glyph: Glyph) -> tuple[int, int] | None:
        return EscpInterpreter._nlq_proportional_cell(self, location, glyph)

    def _vertical_tab(self) -> None:
        EscpInterpreter._vertical_tab(self)

    # -- Its IBM mode commands ----------------------------------------------

    def _esc_lc10_print_mode(self) -> ArgumentReader:
        """0 draft, 1 draft elite, 2 Sanserif, 3 or 7 Courier, 4 and 5 draft
        and draft elite from the download set, 6 NLQ from it; or the digits."""
        n = yield
        n = n - ord("0") if ord("0") <= n <= ord("7") else n
        mode = _PRINT_MODES.get(n)
        if mode is None:
            logger.debug("ignoring print mode %d", n)
            return
        self._print_line()
        self._nlq, typeface, elite, download = mode
        if typeface is not None:
            self._typeface = typeface
        if elite is not None:
            self._elite = elite
        self._user_set_selected = download

    def _esc_line_spacing_216_not_zero(self) -> ArgumentReader:
        n = yield
        if n:
            self._line_spacing = n * FEED_STEP
        else:
            logger.debug("ignoring zero line spacing")

    def _esc_up_to_28_horizontal_tabs(self) -> ArgumentReader:
        """Standard mode's ESC D, with the Proprinter's 28 stops."""
        columns = yield from self._read_stops(28)
        width = self._tab_unit()
        self._tabs = [column * width for column in columns]

    def _esc_elite_dropping_condensed(self) -> None:
        self._elite, self._condensed = True, False

    def _esc_download(self) -> ArgumentReader:
        """The Proprinter's ESC =, ignored with NLQ selected or the RAM
        serving as a buffer."""
        if self._mechanism.user_defined_characters and not self._nlq:
            yield from super()._esc_download()
            return
        low = yield
        high = yield
        for _ in range(low + 256 * high):
            yield
        logger.debug("ignoring ESC =: NLQ is selected or the RAM is a buffer")
