"""The Proprinter's near letter quality, made from its draft characters.

The 9-wire Proprinters keep no NLQ characters of their own: they print a
draft character in two passes, the second half a dot lower, adding dots
between those the character gives (IBM Proprinter Family Technical
Reference, 4-3 to 4-7; ``docs/ibm-proprinter-ii.md``). A draft dot in
column c and row r becomes the NLQ dot in column 2c and row 2r, on a grid
of 1/240 inch columns and 1/144 inch rows, and the printer adds:

- between two dots in successive rows of a column, one halfway between
  them, so a vertical line prints solid;
- between two dots in successive rows of neighbouring columns, one
  halfway between them, so a diagonal fills in, unless either dot lies
  inside a horizontal line, with dots either side of it in its row: the
  meeting of a diagonal and a horizontal line is left as it is.
"""

from __future__ import annotations

from dataclasses import replace

from papyrium.core.dotfont import Glyph

#: The NLQ grid's columns and rows to a draft character's.
NLQ_SCALE = 2


def nlq_from_draft(glyph: Glyph) -> Glyph:
    """The NLQ glyph the Proprinter prints for the draft *glyph*: every dot
    the draft character gives, horizontal lines included, and the dots
    the printer adds between them."""
    draft = glyph.dots

    def inside_horizontal_line(column: int, row: int) -> bool:
        return (column - 1, row) in draft and (column + 1, row) in draft

    dots = set()
    for column, row in draft:
        dots.add((2 * column, 2 * row))
        if (column, row + 1) in draft:
            dots.add((2 * column, 2 * row + 1))
        for neighbour in (column - 1, column + 1):
            if (neighbour, row + 1) not in draft:
                continue
            if inside_horizontal_line(column, row) or inside_horizontal_line(neighbour, row + 1):
                continue
            dots.add((column + neighbour, 2 * row + 1))
    span = None if glyph.span is None else (2 * glyph.span[0], 2 * glyph.span[1])
    return replace(glyph, dots=frozenset(dots), span=span)
