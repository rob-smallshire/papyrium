"""CharacterGenerator: how a printer turns a glyph into dots.

The interpreter decides what to print and where; the character generator
decides which dots a glyph becomes in a given style: how italics lean,
how emphasized and double-strike repeat the dots, how near letter quality
lays out its two passes. Printers differ here, so a printer model supplies
its own generator through its mechanism. The defaults are the Epson
FX-80's.

Lengths are in page units (1/4320 inch).
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, replace

from papyrium.core.dotfont import Glyph
from papyrium.core.page import inches

#: Superscript and subscript rows are half the normal pin pitch apart.
SCRIPT_ROW_PITCH = inches(1) // 144

#: The baseline row of the character matrix, about which italics lean.
BASELINE_ROW = 6

#: Dot columns in a draft character's cell at fixed pitch.
CELL_COLUMNS = 12

#: Width of a proportional space, in proportional columns.
PROPORTIONAL_SPACE_COLUMNS = 10

#: The second pass of double-strike printing is this far below the first.
DOUBLE_STRIKE_OFFSET = inches(1) // 216

Dot = tuple[int, int]


@dataclass(frozen=True)
class CharacterStyle:
    """What decides a character's dots, apart from its glyph.

    *step* is the distance between the glyph's columns and *offset* moves
    the glyph that many columns right. *script* is "superscript",
    "subscript" or None.
    """

    step: int
    offset: int = 0
    italic: bool = False
    script: str | None = None
    emphasized: bool = False
    double_strike: bool = False
    double_width: bool = False


@dataclass(frozen=True)
class CharacterGenerator:
    """The Epson FX-80's character generator, the default for ESC/P printers.

    *prints_adjacent_dots_once*: a dot in the column after a printed one in
    the same row is not printed, since the head cannot fire a pin so soon:
    the ROM stores characters with such dots, and the printer prints them
    once. *nlq_emphasized*: near letter quality prints emphasized, rather
    than masking it. *nlq_pass_offset*: how far below the first NLQ pass
    the second prints.
    """

    prints_adjacent_dots_once: bool = False
    nlq_emphasized: bool = False
    nlq_pass_offset: int = DOUBLE_STRIKE_OFFSET

    def cell_columns(self, pitch: int) -> int:
        """The dot columns of a draft character's cell at fixed *pitch*, the
        cell's width: twelve, whatever the pitch."""
        return CELL_COLUMNS

    def proportional_cell(self, glyph: Glyph) -> tuple[int, int]:
        """The columns a character takes in proportional spacing, and how
        many columns its glyph moves right: its extent with a column of
        space either side, or a fixed width for a blank glyph."""
        if glyph.extent is None:
            return PROPORTIONAL_SPACE_COLUMNS, 0
        first, last = glyph.extent
        return last - first + 3, 1 - first

    def italic_offset(self, glyph: Glyph, row: int, step: int) -> int:
        """How far right italic moves *glyph*'s dots in *row*, its columns
        *step* apart: half a column for each row above the baseline, row 6."""
        return (BASELINE_ROW - row) * step // 2

    def draft_dots(self, glyph: Glyph, style: CharacterStyle, pin_pitch: int) -> list[Dot]:
        """The dots of a draft character, relative to the head."""
        if self.prints_adjacent_dots_once:
            glyph = printable_once(glyph)
        return list(self._draft_dots(glyph, style, pin_pitch))

    def _draft_dots(self, glyph: Glyph, style: CharacterStyle, pin_pitch: int) -> Iterable[Dot]:
        step = style.step
        for column, row in sorted(glyph.dots, key=lambda dot: (dot[1], dot[0])):
            dx = (column + style.offset) * step
            if style.italic:
                dx += self.italic_offset(glyph, row, step)
            if style.script == "superscript":
                dy = row * SCRIPT_ROW_PITCH
            elif style.script == "subscript":
                dy = 4 * pin_pitch + row * SCRIPT_ROW_PITCH
            else:
                dy = row * pin_pitch
            passes = [(dx, dy)]
            if style.double_width:
                # Enlarged characters strike every dot twice, side by side.
                passes.append((dx + step // 2, dy))
            if style.emphasized:
                passes.extend([(x + step // 2, y) for x, y in passes])
            if style.double_strike:
                passes.extend([(x, y + DOUBLE_STRIKE_OFFSET) for x, y in passes])
            yield from passes

    def nlq_dots(
        self, glyph: Glyph, columns: int, width: int, style: CharacterStyle, pin_pitch: int
    ) -> list[Dot]:
        """The dots of an NLQ character from a font of *columns* columns,
        which span its cell, *width* wide: the pins of the first pass on
        even rows, of the second, *nlq_pass_offset* lower, on odd rows.
        NLQ prints upright, italic or not."""
        step = width // columns
        result = []
        for column, row in sorted(glyph.dots, key=lambda dot: (dot[1], dot[0])):
            dx = column * step
            dy = (row // 2) * pin_pitch + (row % 2) * self.nlq_pass_offset
            passes = [(dx, dy)]
            if style.double_width:
                # Enlarged characters strike every dot twice, side by side.
                passes.append((dx + step // 2, dy))
            if style.emphasized and self.nlq_emphasized:
                passes.extend([(x + step, y) for x, y in passes])
            result.extend(passes)
        return result


def printable_once(glyph: Glyph) -> Glyph:
    """*glyph* without any dot that follows a printed dot in the same row."""
    printed: set[Dot] = set()
    for column, row in sorted(glyph.dots):
        if (column - 1, row) not in printed:
            printed.add((column, row))
    return replace(glyph, dots=frozenset(printed))
