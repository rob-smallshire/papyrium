"""EscpInterpreter: an incremental ESC/P interpreter for 9-pin printers.

Written from the published FX-series command descriptions. Bytes are
consumed one at a time by a generator-based state machine, so the pages
produced never depend on how the stream was chunked.

Characters and graphics go into a line buffer, as on the real printer, and
are committed to the paper when the line is printed (CR, LF, FF, VT,
ESC J, or a full line). DEL and CAN edit that buffer.

Paper is continuous. Dots are kept at absolute paper positions; a page is
complete once the head has moved past its bottom edge (or a form feed
ejects it), so a line printed across a perforation splits between pages
exactly as the paper would.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Generator, Iterable
from dataclasses import dataclass, field

from papyrium.core.dotfont import Glyph
from papyrium.core.model import Interpreter
from papyrium.core.page import Page, inches
from papyrium.language.escp.charsets import CharacterSet, character_for
from papyrium.language.escp.mechanism import EscpMechanism

logger = logging.getLogger(__name__)

NUL, BEL, BS, HT, LF, VT, FF, CR, SO, SI = 0, 7, 8, 9, 10, 11, 12, 13, 14, 15
DC1, DC2, DC3, DC4, CAN, ESC, DEL = 17, 18, 19, 20, 24, 27, 127

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

#: The baseline row of the character matrix, about which italics lean.
BASELINE_ROW = 6

ArgumentReader = Generator[None, int, None]


@dataclass
class _Entry:
    """One character or graphics run in the line buffer."""

    x_before: int
    dots: list[tuple[int, int]] = field(default_factory=list)


class EscpInterpreter(Interpreter):
    """Interprets ESC/P for a 9-pin printer described by an :class:`EscpMechanism`."""

    def __init__(self, mechanism: EscpMechanism) -> None:
        self._mechanism = mechanism
        self._font = mechanism.font
        self._completed: list[Page] = []
        self._page_number = 0
        self._paper_dots: list[tuple[int, int]] = []
        self._page_top = 0
        self._y = 0
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
            send(byte)
        return self._take_completed()

    def finish(self) -> list[Page]:
        self._print_line()
        while self._paper_dots:
            self._eject_page()
        return self._take_completed()

    # -- State ------------------------------------------------------------

    def _power_on(self) -> None:
        mechanism = self._mechanism
        self._form_length = mechanism.form_length
        self._selected = True
        self._initialise()

    def _initialise(self) -> None:
        """The settings ESC @ restores: the power-on switch settings."""
        mechanism = self._mechanism
        self._elite = False
        self._condensed = mechanism.condensed
        self._proportional = False
        self._emphasized = False
        self._double_strike = False
        self._double_width = False
        self._one_line_double_width = False
        self._italic = False
        self._underline = False
        self._script: str | None = None
        self._msb: int | None = None
        self._character_set = mechanism.character_set
        self._high_codes_printable = mechanism.high_codes_printable
        self._line_spacing = inches(1) // 6
        self._left_margin = 0
        self._right_margin = mechanism.columns * PICA_WIDTH
        self._tabs = [column * PICA_WIDTH for column in range(8, mechanism.columns, 8)]
        self._vertical_tabs: list[int] = []
        self._skip_perforation = mechanism.skip_perforation_lines * self._line_spacing
        self._graphics_modes = {"K": 0, "L": 1, "Y": 2, "Z": 3}
        self._user_glyphs: dict[int, Glyph] = {}
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
            if byte < 0x20 or byte == DEL:
                yield from self._control(byte)
            elif byte < 0xA0 and byte >= 0x80 and not self._high_codes_printable:
                yield from self._control(byte & 0x7F)
            elif byte == 0xFF:
                continue
            else:
                self._character(byte)

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
            self._condensed = True
        elif code == DC2:
            self._condensed = False
        elif code == DC4:
            self._one_line_double_width = False
        elif code == DC3:
            self._selected = False
        elif code == CAN:
            self._line.clear()
            self._x = self._left_margin
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

    def _character(self, byte: int) -> None:
        if self._msb == 0:
            byte &= 0x7F
        elif self._msb == 1:
            byte |= 0x80
        italic = self._italic or byte >= 0x80
        code = byte & 0x7F
        if code < 0x20:
            # A printable high code (ESC 6) for a control position has no glyph.
            code = 0x20
        width, step, offset, glyph_key = self._character_layout(code)
        if self._x + width > self._right_margin:
            self._print_line()
            self._x = self._left_margin
            self._advance(self._line_spacing)
        dots = self._character_dots(code, glyph_key, step, offset, italic)
        entry = _Entry(self._x, [(self._x + dx, self._y + dy) for dx, dy in dots])
        if self._underline:
            entry.dots.extend(self._underline_dots(width))
        self._line.append(entry)
        self._x += width

    def _glyph(self, code: int) -> Glyph:
        if self._user_set_selected and code in self._user_glyphs:
            return self._user_glyphs[code]
        character = character_for(code, self._character_set)
        glyph = self._font.glyph(character)
        if glyph is None:
            if character not in self._missing_characters:
                self._missing_characters.add(character)
                logger.warning("font has no glyph for U+%04X; printing nothing", ord(character))
            return Glyph(frozenset())
        return glyph

    def _character_layout(self, code: int) -> tuple[int, int, int, tuple]:
        """Width, column step, column offset and cache key of a character."""
        double = 2 if self._is_double_width() else 1
        glyph_source = (
            ("user", code)
            if self._user_set_selected and code in self._user_glyphs
            else (self._character_set, code)
        )
        if self._proportional:
            glyph = self._glyph(code)
            if glyph.leftmost is None:
                columns, offset = PROPORTIONAL_SPACE_COLUMNS, 0
            else:
                columns = glyph.rightmost - glyph.leftmost + 3
                offset = 1 - glyph.leftmost
            step = PROPORTIONAL_STEP * double
            return columns * step, step, offset, glyph_source
        if self._elite:
            width = ELITE_WIDTH
        elif self._condensed and not self._emphasized:
            width = CONDENSED_WIDTH
        else:
            width = PICA_WIDTH
        width *= double
        return width, width // CELL_COLUMNS, 0, glyph_source

    def _character_dots(
        self, code: int, glyph_source: tuple, step: int, offset: int, italic: bool
    ) -> tuple[tuple[int, int], ...]:
        """The dots of a character relative to the head, cached by style."""
        key = (
            glyph_source,
            step,
            offset,
            italic,
            self._script,
            self._emphasized,
            self._double_strike,
        )
        dots = self._glyph_cache.get(key)
        if dots is None:
            dots = tuple(self._style_dots(self._glyph(code), step, offset, italic))
            if glyph_source[0] != "user":
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
            if self._emphasized:
                passes.extend([(x + step // 2, y) for x, y in passes])
            if self._double_strike:
                passes.extend([(x, y + DOUBLE_STRIKE_OFFSET) for x, y in passes])
            yield from passes

    def _is_double_width(self) -> bool:
        return self._double_width or self._one_line_double_width

    def _underline_dots(self, width: int) -> list[tuple[int, int]]:
        y = self._y + (self._mechanism_rows() - 1) * self._mechanism.pin_pitch
        return [(self._x + x, y) for x in range(0, width, PROPORTIONAL_STEP)]

    def _mechanism_rows(self) -> int:
        return self._font.rows

    # -- Bit-image graphics -----------------------------------------------

    def _graphics(self, mode: int, columns: list[int], *, nine_pin: bool) -> None:
        step = GRAPHICS_STEP.get(mode)
        if step is None:
            logger.debug("ignoring graphics in unknown density %d", mode)
            return
        pin_pitch = self._mechanism.pin_pitch
        entry = _Entry(self._x)
        for index, pattern in enumerate(columns):
            x = self._x + index * step
            if x >= self._right_margin:
                break
            pins = 9 if nine_pin else 8
            for pin in range(pins):
                if pattern & (1 << (pins - 1 - pin)):
                    entry.dots.append((x, self._y + pin * pin_pitch))
        self._line.append(entry)
        self._x = min(self._x + len(columns) * step, self._right_margin)

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
            bottom = self._page_top + self._form_length - self._skip_perforation
            if self._page_top < bottom <= self._y < self._page_top + self._form_length:
                self._advance(self._page_top + self._form_length - self._y)

    def _advance(self, distance: int) -> None:
        self._y += distance
        while self._y >= self._page_top + self._form_length:
            self._eject_page()

    def _form_feed(self) -> None:
        self._print_line()
        self._x = self._left_margin
        self._one_line_double_width = False
        self._advance(self._page_top + self._form_length - self._y)

    def _vertical_tab(self) -> None:
        position = self._y - self._page_top
        below = [tab for tab in self._vertical_tabs if tab > position]
        if not self._vertical_tabs:
            self._line_feed()
        elif below:
            self._print_line()
            self._x = self._left_margin
            self._advance(below[0] - position)
        else:
            self._form_feed()

    def _horizontal_tab(self) -> None:
        following = [tab for tab in self._tabs if tab > self._x]
        if following and following[0] <= self._right_margin:
            self._line.append(_Entry(self._x))
            self._x = following[0]

    def _backspace(self) -> None:
        width = self._character_layout(0x20)[0]
        self._line.append(_Entry(self._x))
        self._x = max(self._left_margin, self._x - width)

    def _eject_page(self) -> None:
        mechanism = self._mechanism
        top, bottom = self._page_top, self._page_top + self._form_length
        on_page = [(x, y) for x, y in self._paper_dots if y < bottom]
        self._paper_dots = [(x, y) for x, y in self._paper_dots if y >= bottom]
        self._page_number += 1
        left = mechanism.left_offset
        self._completed.append(
            Page(
                number=self._page_number,
                width=mechanism.paper_width,
                height=self._form_length,
                dot_diameter=mechanism.dot_diameter,
                dots=tuple(
                    (left + x, y - top)
                    for x, y in on_page
                    if 0 <= left + x < mechanism.paper_width and y >= top
                ),
            )
        )
        self._page_top = bottom

    def _take_completed(self) -> list[Page]:
        completed, self._completed = self._completed, []
        return completed

    def _set_top_of_form(self) -> None:
        if not any(y >= self._page_top for _, y in self._paper_dots):
            self._page_top = self._y

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
            "/": self._esc_skip_argument,
            "0": setter("_line_spacing", inches(1) // 8),
            "1": setter("_line_spacing", inches(7) // 72),
            "2": setter("_line_spacing", inches(1) // 6),
            "3": self._esc_line_spacing_216,
            "A": self._esc_line_spacing_72,
            "J": self._esc_immediate_feed,
            "4": setter("_italic", True),
            "5": setter("_italic", False),
            "6": setter("_high_codes_printable", True),
            "7": setter("_high_codes_printable", False),
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
            "b": self._esc_vfu_channel,
            "i": self._esc_skip_argument,
            "p": self._esc_proportional,
            "s": self._esc_skip_argument,
        }

    @staticmethod
    def _flag(value: int) -> bool:
        """ESC/P accepts 0/1 or the ASCII digits '0'/'1' for on/off arguments."""
        return value in (1, ord("1"))

    def _esc_master_select(self) -> ArgumentReader:
        n = yield
        self._elite = bool(n & 0x01)
        self._proportional = bool(n & 0x02)
        self._condensed = bool(n & 0x04)
        self._emphasized = bool(n & 0x08)
        self._double_strike = bool(n & 0x10)
        self._double_width = bool(n & 0x20)
        self._italic = bool(n & 0x40)
        self._underline = bool(n & 0x80)

    def _esc_select_user_set(self) -> ArgumentReader:
        n = yield
        yield  # The FX-80 takes a second argument, always 0.
        self._user_set_selected = bool(n & 1)

    def _esc_define_user_characters(self) -> ArgumentReader:
        yield  # Always 0.
        first = yield
        last = yield
        for code in range(first, last + 1):
            attribute = yield
            columns = []
            for _ in range(11):
                columns.append((yield))
            top_row = 0 if attribute & 0x80 else 1
            dots = frozenset(
                (column, top_row + bit)
                for column, pattern in enumerate(columns)
                for bit in range(8)
                if pattern & (0x80 >> bit)
            )
            self._user_glyphs[code & 0x7F] = Glyph(dots)

    def _esc_copy_rom(self) -> ArgumentReader:
        for _ in range(3):
            yield
        self._user_glyphs.clear()

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
        self._line_spacing = (yield) * self._mechanism.pin_pitch

    def _esc_immediate_feed(self) -> ArgumentReader:
        n = yield
        self._print_line()
        self._advance(n * DOUBLE_STRIKE_OFFSET)

    def _esc_initialise(self) -> None:
        self._print_line()
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
        lines = yield from self._read_stops(16)
        self._vertical_tabs = [line * self._line_spacing for line in lines]

    def _esc_horizontal_tabs(self) -> ArgumentReader:
        columns = yield from self._read_stops(32)
        width = self._character_layout(0x20)[0]
        self._tabs = [column * width for column in columns]

    def _esc_vfu_channel(self) -> ArgumentReader:
        yield  # Channel number; channels other than 0 are not modelled.
        yield from self._esc_vertical_tabs()

    def _esc_form_length(self) -> ArgumentReader:
        n = yield
        if n == 0:
            inch_count = yield
            if inch_count:
                self._form_length = inches(inch_count)
        elif n:
            self._form_length = n * self._line_spacing
        self._set_top_of_form()

    def _esc_skip_perforation(self) -> ArgumentReader:
        self._skip_perforation = (yield) * self._line_spacing

    def _column_width(self) -> int:
        if self._elite:
            return ELITE_WIDTH
        if self._condensed:
            return CONDENSED_WIDTH
        return PICA_WIDTH

    def _esc_right_margin(self) -> ArgumentReader:
        n = yield
        right = n * self._column_width()
        if self._left_margin < right <= self._mechanism.columns * PICA_WIDTH:
            self._right_margin = right

    def _esc_left_margin(self) -> ArgumentReader:
        n = yield
        left = n * self._column_width()
        if left < self._right_margin:
            self._left_margin = left
            if self._x < left:
                self._x = left

    def _esc_character_set(self) -> ArgumentReader:
        n = yield
        try:
            self._character_set = CharacterSet(n)
        except ValueError:
            logger.debug("ignoring unknown international character set %d", n)

    def _esc_script(self) -> ArgumentReader:
        n = yield
        self._script = "subscript" if self._flag(n) else "superscript"

    def _esc_double_width(self) -> ArgumentReader:
        self._double_width = self._flag((yield))

    def _esc_proportional(self) -> ArgumentReader:
        self._proportional = self._flag((yield))
