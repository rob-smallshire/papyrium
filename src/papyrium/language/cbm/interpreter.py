"""CbmInterpreter: a Commodore printer's job, as the MPS-803's firmware prints it.

The firmware is read in docs/commodore-mps-803-firmware.md; each rule
here names the routine it follows.
"""

from __future__ import annotations

import logging
from collections.abc import Generator
from dataclasses import dataclass, field

from papyrium.core.dotfont import Glyph
from papyrium.core.model import Interpreter
from papyrium.core.page import Page, TextMark, inches
from papyrium.language.cbm.charset import business_glyph, glyph_character, graphic_glyph
from papyrium.language.cbm.mechanism import CbmMechanism

logger = logging.getLogger(__name__)

BS, LF, CR, SO, SI, POS, DOWN, RVS_ON, SUB, ESC = 8, 10, 13, 14, 15, 16, 17, 18, 26, 27
UP, RVS_OFF, QUOTE = 0x91, 0x92, 0x22

#: Dots across the line, 1/60 inch apart.
LINE_DOTS = 480
#: A character cell, in dots.
CELL_DOTS = 6
#: The dot pitch across the line, and the wires' pitch down it.
DOT_STEP = inches(1) // 60
WIRE_PITCH = inches(1) // 72
#: Rows the head prints: wires 1-7; the firmware never fires wire 8.
ROWS = 7
#: The paper feeds in steps of 1/216 inch; a line printed in bit image
#: feeds 21, 7/72 inch.
FEED_STEP = inches(1) // 216
BIT_IMAGE_FEED_STEPS = 21

ArgumentReader = Generator[None, int, None]


@dataclass
class _Item:
    """Something on the line: dots and, for a character, its text."""

    x: int
    dots: list[tuple[int, int]] = field(default_factory=list)
    mark: TextMark | None = None


