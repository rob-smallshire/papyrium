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
from collections.abc import Callable, Generator, Iterable
from dataclasses import dataclass, field

from papyrium.core.dotfont import Glyph, code_points
from papyrium.core.model import Interpreter
from papyrium.core.page import Page, TextMark, inches
from papyrium.language.escp.charsets import CharacterSet, character_at, rom_location
from papyrium.language.escp.mechanism import EscpMechanism

logger = logging.getLogger(__name__)

NUL, BEL, BS, HT, LF, VT, FF, CR, SO, SI = 0, 7, 8, 9, 10, 11, 12, 13, 14, 15
DC1, DC2, DC3, DC4, CAN, ESC, DEL = 17, 18, 19, 20, 24, 27, 127

#: Codes below 32 that stay controls even when ESC I makes the others printable.
PRINTER_CONTROLS = frozenset({BEL, BS, HT, LF, VT, FF, CR, SO, SI, DC1, DC2, DC3, DC4, CAN, ESC})

#: Character widths, in units, for each pitch.
PICA_WIDTH = inches(1) // 10
ELITE_WIDTH = inches(1) // 12
CONDENSED_WIDTH = 252  # 7/120 inch, about 17.1 characters per inch

#: Dot columns in a character cell at fixed pitch.
CELL_COLUMNS = 12

#: Column step for proportional characters: 1/120 inch.
PROPORTIONAL_STEP = inches(1) // 120

#: Width of a proportional space, in proportional columns.
PROPORTIONAL_SPACE_COLUMNS = 10

#: The second pass of double-strike printing is this far below the first: 1/216 inch.
DOUBLE_STRIKE_OFFSET = inches(1) // 216

#: Superscript and subscript rows are half the normal pin pitch apart.
SCRIPT_ROW_PITCH = inches(1) // 144

#: Horizontal dot spacing of each bit-image density (ESC * m), in units.
GRAPHICS_STEP = {
    0: inches(1) // 60,
    1: inches(1) // 120,
    2: inches(1) // 120,
    3: inches(1) // 240,
    4: inches(1) // 80,
    5: inches(1) // 72,
    6: inches(1) // 90,
}

#: Densities that move the head too fast to fire a pin in two adjacent columns.
HIGH_SPEED_MODES = frozenset({2, 3})

#: The font's name for the zero printed when the slashed-zero switch is on.
SLASHED_ZERO = "0\u0338"

#: The baseline row of the character matrix, about which italics lean.
BASELINE_ROW = 6

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


