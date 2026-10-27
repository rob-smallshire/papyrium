"""The Star LC-10's interpreter: ESC/P in Standard mode, the IBM Proprinter
II's language in IBM mode.

The firmware keeps the mode in one bit (``$37`` bit 5), set from switch
1-6 at power on and by ``ESC 0x01`` and ``ESC 0x02`` at any time, and
looks up commands in a table for each mode; the handlers the modes share
test the bit where they differ. So does this interpreter, one for both
modes, so that a job can change mode part way through.

Standard mode is the ESC/P interpreter with the LC-10's mechanism. IBM
mode is built, per the emulation rule, on the Proprinter's language as a
variant: from the Proprinter it takes its character sets 1 and 2 and the
commands whose letters mean something else there. It keeps the LC-10's
own typefaces and character generator, which ``ESC I`` chooses among in
place of the Proprinter's faces, ``ESC G`` being double strike, and the
commands the two modes share; Star's commands after FS give back the
Standard mode commands whose letters the Proprinter's took.

Each handler follows the firmware's (``docs/star-lc10-firmware.md``,
whose IBM mode section lists them by address). Where IBM mode has a
handler of its own, the cited address is it; the others are Standard
mode's, which test the mode where they differ.
"""

from __future__ import annotations

import logging
from collections.abc import Callable

from papyrium.core.dotfont import DotFont, Glyph
from papyrium.language.escp.charsets import IBM_LOCATION
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

#: The commands after ESC in Standard mode, as its firmware's command table
#: lists them ($B1F4).
STANDARD_COMMANDS = frozenset(
    "\x01\x02\n\x0c\x0e\x0f\x19 !#$%&*+-/0123456789:<=>?@ABCDEFGHJKLMNOPQRSTUWXYZ[\\^_"
    "abcefhjklprtwx~"
)

#: The ESC/P commands whose Standard mode handlers serve IBM mode too.
_COMMANDS_OF_BOTH_MODES = "\n\x0c\x0e$%&*-/89?BDGHWabcefhjklprw~"

#: The codes of the IBM table marked as block graphics ($84BD), which are
#: never underlined or overlined ($F81B): line drawing and shading, and the
#: integral halves.
_BLOCK_GRAPHICS = frozenset(range(0xB0, 0xE0)) | {0xF4, 0xF5}

#: The ESC k typefaces ESC I chooses: Courier and Sanserif.
_COURIER, _SANSERIF = 0, 1

#: Vertical tab stops ESC B keeps.
_VERTICAL_TAB_STOPS = 16