class CbmInterpreter(Interpreter):
    """Interprets a Commodore printer's job into pages, as the MPS-803 prints it.

    A line is buffered and printed on CR or LF, or when the next item will
    not fit (`advance`, $07C7): characters six dots wide (twelve double
    width), bit-image columns one dot, on a line of 480 dots 1/60 inch
    apart, seven wires 1/72 inch apart.
    """

    def __init__(self, mechanism: CbmMechanism) -> None:
        self._mechanism = mechanism
        self._font = mechanism.font
        self._pages: list[Page] = []
        self._page_number = 0
        self._paper_y = mechanism.top_offset
        self._sheet_top = 0
        self._printed: list[_Item] = []
        self._line: list[_Item] = []
        self._position = 0
        self._pending_move = 0
        self._double_width = False
        self._bit_image = False
        self._reverse = False
        self._quote = False
        self._line_set_business: bool | None = None
        self._machine = self._run()
        next(self._machine)

    # -- The Interpreter interface -----------------------------------------

    def feed(self, data: bytes) -> list[Page]:
        for byte in data:
            self._machine.send(byte)
        return self._take_pages()

    def finish(self) -> list[Page]:
        if self._line:
            self._end_line()
        self._eject_all()
        return self._take_pages()

    # -- Bytes (`interpret`, $0256) ------------------------------------------

    def _run(self) -> ArgumentReader:
        while True:
            byte = yield
            if self._bit_image:
                if byte & 0x80:
                    self._column(byte)
                elif byte < 0x20:
                    yield from self._control(byte)
                # $20-$7F are ignored in bit image.
                continue
            if byte == CR:
                self._carriage_return()
            elif self._quote:
                self._quoted(byte)
            elif byte == UP:
                self._line_set_business = False
            elif byte == RVS_OFF:
                self._reverse = False
            elif byte < 0x20:
                yield from self._control(byte)
            elif 0x80 <= byte < 0xA0:
                pass
            else:
                self._character(byte, reversed_=self._reverse)
                if byte == QUOTE:
                    self._quote = not self._quote

    def _control(self, code: int) -> ArgumentReader:
        """The control codes, through the table at $036C; others are ignored."""
        if code == BS:
            self._pending_move = 0
            self._bit_image = True
        elif code in (LF, CR):
            self._carriage_return()
        elif code == SO:
            self._pending_move = 0
            self._double_width = True
            self._bit_image = False
        elif code == SI:
            self._pending_move = 0
            self._double_width = False
            self._bit_image = False
        elif code == POS:
            tens = yield
            units = yield
            column = 10 * (tens & 15) + (units & 15)
            if column < LINE_DOTS // CELL_DOTS:
                self._move_to(column * CELL_DOTS)
        elif code == DOWN:
            if not self._bit_image:
                self._line_set_business = True
        elif code == RVS_ON:
            if not self._bit_image:
                self._reverse = True
        elif code == SUB:
            if self._bit_image:
                count = yield
                column = yield
                if column & 0x80:
                    self._repeat(count or 256, column)
        elif code == ESC:
            if (yield) == POS:
                high = yield
                low = yield
                dot = (high & 1) * 256 + low
                if dot < LINE_DOTS:
                    self._move_to(dot)

    # -- Characters ------------------------------------------------------------

    def _is_business(self) -> bool:
        if self._line_set_business is not None:
            return self._line_set_business
        return self._mechanism.business_set

    def _glyph_index(self, code: int) -> int:
        return business_glyph(code) if self._is_business() else graphic_glyph(code)

    def _quoted(self, byte: int) -> None:
        """Quote mode: every byte but CR prints, the controls as reversed glyphs."""
        if byte < 0x20:
            self._character(byte + 0x40, reversed_=True)
        elif 0x80 <= byte < 0xA0:
            self._character(byte + 0x40, reversed_=True)
        else:
            self._character(byte, reversed_=self._reverse)
            if byte == QUOTE:
                self._quote = False

    def _character(self, code: int, *, reversed_: bool) -> None:
        width = CELL_DOTS * (2 if self._double_width else 1)
        if not self._advance(width):
            return
        glyph_index = self._glyph_index(code)
        character = glyph_character(glyph_index) or " "
        glyph = self._font.glyph(character) or Glyph(frozenset())
        x = self._position - width
        item = _Item(x)
        repeat = 2 if self._double_width else 1
        for column in range(CELL_DOTS * repeat):
            source = column // repeat
            for row in range(ROWS):
                inked = (source, row) in glyph.dots
                if inked != reversed_:
                    item.dots.append((x + column, row))
        item.mark = TextMark(
            x=x * DOT_STEP,
            y=0,
            width=width * DOT_STEP,
            height=ROWS * WIRE_PITCH,
            character=character,
        )
        self._line.append(item)

    # -- Bit image ---------------------------------------------------------

    def _column(self, byte: int) -> None:
        if self._advance(1):
            self._line.append(_Item(self._position - 1, _column_dots(self._position - 1, byte)))

    def _repeat(self, count: int, byte: int) -> None:
        """SUB: *count* copies of a column, split at the margin ($0808)."""
        while count:
            self._apply_pending_move()
            room = LINE_DOTS - self._position
            if room <= 0:
                self._wrap()
                continue
            run = min(count, room)
            start = self._position
            item = _Item(start)
            for column in range(run):
                item.dots.extend(_column_dots(start + column, byte))
            self._line.append(item)
            self._position += run
            count -= run

    # -- The line ----------------------------------------------------------

    def _move_to(self, dot: int) -> None:
        """POS and ESC POS: a forward move, pending until the next item (`set_position`)."""
        if self._position >= LINE_DOTS:
            self._wrap()
        self._pending_move = max(0, dot - self._position)

    def _apply_pending_move(self) -> None:
        self._position += self._pending_move
        self._pending_move = 0

    def _advance(self, width: int) -> bool:
        """Make room for an item *width* dots wide, wrapping when it will
        not fit; whether there is room for it at all."""
        self._apply_pending_move()
        if self._position + width > LINE_DOTS:
            self._wrap()
            if width > LINE_DOTS:
                return False
        self._position += width
        return True

    def _wrap(self) -> None:
        """Print the line and start the next at dot 0, keeping the modes (`wrap_line`)."""
        self._print_line()
        self._position = 0
        self._pending_move = 0

    def _carriage_return(self) -> None:
        """CR and LF alike: print, feed, and end reverse, quote mode and the
        line's own set ($0421)."""
        self._print_line()
        self._position = 0
        self._pending_move = 0
        self._reverse = False
        self._quote = False
        if not self._bit_image:
            self._line_set_business = None

    def _end_line(self) -> None:
        self._print_line()

    def _print_line(self) -> None:
        """Lay the line on the paper and feed: 7/72 inch after bit image,
        else the spacing the switch sets."""
        for item in self._line:
            item.dots = [(x, self._paper_y + row * WIRE_PITCH) for x, row in item.dots]
            if item.mark is not None:
                item.mark = TextMark(
                    x=item.mark.x,
                    y=self._paper_y,
                    width=item.mark.width,
                    height=item.mark.height,
                    character=item.mark.character,
                )
            self._printed.append(item)
        self._line.clear()
        steps = BIT_IMAGE_FEED_STEPS if self._bit_image else self._mechanism.line_feed_steps
        self._paper_y += steps * FEED_STEP
        while self._paper_y >= self._sheet_top + self._mechanism.sheet_length:
            self._eject_page()

    # -- Pages -------------------------------------------------------------

    def _eject_page(self) -> None:
        mechanism = self._mechanism
        top = self._sheet_top
        bottom = top + mechanism.sheet_length
        dots = []
        text = []
        kept = []
        for item in self._printed:
            on = [(x, y) for x, y in item.dots if y < bottom]
            later = [(x, y) for x, y in item.dots if y >= bottom]
            dots.extend((mechanism.left_offset + x * DOT_STEP, y - top) for x, y in on)
            if item.mark is not None and top <= item.mark.y < bottom:
                mark = item.mark
                text.append(
                    TextMark(
                        x=mechanism.left_offset + mark.x,
                        y=mark.y - top,
                        width=mark.width,
                        height=mark.height,
                        character=mark.character,
                    )
                )
                item.mark = None
            if later or item.mark is not None:
                item.dots = later
                kept.append(item)
        self._printed = kept
        self._page_number += 1
        self._pages.append(
            Page(
                number=self._page_number,
                width=mechanism.paper_width,
                height=mechanism.sheet_length,
                dot_diameter=mechanism.dot_diameter,
                stationery=mechanism.stationery,
                dots=tuple(dots),
                text=tuple(text),
            )
        )
        self._sheet_top = bottom

    def _eject_all(self) -> None:
        while self._printed:
            self._eject_page()

    def _take_pages(self) -> list[Page]:
        pages, self._pages = self._pages, []
        return pages


def _column_dots(x: int, byte: int) -> list[tuple[int, int]]:
    """A bit-image column: bit 0 the top wire, bit 6 the seventh; bit 7 marks it."""
    return [(x, row) for row in range(ROWS) if byte & (1 << row)]
