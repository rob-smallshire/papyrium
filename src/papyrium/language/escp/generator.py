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
    than masking it. *double_strike_offset*: how far below the first pass
    of double-strike the second prints. *nlq_pass_offset*: how far below
    the first NLQ pass the second prints. *nlq_underline_second_pass*: NLQ
    underlines in its second pass, *nlq_pass_offset* below draft's
    underline, rather than in its first. *nlq_cell_columns*: how many NLQ
    columns span a character's cell, where it is not the font's columns,
    which then leave some of the cell blank; None for the font's.
    *nlq_double_width_pairs*: enlarged NLQ prints each pair of columns as
    one, the even column's place, rather than striking every dot twice.
    """

    prints_adjacent_dots_once: bool = False
    nlq_emphasized: bool = False
    double_strike_offset: int = DOUBLE_STRIKE_OFFSET
    nlq_pass_offset: int = DOUBLE_STRIKE_OFFSET
    nlq_underline_second_pass: bool = False
    nlq_cell_columns: int | None = None
    nlq_double_width_pairs: bool = False

    def nlq_columns(self, font_columns: int) -> int:
        """The NLQ columns that span a character's cell, from a font of *font_columns*."""
        return font_columns if self.nlq_cell_columns is None else self.nlq_cell_columns

    def user_proportional_cell(self, first: int, last: int) -> tuple[int, int]:
        """The columns a download character takes in proportional spacing,
        from its attribute's *first* and *last* columns, and how many its
        glyph moves right: those columns exactly."""
        return last - first + 1, -first

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

    def nlq_proportional_cell(self, glyph: Glyph) -> tuple[int, int] | None:
        """The columns an NLQ character takes in proportional spacing, and
        how many its glyph moves right; None where NLQ keeps to its fixed
        cell, as here."""
        return None

    def nlq_italic_offset(self, glyph: Glyph, row: int, step: int) -> int:
        """How far right italic moves an NLQ *glyph*'s dots in *row*, its
        columns *step* apart: not at all, NLQ printing upright."""
        return 0

    def enlarged_dots(
        self, glyph: Glyph, step: int, width_scale: int, height_scale: int, pin_pitch: int
    ) -> list[Dot]:
        """The dots of an enlarged NLQ character, its columns *step* apart.

        Each of the glyph's rows, half a pin apart, becomes *height_scale* / 2
        rows of pins, and each column *width_scale* columns, as the Star
        LC-10 enlarges them: it sends each column, ORed with the one before
        it, *width_scale* / 2 times every other column, so a column's dots
        repeat every other column across its own place and the next's.
        """
        result = []
        pins = max(1, height_scale // 2)
        repeats = range(0, 2 * width_scale - 1, 2) if width_scale > 1 else (0,)
        for column, row in sorted(glyph.dots, key=lambda dot: (dot[1], dot[0])):
            for pin in range(pins):
                dy = (row * pins + pin) * pin_pitch
                for repeat in repeats:
                    result.append(((column * width_scale + repeat) * step, dy))
        return result

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
                passes.extend([(x, y + self.double_strike_offset) for x, y in passes])
            yield from passes

    def nlq_dots(
        self, glyph: Glyph, columns: int, width: int, style: CharacterStyle, pin_pitch: int
    ) -> list[Dot]:
        """The dots of an NLQ character from a font of *columns* columns,
        which span its cell, *width* wide: the pins of the first pass on
        even rows, of the second, *nlq_pass_offset* lower, on odd rows."""
        step = width // columns
        result = []
        dots = glyph.dots
        if style.double_width and self.nlq_double_width_pairs:
            dots = frozenset((column - column % 2, row) for column, row in dots)
        for column, row in sorted(dots, key=lambda dot: (dot[1], dot[0])):
            dx = (column + style.offset) * step
            if style.italic:
                dx += self.nlq_italic_offset(glyph, row, step)
            dy = (row // 2) * pin_pitch + (row % 2) * self.nlq_pass_offset
            passes = [(dx, dy)]
            if style.double_width and not self.nlq_double_width_pairs:
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
