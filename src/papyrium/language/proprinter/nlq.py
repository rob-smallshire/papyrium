"""The Proprinter's near letter quality, made from its draft characters.

The 9-wire Proprinters keep no NLQ characters of their own: they print a
draft character in two passes, the second half a dot lower, adding dots
between those the character gives (IBM Proprinter Family Technical
Reference, 4-3 to 4-7; ``docs/ibm-proprinter-ii.md``). A draft dot in
column c and row r becomes the NLQ dot in column 2c and row 2r, on a grid
of 1/240 inch columns and 1/144 inch rows, and the printer adds a dot
halfway between two dots in successive rows:

- of the same column, so that a vertical line prints solid;
- one or two columns apart, so that a diagonal fills in, unless either
  dot lies inside a line, with dots either side of it in its row or
  above and below it in its column: a diagonal meets a line only at the
  line's end.
"""

from __future__ import annotations

from dataclasses import replace

from papyrium.core.dotfont import Glyph

#: The NLQ grid's columns and rows to a draft character's.
NLQ_SCALE = 2

#: How many columns left or right a dot in the next row may be for the
#: printer to add a dot between them on a diagonal.
DIAGONAL_NEIGHBOURS = (-2, -1, 1, 2)


def nlq_from_draft(glyph: Glyph) -> Glyph:
    """The NLQ glyph the Proprinter prints for the draft *glyph*: every dot
    the draft character gives, horizontal lines included, and the dots
    the printer adds between them."""
    draft = glyph.dots

    def inside_line(column: int, row: int) -> bool:
        horizontal = (column - 1, row) in draft and (column + 1, row) in draft
        vertical = (column, row - 1) in draft and (column, row + 1) in draft
        return horizontal or vertical

    dots = set()
    for column, row in draft:
        dots.add((2 * column, 2 * row))
        if (column, row + 1) in draft:
            dots.add((2 * column, 2 * row + 1))
        if inside_line(column, row):
            continue
        for neighbour in DIAGONAL_NEIGHBOURS:
            below = (column + neighbour, row + 1)
            if below in draft and not inside_line(*below):
                dots.add((2 * column + neighbour, 2 * row + 1))
    span = None if glyph.span is None else (2 * glyph.span[0], 2 * glyph.span[1])
    return replace(glyph, dots=frozenset(dots), span=span)