class EscpInterpreter(Interpreter):
    """Interprets ESC/P for a 9-pin printer described by an :class:`EscpMechanism`."""

    def __init__(self, mechanism: EscpMechanism) -> None:
        self._mechanism = mechanism
        self._font = mechanism.font
        self._completed: list[Page] = []
        self._page_number = 0
        self._paper_dots: list[tuple[int, int]] = []
        self._paper_text: list[TextMark] = []
        self._sheet_top = 0
        self._missing_characters: set[str] = set()
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
        return self._take_completed()

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
        self._script: str | None = None
        self._msb: int | None = None
        self._character_set = mechanism.character_set
        self._high_codes_printable = mechanism.high_codes_printable
        self._low_codes_printable = False
        self._immediate = False
        self._line_spacing = inches(1) // 6
        self._form_length = mechanism.sheet_length
        self._left_margin = 0
        # None until ESC Q sets one: the power-on margin depends on the pitch.
        self._right_margin: int | None = None
        self._tabs = self._default_tabs()
        # Eight stored channels of vertical tab stops; channel 0 is selected.
        two_lines = 2 * self._line_spacing
        self._vertical_tab_channels: list[list[int]] = [
            list(range(two_lines, self._form_length, two_lines))
        ] + [[] for _ in range(7)]
        self._vertical_tab_channel = 0
        self._vertical_tabs = self._vertical_tab_channels[0]
        self._skip_perforation = mechanism.skip_perforation_lines * self._line_spacing
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
        return code != DEL and self._low_codes_printable and code not in PRINTER_CONTROLS

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
        if code >= 0x20:
            code = rom_location(code, self._character_set)
        return code | (byte & 0x80)

    def _character(self, byte: int) -> None:
        location = self._location(byte)
        # The ROM keeps italic characters at 128-255; the RAM has its own there.
        from_rom = self._glyph_source(location)[0] == "rom"
        italic = self._italic or (from_rom and location >= 0x80)
        width, step, offset, glyph_key = self._character_layout(location)
        if self._x + width > self._right_limit(text=True):
            # A full line prints and the carriage returns, as for CR LF.
            self._print_line()
            self._x = self._left_margin
            self._advance_line()
            width, step, offset, glyph_key = self._character_layout(location)
        dots = self._character_dots(location, glyph_key, step, offset, italic)
        entry = _Entry(self._x, [(self._x + dx, self._y + dy) for dx, dy in dots])
        entry.text.append(self._text_mark(location, width))
        if self._underline:
            entry.dots.extend(self._underline_dots(width))
        self._line.append(entry)
        self._x += width
        if self._immediate:
            self._print_line()

    @staticmethod
    def _rom_character(location: int) -> str:
        """The character at a ROM location; the italics at 128-255 mirror 0-127."""
        location &= 0x7F
        return " " if location == DEL else character_at(location)

    def _text_mark(self, location: int, width: int) -> TextMark:
        # A user-defined character is recorded as the ROM character it replaces.
        blank = self._glyph_source(location) == _BLANK
        character = " " if blank else self._rom_character(location)
        height = self._font.rows * self._mechanism.pin_pitch
        y = self._y
        if self._script is not None:
            height = self._font.rows * SCRIPT_ROW_PITCH
            if self._script == "subscript":
                y += 4 * self._mechanism.pin_pitch
        return TextMark(x=self._x, y=y, width=width, height=height, character=character)

    def _glyph_source(self, location: int) -> tuple:
        """Where the dots for *location* come from, as a cache key."""
        if not self._user_set_selected or (self._ram_holds_rom and location not in self._ram):
            return ("rom", location & 0x7F)
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
        if character == "0" and self._mechanism.slashed_zero:
            glyph = self._font.glyph(SLASHED_ZERO)
            if glyph is not None:
                return glyph
            self._report_missing(SLASHED_ZERO, "printing a plain zero")
        glyph = self._font.glyph(character)
        if glyph is None:
            self._report_missing(character, "printing nothing")
            return Glyph(frozenset())
        return glyph

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
            elif glyph.leftmost is None:
                columns, offset = PROPORTIONAL_SPACE_COLUMNS, 0
            else:
                columns = glyph.rightmost - glyph.leftmost + 3
                offset = 1 - glyph.leftmost
            step = PROPORTIONAL_STEP * double
            return columns * step, step, offset, glyph_source
        width = self._column_width() * double
        return width, width // CELL_COLUMNS, 0, glyph_source

    def _character_dots(
        self, location: int, glyph_source: tuple, step: int, offset: int, italic: bool
    ) -> tuple[tuple[int, int], ...]:
        """The dots of a character relative to the head, cached by style."""
        key = (
            glyph_source,
            step,
            offset,
            italic,
            self._script,
            self._is_emphasized(),
            self._is_double_strike(),
        )
        dots = self._glyph_cache.get(key)
        if dots is None:
            dots = tuple(self._style_dots(self._glyph(location), step, offset, italic))
            if glyph_source[0] != "ram":
                self._glyph_cache[key] = dots
        return dots

    def _style_dots(
        self, glyph: Glyph, step: int, offset: int, italic: bool
    ) -> Iterable[tuple[int, int]]:
        pin_pitch = self._mechanism.pin_pitch
        for column, row in sorted(glyph.dots, key=lambda dot: (dot[1], dot[0])):
            dx = (column + offset) * step
            if italic:
                dx += (BASELINE_ROW - row) * step // 2
            if self._script == "superscript":
                dy = row * SCRIPT_ROW_PITCH
            elif self._script == "subscript":
                dy = 4 * pin_pitch + row * SCRIPT_ROW_PITCH
            else:
                dy = row * pin_pitch
            passes = [(dx, dy)]
            if self._is_double_width():
                # Enlarged characters strike every dot twice, side by side.
                passes.append((dx + step // 2, dy))
            if self._is_emphasized():
                passes.extend([(x + step // 2, y) for x, y in passes])
            if self._is_double_strike():
                passes.extend([(x, y + DOUBLE_STRIKE_OFFSET) for x, y in passes])
            yield from passes

    # Each mode has its own switch; a mode of higher priority masks a lower
    # one without cancelling it: elite, proportional, emphasized, condensed.

    def _is_proportional(self) -> bool:
        return self._proportional and not self._elite

    def _is_emphasized(self) -> bool:
        """Proportional characters always print emphasized."""
        return not self._elite and (self._emphasized or self._proportional)

    def _is_double_strike(self) -> bool:
        """Super- and subscript always print double-strike."""
        return self._double_strike or self._script is not None

    def _is_double_width(self) -> bool:
        return self._double_width or self._one_line_double_width

    def _underline_dots(self, width: int) -> list[tuple[int, int]]:
        y = self._y + self._mechanism.underline_row * self._mechanism.pin_pitch
        return [(self._x + x, y) for x in range(0, width, PROPORTIONAL_STEP)]

    # -- Bit-image graphics -----------------------------------------------

    def _graphics(self, mode: int, columns: list[int], *, nine_pin: bool) -> None:
        step = GRAPHICS_STEP.get(mode)
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

    def _cancel(self) -> None:
        """Discard the text in the buffer, returning the head to where it began."""
        if self._line:
            self._x = self._line[0].x_before
            self._line.clear()

    def _carriage_return(self) -> None:
        self._print_line()
        self._x = self._left_margin
        if self._mechanism.auto_line_feed:
            self._advance_line()

    def _line_feed(self) -> None:
        self._print_line()
        self._x = self._left_margin
        self._advance_line()

    def _advance_line(self) -> None:
        self._one_line_double_width = False
        self._advance(self._line_spacing)
        if self._skip_perforation:
            form_bottom = self._form_top + self._form_length
            if form_bottom - self._skip_perforation <= self._y < form_bottom:
                self._advance(form_bottom - self._y)

    def _advance(self, distance: int) -> None:
        self._y += distance
        while self._y >= self._form_top + self._form_length:
            self._form_top += self._form_length
        while self._y >= self._sheet_top + self._mechanism.sheet_length:
            self._eject_page()

    def _form_feed(self) -> None:
        self._print_line()
        self._x = self._left_margin
        self._one_line_double_width = False
        self._advance(self._form_top + self._form_length - self._y)

    def _vertical_tab(self) -> None:
        position = self._y - self._form_top
        below = [tab for tab in self._vertical_tabs if tab > position]
        if not self._vertical_tabs:
            self._line_feed()
        elif below:
            self._print_line()
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

        return {
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
            "O": setter("_skip_perforation", 0),
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
        }

    @staticmethod
    def _flag(value: int) -> bool:
        """ESC/P accepts 0/1 or the ASCII digits '0'/'1' for on/off arguments."""
        return value in (1, ord("1"))

    def _esc_master_select(self) -> ArgumentReader:
        """Pitch, weight and width only; italic, underline and the rest are untouched."""
        n = yield
        self._elite = bool(n & 0x01)
        self._condensed = bool(n & 0x04)
        self._emphasized = bool(n & 0x08)
        self._double_strike = bool(n & 0x10)
        self._double_width = bool(n & 0x20)

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
        self._line_spacing = (yield) * DOUBLE_STRIKE_OFFSET

    def _esc_line_spacing_72(self) -> ArgumentReader:
        n = yield
        if n <= 85:
            self._line_spacing = n * self._mechanism.pin_pitch
        else:
            logger.debug("ignoring line spacing of %d/72 inch", n)

    def _esc_immediate_feed(self) -> ArgumentReader:
        n = yield
        self._print_line()
        self._advance(n * DOUBLE_STRIKE_OFFSET)

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
        self._y = max(self._sheet_top, self._y - n * DOUBLE_STRIKE_OFFSET)
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
        if self._elite:
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
            self._tabs = self._default_tabs()

    def _esc_left_margin(self) -> ArgumentReader:
        n = yield
        self._cancel()
        left = n * self._column_width()
        # The head stays put; the margin applies from the next carriage return.
        if left + self._narrowest_line() <= self._right_limit(text=False):
            self._left_margin = left
            self._tabs = self._default_tabs()

    def _esc_character_set(self) -> ArgumentReader:
        n = yield
        self._print_line()
        try:
            self._character_set = CharacterSet(n)
        except ValueError:
            logger.debug("ignoring unknown international character set %d", n)

    def _esc_script(self) -> ArgumentReader:
        n = yield
        self._script = "subscript" if self._flag(n) else "superscript"

    def _esc_double_width(self) -> ArgumentReader:
        self._double_width = self._flag((yield))
        if not self._double_width:
            self._one_line_double_width = False

    def _esc_proportional(self) -> ArgumentReader:
        self._proportional = self._flag((yield))
