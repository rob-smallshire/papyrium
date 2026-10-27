"""The LC-10's IBM mode: the Proprinter II's language on the LC-10.

With switch 1-6 off (or after ``ESC 0x02``) the LC-10 emulates an IBM
Proprinter II, and per the emulation rule this is built on the
Proprinter's language as a variant. From the Proprinter it takes its
character sets 1 and 2 and the commands whose letters mean something
else there. It keeps its own typefaces and character generator, which
``ESC I`` chooses among in place of the Proprinter's faces, ``ESC G``
being double strike, and the commands the two modes share; Star's
commands after FS give back the Standard mode commands whose letters the
Proprinter's took.

Each handler follows the firmware's (``docs/star-lc10-firmware.md``,
whose IBM mode section lists them by address). Where IBM mode has a
handler of its own, the cited address is it; the others are Standard
mode's, which test the mode where they differ.
"""

from __future__ import annotations

import logging
from collections.abc import Callable

from papyrium.core.dotfont import DotFont, Glyph
from papyrium.language.escp.interpreter import (
    DC2,
    DEL,
    FEED_STEP,
    PICA_WIDTH,
    SI,
    ArgumentReader,
    EscpInterpreter,
)
from papyrium.language.proprinter.interpreter import DRAFT, ProprinterInterpreter

logger = logging.getLogger(__name__)

#: The ESC/P commands whose Standard mode handlers serve IBM mode too.
_COMMANDS_OF_BOTH_MODES = "\n\x0c\x0e$%&*-/89?BDGHWabcefhjklprw~"

#: The ESC k typefaces ESC I chooses: Courier and Sanserif.
_COURIER, _SANSERIF = 0, 1

#: Vertical tab stops ESC B keeps.
_VERTICAL_TAB_STOPS = 16