class LC10Interpreter(ProprinterInterpreter):
    """The Star LC-10's languages, starting in IBM mode (*ibm_mode*, switch
    1-6 off) or Standard mode."""

    def __init__(self, mechanism, *, ibm_mode: bool = False) -> None:
        # $37 bit 5, which ESC @ leaves as it is.
        self._ibm = ibm_mode
        super().__init__(mechanism)

    def _initialise(self) -> None:
        super()._initialise()
        # $5C bit 4: NLQ asked for, which emphasized, the scripts and
        # condensed suspend; _nlq, bit 2, is whether it prints.
        self._nlq_requested = self._nlq
        self._character_table_from_switches()
        if not self._ibm:
            self._ram_holds_rom = False

    def _character_table_from_switches(self) -> None:
        """The IBM table and set as power on and ESC @ choose them ($9060):
        IBM mode always has the table, in set #2 with switch 1-7 on;
        Standard mode has both with 1-7 off, the italic table and set #1
        with it on."""
        switch_1_7_off = self._mechanism.graphics_table
        if self._ibm:
            self._graphics_table = True
            self._ibm_set = 1 if switch_1_7_off else 2
        else:
            self._graphics_table = switch_1_7_off
            self._ibm_set = 2 if switch_1_7_off else 1

    # -- The mode ---------------------------------------------------------------

    def _switch_mode(self, ibm: bool) -> None:
        """ESC 0x01 ($B167) and ESC 0x02 ($B16E): Standard or IBM mode, with
        the IBM table off or on; the IBM set is kept."""
        self._ibm = self._graphics_table = ibm
        self._escapes = self._ibm_escapes if ibm else self._standard_escapes
        self._fs_commands = self._fs_table()

    def _escape_table(self) -> dict[str, Callable[[], ArgumentReader | None]]:
        """The current mode's escapes, keeping both for a change of mode."""
        escp = EscpInterpreter._escape_table(self)
        self._standard_escapes = {
            letter: handler for letter, handler in escp.items() if letter in STANDARD_COMMANDS
        }
        self._standard_escapes["E"] = self._esc_emphasized_standard
        self._standard_escapes["x"] = self._esc_nlq_standard
        self._ibm_escapes = self._ibm_escape_table(escp)
        for table in (self._standard_escapes, self._ibm_escapes):
            table["\x01"] = lambda: self._switch_mode(False)
            table["\x02"] = lambda: self._switch_mode(True)
        return self._ibm_escapes if self._ibm else self._standard_escapes

    def _ibm_escape_table(
        self, escp: dict[str, Callable[[], ArgumentReader | None]]
    ) -> dict[str, Callable[[], ArgumentReader | None]]:
        table = super()._escape_table()
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
        """Star's commands after FS in IBM mode ($B40E): the Standard mode
        commands whose letters the Proprinter's commands took. Standard
        mode has none ($B3F7)."""
        if not self._ibm:
            return {}
        return {
            "4": self._esc_italic,
            "5": lambda: setattr(self, "_italic", False),
            ":": self._esc_copy_rom,
            "=": lambda: setattr(self, "_msb", 0),
            "Q": self._esc_right_margin,
            "R": self._esc_character_set,
            "\\": self._esc_relative_position,
        }

    # -- What the mode changes ---------------------------------------------------

    def _location(self, byte: int) -> int:
        if self._ibm:
            return super()._location(byte)
        return EscpInterpreter._location(self, byte)

    def _is_lined(self, location: int) -> bool:
        """Underline and overline pass over all but the block graphics, in
        either mode."""
        return location - IBM_LOCATION + 0x80 not in _BLOCK_GRAPHICS

    def _is_printable(self, byte: int) -> bool:
        if byte == 0xFF:
            return False
        if self._ibm:
            return super()._is_printable(byte)
        return EscpInterpreter._is_printable(self, byte)

    def _control_code(self, byte: int) -> int:
        """0xFF is NUL in either mode, the input code turning it into 0
        before anything else ($83FA, $843F)."""
        return 0 if byte == 0xFF else byte & 0x7F

    def _control(self, code: int) -> ArgumentReader:
        if not self._ibm:
            yield from EscpInterpreter._control(self, code)
        elif code == SI:
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
        if self._ibm:
            return self._emphasized
        return EscpInterpreter._is_emphasized(self)

    def _proportional_cell(self, location: int, glyph: Glyph) -> tuple[int, int]:
        return EscpInterpreter._proportional_cell(self, location, glyph)

    def _nlq_proportional_cell(self, location: int, glyph: Glyph) -> tuple[int, int] | None:
        return EscpInterpreter._nlq_proportional_cell(self, location, glyph)

    def _vertical_tab(self) -> None:
        EscpInterpreter._vertical_tab(self)

    def _default_tabs(self) -> list[int]:
        """Every eight columns from column 9 ($8A6B), one column further
        than Standard mode's, HT moving that many columns in either."""
        if not self._ibm:
            return EscpInterpreter._default_tabs(self)
        return [column * PICA_WIDTH for column in range(9, self._mechanism.columns, 8)]

    def _store_vertical_tabs(self, channel: int) -> ArgumentReader:
        """Up to 16 stops, each line n but the first n - 1 lines down in IBM
        mode ($A757)."""
        lines = yield from self._read_stops(_VERTICAL_TAB_STOPS)
        if self._ibm:
            lines = [line - 1 if line > 1 else line for line in lines]
        stops = [line * self._line_spacing for line in lines]
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

    def _esc_nlq_standard(self) -> ArgumentReader:
        """Standard mode's ESC x ($9431): NLQ, emphasized off (1), or draft (0)."""
        n = self._flag_or_digit((yield))
        if n == 1:
            self._print_line()
            self._nlq_requested = self._nlq = True
            self._emphasized = False
        elif n == 0:
            self._cancel_nlq()

    def _esc_emphasized_standard(self) -> None:
        """Standard mode's ESC E ($95D9): emphasized, only in draft at pica."""
        if self._nlq or self._elite or self._condensed:
            logger.debug("ignoring ESC E: emphasized is draft pica only")
            return
        self._print_line()
        self._emphasized = True

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
