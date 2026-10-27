"""EscpInterpreter: an incremental ESC/P interpreter for 9-pin printers.

Written from the published FX-series command descriptions. Bytes are
consumed one at a time by a generator-based state machine, so the pages
produced never depend on how the stream was chunked.

Characters go into a line buffer, as on the real printer, and are
committed to the paper when the line is printed (CR, LF, FF, VT, ESC J, or
a full line) or the buffer is flushed (BS, HT, SI, ESC 4, ESC R, and every
graphics command, whose dots are committed at once). DEL, CAN, ESC Q,
ESC l and ESC @ discard what is still in the buffer.

Paper is continuous fanfold. A page is one sheet, perforation to
perforation, and its length is fixed by the paper. Dots are kept at
absolute paper positions; a page is complete once the head has moved past
its bottom edge, so a line printed across a perforation splits between
pages exactly as the paper would.

The printer's forms are a separate matter: the top of form and form length
are the printer's own reckoning, which form feed, vertical tabs and
skip-over-perforation measure from, and which ESC C and ESC @ reset at the
current line. They start aligned with the sheets but need not stay so.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Generator
from dataclasses import dataclass, field, replace

from papyrium.core.dotfont import DotFont, Glyph, code_points
from papyrium.core.model import Interpreter
from papyrium.core.page import Page, TextMark, inches
from papyrium.language.escp.charsets import IBM_LOCATION, character_at, rom_location
from papyrium.language.escp.generator import SCRIPT_ROW_PITCH, CharacterStyle
from papyrium.language.escp.mechanism import EscpMechanism

logger = logging.getLogger(__name__)

NUL, BEL, BS, HT, LF, VT, FF, CR, SO, SI = 0, 7, 8, 9, 10, 11, 12, 13, 14, 15
DC1, DC2, DC3, DC4, CAN, ESC, RS, DEL = 17, 18, 19, 20, 24, 27, 30, 127

#: Codes below 32 that stay controls even when ESC I makes the others printable.

#: Character widths, in units, for each pitch.
PICA_WIDTH = inches(1) // 10
ELITE_WIDTH = inches(1) // 12
CONDENSED_WIDTH = 252  # 7/120 inch, about 17.1 characters per inch

#: Column step for proportional characters: 1/120 inch.
PROPORTIONAL_STEP = inches(1) // 120

#: The unit of ESC 3, ESC J and ESC j: 1/216 inch.
FEED_STEP = inches(1) // 216

#: Horizontal dot spacing of each bit-image density (ESC * m), in units.
GRAPHICS_STEP = {
    0: inches(1) // 60,
    1: inches(1) // 120,
    2: inches(1) // 120,
    3: inches(1) // 240,
    4: inches(1) // 80,
    5: inches(1) // 72,
    6: inches(1) // 90,
    7: inches(1) // 144,
}

#: Densities that move the head too fast to fire a pin in two adjacent columns.
HIGH_SPEED_MODES = frozenset({2, 3, 7})

#: Condensed elite, on printers that have it: 20 characters an inch.
CONDENSED_ELITE_WIDTH = inches(1) // 20

#: The font's name for the zero printed when the slashed-zero switch is on.
SLASHED_ZERO = "0\u0338"

#: The bit of a character location that selects the ROM's italic form.
ITALIC = 0x80

ArgumentReader = Generator[None, int, None]


@dataclass
class _Entry:
    """One character or graphics run in the line buffer."""

    x_before: int
    dots: list[tuple[int, int]] = field(default_factory=list)
    text: list[TextMark] = field(default_factory=list)


@dataclass(frozen=True)
class _UserCharacter:
    """A character defined with ESC &: its dots and its proportional columns."""

    glyph: Glyph
    first_column: int
    last_column: int


#: Where a character's dots come from: the ROM, the user RAM, or nowhere.
_BLANK = ("blank",)


def _is_space(entry: _Entry) -> bool:
    return bool(entry.text) and all(mark.character == " " for mark in entry.text)


def _shift(entry: _Entry, dx: int, dy: int = 0) -> None:
    """Move a buffered character *dx* to the right and *dy* down."""
    entry.x_before += dx
    entry.dots = [(x + dx, y + dy) for x, y in entry.dots]
    entry.text = [replace(mark, x=mark.x + dx, y=mark.y + dy) for mark in entry.text]


class EscpInterpreter(Interpreter):
    """Interprets ESC/P for a 9-pin printer described by an :class:`EscpMechanism`."""

    def __init__(self, mechanism: EscpMechanism) -> None:
        self._mechanism = mechanism
        self._generator = mechanism.generator
        self._completed: list[Page] = []
        self._page_number = 0
        self._paper_dots: list[tuple[int, int]] = []
        self._paper_text: list[TextMark] = []
        self._sheet_top = 0
        self._macro = b""
        self._macro_pending = False
        self._macro_running = False
        self._missing_characters: set[str] = set()
        self._missing_typefaces: set[int] = set()
        self._glyph_cache: dict[tuple, tuple[tuple[int, int], ...]] = {}
        self._escapes = self._escape_table()
        self._power_on()
        self._machine = self._run()
        next(self._machine)

    # -- Interpreter ------------------------------------------------------

    def feed(self, data: bytes) -> list[Page]:
        send = self._machine.send
        for byte in data:
            # ESC = and ESC > force bit 7 of every byte received, arguments included.
            if self._msb == 0:
                byte &= 0x7F
            elif self._msb == 1:
                byte |= 0x80
            send(byte)
            self._run_macro()
        return self._take_completed()

    def _run_macro(self) -> None:
        """Interpret the macro ESC + 1 asked for, as if it had been received."""
        if not self._macro_pending:
            return
        self._macro_pending = False
        self._macro_running = True
        try:
            for byte in self._macro:
                self._machine.send(byte)
        finally:
            self._macro_running = False

    def finish(self) -> list[Page]:
        self._print_line()
        while self._paper_dots or any(not mark.character.isspace() for mark in self._paper_text):
            self._eject_page()
        return self._take_completed()

    # -- State ------------------------------------------------------------

    def _power_on(self) -> None:
        self._y = self._mechanism.top_offset
        self._form_top = self._y
        self._selected = True
        self._initialise()

    def _initialise(self) -> None:
        """The settings ESC @ restores: the power-on switch settings."""
        mechanism = self._mechanism
        self._elite = False
        self._condensed = mechanism.condensed
        self._proportional = False
        self._emphasized = mechanism.emphasized
        self._double_strike = False
        self._double_width = False
        self._one_line_double_width = False
        self._italic = False
        self._underline = False
        self._overline = False
        self._extra_space = 0
        self._slashed_zero = mechanism.slashed_zero
        # Character size: height and width scales, the half printed, whether
        # the base line stays put, and the scale of line feeds.
        self._height_scale = 1
        self._width_scale = 1
        self._half: str | None = None
        self._base_line_kept = False
        self._spacing_scale = 1
        # The most a character on the current line scales its line feed.
        self._line_feed_scale = 1
        self._script: str | None = None
        self._msb: int | None = None
        self._character_set = mechanism.character_set
        self._high_codes_printable = mechanism.high_codes_printable
        self._graphics_table = mechanism.graphics_table
        self._low_codes_printable = False
        self._immediate = False
        self._nlq = mechanism.near_letter_quality
        self._typeface = 0
        self._justification = 0
        self._line_spacing = inches(1) // 6
        self._form_length = mechanism.sheet_length
        self._left_margin = 0
        # None until ESC Q sets one: the power-on margin depends on the pitch.
        self._right_margin: int | None = None
        self._tabs = self._default_tabs()
        # Eight stored channels of vertical tab stops; channel 0 is selected.
        two_lines = 2 * self._line_spacing
        default_stops = (
            list(range(two_lines, self._form_length, two_lines))
            if mechanism.default_vertical_tabs
            else []
        )
        self._vertical_tab_channels: list[list[int]] = [default_stops] + [[] for _ in range(7)]
        self._vertical_tab_channel = 0
        self._vertical_tabs = self._vertical_tab_channels[0]
        self._skip_perforation = mechanism.skip_perforation_lines * self._line_spacing
        self._top_margin = 0
        self._graphics_modes = {"K": 0, "L": 1, "Y": 2, "Z": 3}
        # The user RAM: 256 locations, empty until defined or copied from the ROM.
        self._ram: dict[int, _UserCharacter] = {}
        self._ram_holds_rom = False
        self._user_set_selected = False
        self._x = self._left_margin
        self._line: list[_Entry] = []

    # -- The state machine ------------------------------------------------

    def _run(self) -> Generator[None, int, None]:
        while True:
            byte = yield
            if not self._selected:
                if byte & 0x7F == DC1:
                    self._selected = True
                continue
            if self._is_printable(byte):
                self._character(byte)
            else:
                yield from self._control(byte & 0x7F)

    def _is_printable(self, byte: int) -> bool:
        """Whether *byte* prints a character; the high codes mirror the controls."""
        code = byte & 0x7F
        if code >= 0x20 and code != DEL:
            return True
        if byte & 0x80:
            return self._high_codes_printable
        return code != DEL and self._low_codes_printable and code not in self._mechanism.controls

    def _control(self, code: int) -> ArgumentReader:
        if code == ESC:
            command = yield
            yield from self._escape(command & 0x7F)
        elif code == CR:
            self._carriage_return()
        elif code == LF:
            self._line_feed()
        elif code == FF:
            self._form_feed()
        elif code == HT:
            self._horizontal_tab()
        elif code == VT:
            self._vertical_tab()
        elif code == BS:
            self._backspace()
        elif code == SO:
            self._one_line_double_width = True
        elif code == SI:
            self._print_line()
            self._condensed = True
        elif code == DC2:
            self._condensed = False
        elif code == DC4:
            self._one_line_double_width = False
        elif code == DC3:
            self._selected = not self._mechanism.software_select
        elif code == CAN:
            self._cancel()
            if self._mechanism.cancel_ends_one_line_enlarged:
                self._one_line_double_width = False
        elif code == DEL:
            if self._line:
                self._x = self._line.pop().x_before
        # NUL, BEL, DC1 and the other control codes do nothing visible.

    def _escape(self, command: int) -> ArgumentReader:
        letter = chr(command)
        handler = self._escapes.get(letter)
        supported = self._mechanism.commands
        if handler is None or (supported is not None and letter not in supported):
            logger.debug("ignoring unsupported command ESC %r", letter)
            return
        result = handler()
        if result is not None:
            yield from result

    # -- Characters -------------------------------------------------------

    def _location(self, byte: int) -> int:
        """The character location *byte* prints: the national sets redirect some codes."""
        code = byte & 0x7F
        if byte & 0x80 and self._graphics_table:
            return IBM_LOCATION + code
        if code >= 0x20:
            code = rom_location(code, self._character_set, self._mechanism.national_differences)
        return code | (byte & 0x80)

    def _character(self, byte: int) -> None:
        location = self._location(byte)
        italic = self._is_italic(location)
        if self._height_scale > 1:
            enlarged = self._enlarged_glyph(location)
            if enlarged is not None:
                self._enlarged_character(location, enlarged)
                return
        nlq_glyph = self._nlq_glyph(location)
        if nlq_glyph is not None:
            self._nlq_character(location, nlq_glyph, italic)
            return
        width, step, offset, glyph_key = self._character_layout(location)
        if self._x + width > self._right_limit(text=True):
            # A full line prints and the carriage returns, as for CR LF.
            self._wrap()
            width, step, offset, glyph_key = self._character_layout(location)
        dots = self._character_dots(location, glyph_key, step, offset, italic)
        entry = _Entry(self._x, [(self._x + dx, self._y + dy) for dx, dy in dots])
        entry.text.append(self._text_mark(location, width))
        entry.dots.extend(self._line_dots(width))
        self._line.append(entry)
        self._x += width + self._extra_space
        if self._immediate:
            self._print_line()

    def _enlarged_glyph(self, location: int) -> Glyph | None:
        """The NLQ glyph an enlarged character prints, in draft or NLQ."""
        font = self._nlq_font()
        if font is None or self._glyph_source(location)[0] != "rom":
            return None
        character = self._rom_character(location)
        if character == "0" and self._slashed_zero:
            character = SLASHED_ZERO
        return font.glyph(character)

    def _enlarged_character(self, location: int, glyph: Glyph) -> None:
        cell = self._column_width()
        width_scale = self._width_scale * (2 if self._is_double_width() else 1)
        width = cell * width_scale
        if self._x + width > self._right_limit(text=True):
            self._wrap()
        pin_pitch = self._mechanism.pin_pitch
        step = cell // self._nlq_font().columns
        dots = self._generator.enlarged_dots(
            glyph, step, width_scale, self._height_scale, pin_pitch
        )
        # A half is eight pins for each doubling of the height.
        half = 8 * (self._height_scale // 2) * pin_pitch
        if self._half == "upper":
            dots = [(dx, dy) for dx, dy in dots if dy < half]
        elif self._half == "lower":
            dots = [(dx, dy - half) for dx, dy in dots if dy >= half]
        raise_by = half if self._base_line_kept else 0
        entry = _Entry(self._x, [(self._x + dx, self._y + dy - raise_by) for dx, dy in dots])
        entry.text.append(self._text_mark(location, width))
        entry.dots.extend(self._line_dots(width))
        self._line.append(entry)
        self._x += width + self._extra_space
        self._line_feed_scale = max(self._line_feed_scale, self._spacing_scale)
        if self._immediate:
            self._print_line()

    def _is_italic(self, location: int) -> bool:
        """Whether the character at *location* prints italic."""
        # The ROM keeps italic characters at 128-255; the RAM has its own there.
        from_rom = self._glyph_source(location)[0] == "rom"
        # The IBM PC table's characters are never italic.
        return location < IBM_LOCATION and (self._italic or (from_rom and bool(location & ITALIC)))

    def _nlq_character(self, location: int, glyph: Glyph, italic: bool) -> None:
        cell = self._column_width() * (2 if self._is_double_width() else 1)
        width, offset = cell, 0
        proportional = self._generator.nlq_proportional_cell(glyph)
        if self._is_proportional() and proportional is not None:
            columns, offset = proportional
            width = columns * (cell // self._nlq_font().columns)
        if self._x + width > self._right_limit(text=True):
            self._wrap()
        dots = self._nlq_dots(glyph, cell, italic, offset)
        entry = _Entry(self._x, [(self._x + dx, self._y + dy) for dx, dy in dots])
        entry.text.append(self._text_mark(location, width))
        entry.dots.extend(self._line_dots(width))
        self._line.append(entry)
        self._x += width + self._extra_space
        if self._immediate:
            self._print_line()

    @staticmethod
    def _rom_character(location: int) -> str:
        """The character at a ROM location; the italics at 128-255 mirror 0-127."""
        location &= ~ITALIC
        return " " if location == DEL else character_at(location)

    def _text_mark(self, location: int, width: int) -> TextMark:
        # A user-defined character is recorded as the ROM character it replaces.
        blank = self._glyph_source(location) == _BLANK
        character = " " if blank else self._rom_character(location)
        height = self._draft_font().rows * self._mechanism.pin_pitch
        y = self._y
        if self._script is not None:
            height = self._draft_font().rows * SCRIPT_ROW_PITCH
            if self._script == "subscript":
                y += 4 * self._mechanism.pin_pitch
        return TextMark(x=self._x, y=y, width=width, height=height, character=character)

    def _glyph_source(self, location: int) -> tuple:
        """Where the dots for *location* come from, as a cache key."""
        if not self._user_set_selected or (self._ram_holds_rom and location not in self._ram):
            return ("rom", location & ~ITALIC)
        if location in self._ram:
            return ("ram", location)
        return _BLANK

    def _glyph(self, location: int) -> Glyph:
        source = self._glyph_source(location)
        if source[0] == "ram":
            return self._ram[location].glyph
        if source == _BLANK:
            return Glyph(frozenset())
        character = self._rom_character(location)
        if character == "0" and self._slashed_zero:
            glyph = self._draft_font().glyph(SLASHED_ZERO)
            if glyph is not None:
                return glyph
            self._report_missing(SLASHED_ZERO, "printing a plain zero")
        glyph = self._draft_font().glyph(character)
        block_graphics_font = self._mechanism.block_graphics_font
        if glyph is None and block_graphics_font is not None:
            glyph = block_graphics_font.glyph(character)
        if glyph is None:
            self._report_missing(character, "printing nothing")
            return Glyph(frozenset())
        return glyph

    def _nlq_glyph(self, location: int) -> Glyph | None:
        """The NLQ form of the ROM character at *location*, if it has one in use.

        Downloaded characters and super- and subscripts print in draft.
        """
        font = self._nlq_font()
        if not self._nlq or font is None or self._script is not None:
            return None
        if self._glyph_source(location)[0] != "rom":
            return None
        character = self._rom_character(location)
        if character == "0" and self._slashed_zero:
            character = SLASHED_ZERO
        return font.glyph(character)

    def _draft_font(self) -> DotFont:
        """The draft font for the pitch: the elite font in elite at fixed
        pitch, where there is one."""
        elite_font = self._mechanism.elite_font
        fixed_elite = self._column_width() == ELITE_WIDTH and not self._is_proportional()
        if elite_font is not None and fixed_elite:
            return elite_font
        return self._mechanism.font

    def _nlq_font(self) -> DotFont | None:
        """The font of the selected NLQ typeface for the pitch, or the first
        typeface's if there is none for it."""
        fonts = self._mechanism.nlq_fonts
        if not fonts:
            return None
        elite_fonts = self._mechanism.nlq_elite_fonts
        if (
            self._column_width() == ELITE_WIDTH
            and self._typeface < len(elite_fonts)
            and elite_fonts[self._typeface] is not None
        ):
            return elite_fonts[self._typeface]
        if self._typeface < len(fonts) and fonts[self._typeface] is not None:
            return fonts[self._typeface]
        if self._typeface not in self._missing_typefaces:
            self._missing_typefaces.add(self._typeface)
            logger.warning("no font for NLQ typeface %d; printing the first", self._typeface)
        return fonts[0]

    def _nlq_dots(
        self, glyph: Glyph, width: int, italic: bool, offset: int
    ) -> list[tuple[int, int]]:
        style = CharacterStyle(
            step=0,
            offset=offset,
            italic=italic,
            emphasized=self._emphasized,
            double_width=self._is_double_width(),
        )
        columns = self._nlq_font().columns
        return self._generator.nlq_dots(glyph, columns, width, style, self._mechanism.pin_pitch)

    def _report_missing(self, character: str, instead: str) -> None:
        if character not in self._missing_characters:
            self._missing_characters.add(character)
            logger.warning("font has no glyph for %s; %s", code_points(character), instead)

    def _character_layout(self, location: int) -> tuple[int, int, int, tuple]:
        """Width, column step, column offset and cache key of a character."""
        double = 2 if self._is_double_width() else 1
        glyph_source = self._glyph_source(location)
        if self._is_proportional():
            glyph = self._glyph(location)
            if glyph_source[0] == "ram":
                # The attribute byte gives the columns to print.
                user_character = self._ram[location]
                columns = user_character.last_column - user_character.first_column + 1
                offset = -user_character.first_column
            else:
                columns, offset = self._generator.proportional_cell(glyph)
            step = PROPORTIONAL_STEP * double
            return columns * step, step, offset, glyph_source
        pitch = self._column_width()
        width = pitch * double
        return width, width // self._generator.cell_columns(pitch), 0, glyph_source

    def _character_dots(
        self, location: int, glyph_source: tuple, step: int, offset: int, italic: bool
    ) -> tuple[tuple[int, int], ...]:
        """The dots of a character relative to the head, cached by style."""
        style = CharacterStyle(
            step=step,
            offset=offset,
            italic=italic,
            script=self._script,
            emphasized=self._is_emphasized(),
            double_strike=self._is_double_strike(),
            double_width=self._is_double_width(),
        )
        key = (glyph_source, self._draft_font(), self._slashed_zero, style)
        dots = self._glyph_cache.get(key)
        if dots is None:
            glyph = self._glyph(location)
            dots = tuple(self._generator.draft_dots(glyph, style, self._mechanism.pin_pitch))
            if glyph_source[0] != "ram":
                self._glyph_cache[key] = dots
        return dots

    # Each mode has its own switch; a mode of higher priority masks a lower
    # one without cancelling it: elite, proportional, emphasized, condensed.

    def _is_proportional(self) -> bool:
        """Proportional spacing; elite masks it unless the printer spaces elite
        proportionally."""
        return self._proportional and (not self._elite or self._mechanism.proportional_elite)

    def _is_emphasized(self) -> bool:
        """Emphasized, which on some printers proportional characters always
        print; NLQ and elite mask it."""
        proportional = self._proportional and self._mechanism.proportional_emphasized
        return not self._nlq and not self._elite and (self._emphasized or proportional)

    def _is_double_strike(self) -> bool:
        """Super- and subscript always print double-strike, and so does NLQ.

        A character with no NLQ form prints in draft struck twice, 1/216
        inch apart; those with one never come here.
        """
        return self._double_strike or self._script is not None or self._nlq

    def _is_double_width(self) -> bool:
        return self._double_width or self._one_line_double_width

    def _line_dots(self, width: int) -> list[tuple[int, int]]:
        """The underline and overline across a character *width* wide."""
        dots = []
        if self._overline:
            dots.extend((self._x + x, self._y) for x in range(0, width, PROPORTIONAL_STEP))
        if self._underline:
            dots.extend(self._underline_dots(width))
        return dots

    def _underline_dots(self, width: int) -> list[tuple[int, int]]:
        y = self._y + self._mechanism.underline_row * self._mechanism.pin_pitch
        return [(self._x + x, y) for x in range(0, width, PROPORTIONAL_STEP)]

    # -- Bit-image graphics -----------------------------------------------

    def _graphics(self, mode: int, columns: list[int], *, nine_pin: bool) -> None:
        step = GRAPHICS_STEP.get(mode) if mode in self._mechanism.graphics_modes else None
        if step is None:
            logger.debug("ignoring graphics in unknown density %d", mode)
            return
        pin_pitch = self._mechanism.pin_pitch
        self._print_line()
        entry = _Entry(self._x)
        fired = 0
        for index, pattern in enumerate(columns):
            x = self._x + index * step
            if x >= self._right_limit(text=False):
                break
            if mode in HIGH_SPEED_MODES:
                pattern &= ~fired
            fired = pattern
            pins = 9 if nine_pin else 8
            for pin in range(pins):
                if pattern & (1 << (pins - 1 - pin)):
                    entry.dots.append((x, self._y + pin * pin_pitch))
        self._line.append(entry)
        self._print_line()
        self._x = min(self._x + len(columns) * step, self._right_limit(text=False))

    def _read_graphics(self, mode: int) -> ArgumentReader:
        low = yield
        high = yield
        count = low + 256 * high
        columns = []
        for _ in range(count):
            columns.append((yield))
        self._graphics(mode, columns, nine_pin=False)

    # -- Paper motion -----------------------------------------------------

    def _print_line(self) -> None:
        for entry in self._line:
            self._paper_dots.extend(entry.dots)
            self._paper_text.extend(entry.text)
        self._line.clear()

    def _wrap(self) -> None:
        """Print a full line and start the next, as for CR LF.

        Under full justification the word the line filled in is carried to
        the next line whole, rather than split.
        """
        carried = self._take_unfinished_word()
        end = self._x
        self._end_line()
        self._x = self._left_margin
        top = self._y
        self._advance_line()
        if carried:
            dx = self._x - carried[0].x_before
            for entry in carried:
                _shift(entry, dx, self._y - top)
            self._line.extend(carried)
            self._x += end - carried[0].x_before + dx

    def _take_unfinished_word(self) -> list[_Entry]:
        """Under full justification, the characters after the line's last space."""
        if self._justification != 3 or (self._mechanism.justify_nlq_only and not self._nlq):
            return []
        spaces = [index for index, entry in enumerate(self._line) if _is_space(entry)]
        if not spaces or spaces[-1] == len(self._line) - 1:
            return []
        carried = self._line[spaces[-1] + 1 :]
        del self._line[spaces[-1] + 1 :]
        return carried

    def _end_line(self) -> None:
        """Print the line at its end, justified as ESC a asks."""
        self._justify()
        self._print_line()

    def _justify(self) -> None:
        mode = self._justification
        if not mode or not self._line or (self._mechanism.justify_nlq_only and not self._nlq):
            return
        entries = self._line
        # Trailing spaces take no part: the text ends at the last other character.
        last = len(entries) - 1
        while last >= 0 and _is_space(entries[last]):
            last -= 1
        if last < 0:
            return
        end = entries[last + 1].x_before if last + 1 < len(entries) else self._x
        spare = self._right_limit(text=True) - end
        if spare <= 0:
            return
        if mode == 3:
            # Spaces leading the line keep their width; the gaps are between words.
            first = 0
            while _is_space(entries[first]):
                first += 1
            gaps = [index for index in range(first, last) if _is_space(entries[index])]
            if not gaps:
                return
            share, extra = divmod(spare, len(gaps))
            shift = 0
            for index, entry in enumerate(entries[: last + 1]):
                _shift(entry, shift)
                if index in gaps:
                    shift += share + (1 if gaps.index(index) < extra else 0)
        else:
            shift = spare // 2 if mode == 1 else spare
            for entry in entries:
                _shift(entry, shift)

    def _cancel(self) -> None:
        """Discard the text in the buffer, returning the head to where it began."""
        if self._line:
            self._x = self._line[0].x_before
            self._line.clear()

    def _carriage_return(self) -> None:
        self._end_line()
        self._x = self._left_margin
        if self._mechanism.carriage_return_ends_one_line_enlarged:
            self._one_line_double_width = False
        if self._mechanism.auto_line_feed:
            self._advance_line()

    def _line_feed(self) -> None:
        self._end_line()
        if self._mechanism.line_feed_returns:
            self._x = self._left_margin
        self._advance_line()

    def _advance_line(self) -> None:
        self._one_line_double_width = False
        scale = max(self._spacing_scale, self._line_feed_scale)
        self._line_feed_scale = 1
        self._advance(self._line_spacing * scale)
        if self._skip_perforation:
            form_bottom = self._form_top + self._form_length
            if form_bottom - self._skip_perforation <= self._y < form_bottom:
                self._advance(form_bottom - self._y + self._top_margin)

    def _advance(self, distance: int) -> None:
        self._y += distance
        while self._y >= self._form_top + self._form_length:
            self._form_top += self._form_length
        while self._y >= self._sheet_top + self._mechanism.sheet_length:
            self._eject_page()

    def _form_feed(self) -> None:
        self._end_line()
        self._x = self._left_margin
        self._one_line_double_width = False
        self._advance(self._form_top + self._form_length - self._y + self._top_margin)

    def _vertical_tab(self) -> None:
        position = self._y - self._form_top
        below = [tab for tab in self._vertical_tabs if tab > position]
        if not self._vertical_tabs:
            self._line_feed()
        elif below:
            self._end_line()
            self._x = self._left_margin
            self._one_line_double_width = False
            self._advance(below[0] - position)
        else:
            self._form_feed()

    def _horizontal_tab(self) -> None:
        # Tab stops are measured from the left margin.
        following = [
            self._left_margin + tab for tab in self._tabs if self._left_margin + tab > self._x
        ]
        self._print_line()
        if following and following[0] <= self._right_limit(text=True):
            self._x = following[0]

    def _backspace(self) -> None:
        width = self._tab_unit()
        self._print_line()
        self._x = max(self._left_margin, self._x - width)

    def _eject_page(self) -> None:
        mechanism = self._mechanism
        top, bottom = self._sheet_top, self._sheet_top + mechanism.sheet_length
        on_page = [(x, y) for x, y in self._paper_dots if y < bottom]
        self._paper_dots = [(x, y) for x, y in self._paper_dots if y >= bottom]
        text_on_page = [mark for mark in self._paper_text if top <= mark.y < bottom]
        self._paper_text = [mark for mark in self._paper_text if mark.y >= bottom]
        self._page_number += 1
        left = mechanism.left_offset
        self._completed.append(
            Page(
                number=self._page_number,
                width=mechanism.paper_width,
                height=mechanism.sheet_length,
                dot_diameter=mechanism.dot_diameter,
                stationery=mechanism.stationery,
                dots=tuple(
                    (left + x, y - top)
                    for x, y in on_page
                    if 0 <= left + x < mechanism.paper_width and y >= top
                ),
                text=tuple(
                    TextMark(left + mark.x, mark.y - top, mark.width, mark.height, mark.character)
                    for mark in text_on_page
                    if left + mark.x < mechanism.paper_width
                ),
            )
        )
        self._sheet_top = bottom

    def _take_completed(self) -> list[Page]:
        completed, self._completed = self._completed, []
        return completed

    def _set_top_of_form(self) -> None:
        """Make the current line the printer's top of form; the paper does not move."""
        self._form_top = self._y

    # -- Escape commands --------------------------------------------------

    def _escape_table(self) -> dict[str, Callable[[], ArgumentReader | None]]:
        def setter(attribute: str, value) -> Callable[[], None]:
            return lambda: setattr(self, attribute, value)

        table = {
            "\x0e": setter("_one_line_double_width", True),
            "\x0f": setter("_condensed", True),
            "!": self._esc_master_select,
            "#": setter("_msb", None),
            "=": setter("_msb", 0),
            ">": setter("_msb", 1),
            "%": self._esc_select_user_set,
            "&": self._esc_define_user_characters,
            ":": self._esc_copy_rom,
            "*": self._esc_graphics,
            "K": lambda: self._read_graphics(self._graphics_modes["K"]),
            "L": lambda: self._read_graphics(self._graphics_modes["L"]),
            "Y": lambda: self._read_graphics(self._graphics_modes["Y"]),
            "Z": lambda: self._read_graphics(self._graphics_modes["Z"]),
            "^": self._esc_nine_pin_graphics,
            "?": self._esc_reassign_graphics,
            "-": self._esc_underline,
            "/": self._esc_select_vertical_tab_channel,
            "0": setter("_line_spacing", inches(1) // 8),
            "1": setter("_line_spacing", inches(7) // 72),
            "2": setter("_line_spacing", inches(1) // 6),
            "3": self._esc_line_spacing_216,
            "A": self._esc_line_spacing_72,
            "J": self._esc_immediate_feed,
            "4": self._esc_italic,
            "5": setter("_italic", False),
            "6": setter("_high_codes_printable", True),
            "7": setter("_high_codes_printable", False),
            "I": self._esc_low_codes_printable,
            "8": lambda: None,
            "9": lambda: None,
            "<": lambda: None,
            "@": self._esc_initialise,
            "B": self._esc_vertical_tabs,
            "C": self._esc_form_length,
            "D": self._esc_horizontal_tabs,
            "E": setter("_emphasized", True),
            "F": setter("_emphasized", False),
            "G": setter("_double_strike", True),
            "H": setter("_double_strike", False),
            "M": setter("_elite", True),
            "P": setter("_elite", False),
            "N": self._esc_skip_perforation,
            "O": self._esc_cancel_margins,
            "Q": self._esc_right_margin,
            "l": self._esc_left_margin,
            "R": self._esc_character_set,
            "S": self._esc_script,
            "T": setter("_script", None),
            "U": self._esc_skip_argument,
            "W": self._esc_double_width,
            "b": self._esc_vertical_tab_channel,
            "i": self._esc_immediate,
            "j": self._esc_reverse_feed,
            "p": self._esc_proportional,
            "s": self._esc_skip_argument,
            "\x19": self._esc_skip_argument,
            "e": self._esc_regular_tabs,
            "a": self._esc_justify,
            "t": self._esc_character_table,
            "f": self._esc_skip,
            "$": self._esc_absolute_position,
            "\\": self._esc_relative_position,
            "X": self._esc_margins,
            " ": self._esc_extra_space,
            "~": self._esc_slashed_zero,
            "\n": self._esc_reverse_line_feed,
            "\x0c": self._esc_top_of_page,
            "+": self._esc_macro,
            "_": self._esc_overline,
            "c": self._esc_top_margin,
            "h": self._esc_size,
            "w": self._esc_double_height,
            "[": self._esc_bracket,
        }
        if self._mechanism.nlq:
            table["x"] = self._esc_nlq
            table["k"] = self._esc_typeface
        return table

    @staticmethod
    def _flag(value: int) -> bool:
        """ESC/P accepts 0/1 or the ASCII digits '0'/'1' for on/off arguments."""
        return value in (1, ord("1"))

    def _esc_master_select(self) -> ArgumentReader:
        """Pitch, weight and width, and on some printers italic and underline."""
        n = yield
        self._elite = bool(n & 0x01)
        self._condensed = bool(n & 0x04)
        self._emphasized = bool(n & 0x08)
        self._double_strike = bool(n & 0x10)
        self._double_width = bool(n & 0x20)
        if self._mechanism.master_select_italic_underline:
            self._italic = bool(n & 0x40)
            self._underline = bool(n & 0x80)

    def _esc_select_user_set(self) -> ArgumentReader:
        n = yield
        yield  # The FX-80 takes a second argument, always 0.
        if self._mechanism.user_defined_characters:
            self._user_set_selected = bool(n & 1)
        else:
            logger.debug("ignoring ESC %%: the RAM is switched to serve as a buffer")

    def _esc_define_user_characters(self) -> ArgumentReader:
        yield  # Always 0.
        first = yield
        last = yield
        for location in range(first, last + 1):
            attribute = yield
            columns = []
            fired = 0
            for _ in range(11):
                # The head never fires a pin in two adjacent columns.
                pattern = (yield) & ~fired
                fired = pattern
                columns.append(pattern)
            top_row = 0 if attribute & 0x80 else 1
            dots = frozenset(
                (column, top_row + bit)
                for column, pattern in enumerate(columns)
                for bit in range(8)
                if pattern & (0x80 >> bit)
            )
            self._ram[location] = _UserCharacter(
                Glyph(dots), first_column=(attribute >> 4) & 0x07, last_column=attribute & 0x0F
            )

    def _esc_copy_rom(self) -> ArgumentReader:
        for _ in range(3):
            yield
        self._ram.clear()
        self._ram_holds_rom = True

    def _esc_graphics(self) -> ArgumentReader:
        mode = yield
        yield from self._read_graphics(mode)

    def _esc_nine_pin_graphics(self) -> ArgumentReader:
        density = yield
        low = yield
        high = yield
        columns = []
        for _ in range(low + 256 * high):
            first = yield
            second = yield
            columns.append((first << 1) | (second >> 7))
        self._graphics(1 if density else 0, columns, nine_pin=True)

    def _esc_reassign_graphics(self) -> ArgumentReader:
        letter = chr((yield) & 0x7F)
        mode = yield
        if letter in self._graphics_modes:
            self._graphics_modes[letter] = mode

    def _esc_underline(self) -> ArgumentReader:
        self._underline = self._flag((yield))

    def _esc_skip_argument(self) -> ArgumentReader:
        yield

    def _esc_line_spacing_216(self) -> ArgumentReader:
        self._line_spacing = (yield) * FEED_STEP

    def _esc_line_spacing_72(self) -> ArgumentReader:
        n = yield
        if n <= 85:
            self._line_spacing = n * self._mechanism.pin_pitch
        else:
            logger.debug("ignoring line spacing of %d/72 inch", n)

    def _esc_immediate_feed(self) -> ArgumentReader:
        n = yield
        self._print_line()
        self._advance(n * FEED_STEP)

    def _esc_low_codes_printable(self) -> ArgumentReader:
        self._low_codes_printable = self._flag((yield))

    def _esc_italic(self) -> None:
        self._print_line()
        self._italic = True

    def _esc_immediate(self) -> ArgumentReader:
        self._immediate = self._flag((yield))
        if self._immediate:
            self._print_line()

    def _esc_reverse_feed(self) -> ArgumentReader:
        """Feed back up the paper, but never past the top of the sheet in the printer."""
        n = yield
        self._print_line()
        self._y = max(self._sheet_top, self._y - n * FEED_STEP)
        while self._y < self._form_top:
            self._form_top -= self._form_length

    def _esc_initialise(self) -> None:
        self._initialise()
        self._set_top_of_form()

    def _read_stops(self, limit: int) -> Generator[None, int, list[int]]:
        stops = []
        while True:
            n = yield
            if n == 0 or (stops and n <= stops[-1]):
                return stops
            if len(stops) < limit:
                stops.append(n)

    def _esc_vertical_tabs(self) -> ArgumentReader:
        yield from self._store_vertical_tabs(0)

    def _store_vertical_tabs(self, channel: int) -> ArgumentReader:
        lines = yield from self._read_stops(16)
        stops = [line * self._line_spacing for line in lines]
        stops = [stop for stop in stops if stop < self._form_length]
        if channel < len(self._vertical_tab_channels):
            self._vertical_tab_channels[channel] = stops
            if self._vertical_tab_channel == channel:
                self._vertical_tabs = stops
        else:
            logger.debug("ignoring vertical tabs for channel %d", channel)

    def _esc_horizontal_tabs(self) -> ArgumentReader:
        columns = yield from self._read_stops(32)
        width = self._tab_unit()
        self._tabs = [column * width for column in columns]

    def _esc_vertical_tab_channel(self) -> ArgumentReader:
        channel = yield
        yield from self._store_vertical_tabs(channel)

    def _esc_select_vertical_tab_channel(self) -> ArgumentReader:
        channel = yield
        if channel < len(self._vertical_tab_channels):
            self._vertical_tab_channel = channel
            self._vertical_tabs = self._vertical_tab_channels[channel]
        else:
            logger.debug("ignoring unknown vertical tab channel %d", channel)

    def _esc_form_length(self) -> ArgumentReader:
        n = yield
        form_length = n * self._line_spacing
        if n == 0:
            form_length = inches((yield))
        self._set_top_of_form()
        self._skip_perforation = 0
        if self._mechanism.form_length_clears_vertical_tabs:
            self._vertical_tab_channels = [[] for _ in range(8)]
            self._vertical_tabs = self._vertical_tab_channels[self._vertical_tab_channel]
        if form_length:
            self._form_length = form_length
        else:
            logger.debug("ignoring a zero form length")

    def _esc_skip_perforation(self) -> ArgumentReader:
        skip = (yield) * self._line_spacing
        if skip < self._form_length:
            self._skip_perforation = skip
        else:
            logger.debug("ignoring a skip-over-perforation as long as the form")

    def _column_width(self) -> int:
        """The fixed pitch, pica for proportional text."""
        if self._nlq:
            # Near letter quality masks condensed, and elite unless the
            # printer has NLQ elite.
            return ELITE_WIDTH if self._elite and self._mechanism.nlq_elite else PICA_WIDTH
        if self._elite:
            if self._condensed and self._mechanism.condensed_elite:
                return CONDENSED_ELITE_WIDTH
            return ELITE_WIDTH
        if self._condensed and not self._is_emphasized():
            return CONDENSED_WIDTH
        return PICA_WIDTH

    def _tab_unit(self) -> int:
        """The column width tabs and backspace count in: pica in proportional mode."""
        if self._is_proportional():
            return PICA_WIDTH
        return self._character_layout(0x20)[0]

    def _default_tabs(self) -> list[int]:
        """Every eight pica columns from the left margin."""
        return [column * PICA_WIDTH for column in range(8, self._mechanism.columns, 8)]

    def _margin_tabs(self) -> list[int]:
        """The tab stops after a margin is set: cleared, or the defaults again."""
        return [] if self._mechanism.margins_clear_tabs else self._default_tabs()

    def _right_limit(self, *, text: bool) -> int:
        """The right margin; at power on, condensed text stops short of it."""
        if self._right_margin is not None:
            return self._right_margin
        full_width = self._mechanism.columns * PICA_WIDTH
        if text and self._column_width() == CONDENSED_WIDTH:
            return min(full_width, self._mechanism.condensed_columns * CONDENSED_WIDTH)
        return full_width

    def _narrowest_line(self) -> int:
        """The least room between the margins: 2 pica, 3 elite or 4 condensed columns."""
        width = self._column_width()
        columns = {ELITE_WIDTH: 3, CONDENSED_WIDTH: 4}.get(width, 2)
        return columns * width

    def _esc_right_margin(self) -> ArgumentReader:
        n = yield
        self._cancel()
        right = n * self._column_width()
        full_width = self._mechanism.columns * PICA_WIDTH
        if self._left_margin + self._narrowest_line() <= right <= full_width:
            self._right_margin = right
            self._tabs = self._margin_tabs()

    def _esc_left_margin(self) -> ArgumentReader:
        n = yield
        self._cancel()
        left = n * self._column_width()
        # The head stays put; the margin applies from the next carriage return.
        if left + self._narrowest_line() <= self._right_limit(text=False):
            self._left_margin = left
            self._tabs = self._margin_tabs()

    def _esc_character_set(self) -> ArgumentReader:
        n = yield
        self._print_line()
        sets = self._mechanism.character_sets
        if n < len(sets):
            self._character_set = sets[n]
        else:
            logger.debug("ignoring international character set %d, which this printer lacks", n)

    def _esc_script(self) -> ArgumentReader:
        n = yield
        self._script = "subscript" if self._flag(n) else "superscript"

    def _esc_double_width(self) -> ArgumentReader:
        self._double_width = self._flag((yield))
        if not self._double_width:
            self._one_line_double_width = False

    def _esc_nlq(self) -> ArgumentReader:
        self._nlq = self._flag((yield))

    def _esc_character_table(self) -> ArgumentReader:
        """Codes 128-255 from the italic table (0) or the IBM PC one (1); not digits."""
        n = yield
        if n in (0, 1):
            self._graphics_table = bool(n)
        else:
            logger.debug("ignoring character table %d", n)

    def _esc_justify(self) -> ArgumentReader:
        """Justify lines left (0), centred (1), right (2) or full (3)."""
        n = (yield) & 0x7F
        n = n - ord("0") if ord("0") <= n <= ord("3") else n
        if 0 <= n <= 3:
            self._justification = n
        else:
            logger.debug("ignoring justification %d", n)

    def _esc_regular_tabs(self) -> ArgumentReader:
        """Horizontal (0) or vertical (1) tab stops every *s* columns or lines."""
        kind = (yield) & 0x7F
        s = yield
        if s == 0:
            logger.debug("ignoring tab stops every 0 columns or lines")
        elif kind in (0, ord("0")):
            width = self._tab_unit()
            right = self._right_limit(text=True) - self._left_margin
            self._tabs = list(range(s * width, right, s * width))
        elif kind in (1, ord("1")):
            step = s * self._line_spacing
            stops = list(range(step, self._form_length, step))
            self._vertical_tab_channels[self._vertical_tab_channel] = stops
            self._vertical_tabs = stops

    def _esc_skip(self) -> ArgumentReader:
        """Print *s* spaces (0), or move to column *s* from the left margin
        where the printer does that instead, or feed *s* lines without a
        carriage return (1)."""
        kind = (yield) & 0x7F
        s = yield
        if kind in (0, ord("0")) and self._mechanism.skip_moves_to_column:
            self._move_to(self._left_margin + min(s, 127) * self._tab_unit())
        elif kind in (0, ord("0")):
            for _ in range(min(s, 127)):
                self._character(0x20)
        elif kind in (1, ord("1")):
            self._print_line()
            for _ in range(s):
                self._advance_line()

    def _move_to(self, x: int) -> None:
        """Move the head to *x*, if it lies between the margins."""
        self._print_line()
        if self._left_margin <= x <= self._right_limit(text=True):
            self._x = x
        else:
            logger.debug("ignoring a move outside the margins")

    def _esc_absolute_position(self) -> ArgumentReader:
        """Move to (n1 + 256 n2)/60 inch from the left margin."""
        low = yield
        high = yield
        self._move_to(self._left_margin + (low + 256 * high) * (inches(1) // 60))

    def _esc_relative_position(self) -> ArgumentReader:
        """Move right n1 + 256 n2 1/120 inch, or left when n2 is 64 or more."""
        low = yield
        high = yield
        if high < 64:
            distance = low + 256 * high
        else:
            distance = -(low + 256 * (high - 64))
        self._move_to(self._x + distance * PROPORTIONAL_STEP)

    def _esc_margins(self) -> ArgumentReader:
        """The left and right margins together, in columns of the pitch."""
        left_column = yield
        right_column = yield
        self._cancel()
        width = self._column_width()
        left, right = left_column * width, right_column * width
        full_width = self._mechanism.columns * PICA_WIDTH
        if left + self._narrowest_line() <= right <= full_width:
            self._left_margin, self._right_margin = left, right
            self._tabs = self._margin_tabs()
        else:
            logger.debug("ignoring margins %d and %d", left_column, right_column)

    def _esc_extra_space(self) -> ArgumentReader:
        """Leave n/240 inch after each character."""
        self._extra_space = ((yield) & 0x7F) * (inches(1) // 240)

    def _esc_cancel_margins(self) -> None:
        """Cancel the bottom margin, and the top margin where there is one."""
        self._skip_perforation = 0
        self._top_margin = 0

    def _esc_top_margin(self) -> ArgumentReader:
        """Start printing on each form at line n, 1-255."""
        n = yield
        if n:
            self._top_margin = (n - 1) * self._line_spacing
        else:
            logger.debug("ignoring a top margin at line 0")

    def _esc_overline(self) -> ArgumentReader:
        """Overline along the top pin, on (1) or off (0)."""
        self._overline = self._flag((yield))

    def _esc_slashed_zero(self) -> ArgumentReader:
        self._slashed_zero = self._flag((yield))

    def _esc_reverse_line_feed(self) -> None:
        """Feed back a line, but never past the top of the sheet in the printer."""
        self._print_line()
        self._y = max(self._sheet_top, self._y - self._line_spacing)
        while self._y < self._form_top:
            self._form_top -= self._form_length

    def _esc_top_of_page(self) -> None:
        """Feed back to the top of the current page."""
        self._print_line()
        self._y = max(self._sheet_top, self._form_top)

    def _esc_macro(self) -> ArgumentReader:
        """Run the macro (1), or define it: up to 16 bytes before RS."""
        first = yield
        if first == 1:
            # A macro that runs itself would run for ever; the printer's would.
            if not self._macro_running:
                self._macro_pending = True
            return
        macro = bytearray()
        byte = first
        while byte != RS:
            if len(macro) < 16:
                macro.append(byte)
            byte = yield
        self._macro = bytes(macro)

    #: ESC h n: height and width scale, half, and line feed scale.
    _SIZES = {
        0: (1, 1, None, 1),
        1: (2, 2, None, 2),
        2: (4, 4, None, 4),
        3: (2, 2, "lower", 1),
        4: (2, 2, "upper", 1),
        5: (4, 4, "lower", 2),
        6: (4, 4, "upper", 2),
    }

    def _esc_size(self) -> ArgumentReader:
        """Double or quadruple size, or one half of it, hanging from the cap line."""
        n = yield
        size = self._SIZES.get(n)
        if size is None:
            logger.debug("ignoring character size %d", n)
            return
        self._print_line()
        self._height_scale, self._width_scale, self._half, self._spacing_scale = size
        self._base_line_kept = False
        self._script = None

    def _esc_double_height(self) -> ArgumentReader:
        """Double height on the base line, line spacing unchanged."""
        on = self._flag((yield))
        self._print_line()
        self._height_scale, self._width_scale, self._half = (2 if on else 1), 1, None
        self._base_line_kept = on
        self._spacing_scale = 1

    def _esc_bracket(self) -> ArgumentReader:
        """ESC [ @ 4 0 0 0 n m: height and line spacing by n, width by m."""
        if (yield) != ord("@"):
            logger.debug("ignoring an ESC [ command other than ESC [ @")
            return
        for _ in range(4):
            yield
        n = yield
        m = yield
        self._print_line()
        height, spacing = n & 0x0F, n >> 4
        if height in (1, 2):
            self._height_scale, self._width_scale, self._half = height, 1, None
            self._base_line_kept = height == 2
        if spacing in (1, 2):
            self._spacing_scale = spacing
        if m in (1, 2):
            self._double_width = m == 2

    def _esc_typeface(self) -> ArgumentReader:
        """Choose the NLQ typeface; in draft it is kept for the next ESC x 1."""
        self._typeface = (yield) & 0x7F

    def _esc_proportional(self) -> ArgumentReader:
        self._proportional = self._flag((yield))