class LC10IbmModeInterpreter(ProprinterInterpreter):
    """The Proprinter's language as the Star LC-10 speaks it in IBM mode."""

    def _initialise(self) -> None:
        super()._initialise()
        # $5C bit 4: NLQ asked for, which emphasized, the scripts and
        # condensed suspend; _nlq, bit 2, is whether it prints.
        self._nlq_requested = self._nlq

    def _escape_table(self) -> dict[str, Callable[[], ArgumentReader | None]]:
        table = super()._escape_table()
        escp = EscpInterpreter._escape_table(self)
        table.update({letter: escp[letter] for letter in _COMMANDS_OF_BOTH_MODES})
        table.update(
            {
                "!": self._esc_master_select_ibm,
                "3": self._esc_line_spacing_216_not_zero,
                "5": self._esc_auto_line_feed_or_reread,
                ":": self._esc_elite_ibm,
                "D": self._esc_up_to_28_horizontal_tabs,
                "E": self._esc_emphasized_ibm,
                "F": self._esc_not_emphasized_ibm,
                "I": self._esc_lc10_print_mode,
                "M": self._esc_elite_ibm,
                "P": self._esc_proportional_or_pica,
                "S": self._esc_script_ibm,
                "T": self._esc_no_script_ibm,
                "j": self._esc_reverse_feed_ibm,
                "x": self._esc_nlq_ibm,
            }
        )
        return table

    def _fs_table(self) -> dict[str, Callable[[], ArgumentReader | None]]:
        """Star's commands after FS ($B40E): the Standard mode commands whose
        letters the Proprinter's commands took."""
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
        if code == SI:
            self._condensed_ibm()
        elif code == DC2:
            self._pica_ibm()
        elif code == DEL:
            # DEL removes the last character, as in Standard mode ($9A2F).
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
        # IBM mode's emphasized prints at any pitch, NLQ being suspended.
        return self._emphasized

    def _proportional_cell(self, location: int, glyph: Glyph) -> tuple[int, int]:
        return EscpInterpreter._proportional_cell(self, location, glyph)

    def _nlq_proportional_cell(self, location: int, glyph: Glyph) -> tuple[int, int] | None:
        return EscpInterpreter._nlq_proportional_cell(self, location, glyph)

    def _vertical_tab(self) -> None:
        EscpInterpreter._vertical_tab(self)

    def _default_tabs(self) -> list[int]:
        """Every eight columns from column 9 ($8A6B), one column further
        than Standard mode's, HT moving that many columns in either."""
        return [column * PICA_WIDTH for column in range(9, self._mechanism.columns, 8)]

    def _store_vertical_tabs(self, channel: int) -> ArgumentReader:
        """Up to 16 stops, each line n but the first n - 1 lines down ($A757)."""
        lines = yield from self._read_stops(_VERTICAL_TAB_STOPS)
        stops = [(line - 1 if line > 1 else line) * self._line_spacing for line in lines]
        stops = [stop for stop in stops if stop < self._form_length]
        self._vertical_tab_channels[channel] = stops
        if self._vertical_tab_channel == channel:
            self._vertical_tabs = stops

    # -- NLQ, and the modes that suspend it ----------------------------------

    def _request_nlq(self) -> None:
        """NLQ is asked for; it prints unless emphasized, a script or
        condensed suspends it ($94D3)."""
        self._print_line()
        self._nlq_requested = True
        self._nlq = not (self._emphasized or self._script is not None or self._condensed)

    def _cancel_nlq(self) -> None:
        """Draft ($94FA)."""
        self._print_line()
        self._nlq_requested = self._nlq = False

    def _resume_nlq(self) -> None:
        """NLQ prints again if it was asked for."""
        if self._nlq_requested and not self._emphasized:
            self._nlq = True

    def _condensed_ibm(self) -> None:
        """SI ($94A4): 17 cpi, from pica or elite, suspending NLQ."""
        self._print_line()
        self._condensed, self._elite, self._nlq = True, False, False

    def _pica_ibm(self) -> None:
        """DC2 ($9472): pica, from elite or condensed."""
        self._elite = self._condensed = False
        self._resume_nlq()

    def _esc_elite_ibm(self) -> None:
        """ESC M and ESC : ($9490): elite, from pica or condensed."""
        self._elite, self._condensed = True, False
        self._resume_nlq()

    def _esc_nlq_ibm(self) -> ArgumentReader:
        """ESC x ($94BD): NLQ (1) or draft (0), as a code or a digit."""
        n = self._flag_or_digit((yield))
        if n == 1:
            self._request_nlq()
        elif n == 0:
            self._cancel_nlq()

    def _esc_emphasized_ibm(self) -> None:
        """ESC E ($95F8): emphasized at any pitch, suspending NLQ."""
        self._print_line()
        self._emphasized, self._nlq = True, False

    def _esc_not_emphasized_ibm(self) -> None:
        """ESC F ($960E)."""
        self._print_line()
        self._emphasized = False
        if self._nlq_requested:
            self._nlq = True

    def _esc_script_ibm(self) -> ArgumentReader:
        """ESC S ($967E): superscript (0) or subscript (1), suspending NLQ."""
        n = self._flag_or_digit((yield))
        if n in (0, 1):
            self._print_line()
            self._script = "subscript" if n else "superscript"
            self._nlq = False

    def _esc_no_script_ibm(self) -> None:
        """ESC T ($96BD)."""
        if self._script is not None:
            self._print_line()
            self._script = None
            if self._nlq_requested:
                self._nlq = True

    def _esc_lc10_print_mode(self) -> ArgumentReader:
        """ESC I ($9513), 0-7 as codes or digits: 0 draft, 1 draft elite, 2
        Sanserif, 3 or 7 Courier, 4 and 5 draft and draft elite from the
        download set, 6 NLQ from it. Draft keeps the pitch."""
        n = yield
        n = n - ord("0") if ord("0") <= n <= ord("7") else n
        if n in (0, 1):
            self._cancel_nlq()
            self._user_set_selected = False
            if n == 1:
                self._esc_elite_ibm()
        elif n in (2, 3, 7):
            self._request_nlq()
            self._typeface = _SANSERIF if n == 2 else _COURIER
        elif n in (4, 5, 6):
            self._download_print_mode(nlq=n == 6)
            if n == 5:
                self._esc_elite_ibm()
            elif n == 6:
                self._typeface = _SANSERIF
        else:
            logger.debug("ignoring print mode %d", n)

    def _download_print_mode(self, *, nlq: bool) -> None:
        """The download set in draft ($959E) or NLQ ($95B6), unless the RAM
        is a buffer. NLQ prints whatever the modes, and ends condensed."""
        if not self._mechanism.user_defined_characters:
            logger.debug("ignoring ESC I: the RAM is a buffer")
            return
        self._print_line()
        self._emphasized = False
        self._nlq_requested = self._nlq = nlq
        if nlq and self._condensed:
            self._condensed = False
        self._user_set_selected = True

    def _esc_master_select_ibm(self) -> ArgumentReader:
        """ESC ! ($92F8), with IBM mode's pitch: condensed (4) is 17 cpi,
        otherwise elite (1) or pica; emphasized (8) only at pica."""
        n = yield
        self._underline = bool(n & 0x80)
        self._double_width = bool(n & 0x20)
        self._double_strike = bool(n & 0x10)
        if n & 0x04:
            self._condensed_ibm()
        else:
            self._pica_ibm()
            if n & 0x01:
                self._esc_elite_ibm()
        self._proportional = bool(n & 0x02)
        pica = not (self._elite or self._condensed)
        if n & 0x08 and pica:
            self._esc_emphasized_ibm()
        else:
            self._esc_not_emphasized_ibm()
        self._italic = bool(n & 0x40)

    def _esc_proportional_or_pica(self) -> ArgumentReader:
        """ESC P ($96D9): proportional off (0) or on (1); any other byte
        chooses pica, as Standard mode's ESC P, and is then read again."""
        byte = yield
        if byte in (0, 1):
            self._proportional = bool(byte)
            return
        self._pica_ibm()
        yield from self._reread(byte)

    def _esc_auto_line_feed_or_reread(self) -> ArgumentReader:
        """ESC 5 ($9165): CR feeds too (1) or not (0); any other byte is read
        again."""
        byte = yield
        if byte in (0, 1):
            self._auto_line_feed = bool(byte)
            return
        yield from self._reread(byte)

    def _reread(self, byte: int) -> ArgumentReader:
        """Act on *byte* as if it had just been received."""
        if self._is_printable(byte):
            self._character(byte)
        else:
            yield from self._control(byte & 0x7F)

    @staticmethod
    def _flag_or_digit(value: int) -> int:
        """An argument given as a code or an ASCII digit ($B52E)."""
        return value - ord("0") if value in (ord("0"), ord("1")) else value

    # -- Paper and position ---------------------------------------------------

    def _esc_line_spacing_216_not_zero(self) -> ArgumentReader:
        """ESC 3 ($97D5): n/216 inch; IBM mode ignores 0."""
        n = yield
        if n:
            self._line_spacing = n * FEED_STEP
        else:
            logger.debug("ignoring zero line spacing")

    def _esc_reverse_feed_ibm(self) -> ArgumentReader:
        """ESC j ($A12A): as in Standard mode, returning the carriage where a
        line feed does."""
        yield from self._esc_reverse_feed()
        if self._mechanism.line_feed_returns:
            self._x = self._left_margin

    def _esc_up_to_28_horizontal_tabs(self) -> ArgumentReader:
        """ESC D ($A501): Standard mode's, with 28 stops rather than 32."""
        columns = yield from self._read_stops(28)
        width = self._tab_unit()
        self._tabs = [column * width for column in columns]

    def _esc_download(self) -> ArgumentReader:
        """ESC = ($AA06): the Proprinter's, ignored with NLQ selected or the
        RAM serving as a buffer."""
        if self._mechanism.user_defined_characters and not self._nlq:
            yield from super()._esc_download()
            return
        low = yield
        high = yield
        for _ in range(low + 256 * high):
            yield
        logger.debug("ignoring ESC =: NLQ is selected or the RAM is a buffer")
