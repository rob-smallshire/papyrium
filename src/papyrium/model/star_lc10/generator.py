"""LC10CharacterGenerator: how the Star LC-10's firmware forms characters.

Taken from the LC-10 Colour's firmware, version 1.5; see
docs/star-lc10-firmware.md.
"""

from __future__ import annotations

from dataclasses import dataclass

from papyrium.core.dotfont import Glyph
from papyrium.core.page import inches
from papyrium.language.escp.generator import CharacterGenerator

#: Dot columns of a draft cell at each fixed pitch: pica and elite on a
#: 1/120 inch grid, condensed pica and condensed elite on 1/240 inch.
_CELL_COLUMNS = {
    inches(1) // 10: 12,
    inches(1) // 12: 10,
    inches(7) // 120: 14,
    inches(1) // 20: 12,
}

#: Blank columns after a proportional draft character, and after a
#: proportional NLQ one.
_PROPORTIONAL_GAP = 2
_NLQ_PROPORTIONAL_GAP = 4


@dataclass(frozen=True)
class LC10CharacterGenerator(CharacterGenerator):
    """The Star LC-10's character generator.

    The second pass of NLQ and of double-strike prints half a dot, 1/144
    inch, below the first, and NLQ's underline is in its second pass.
    Italic shears each column byte: the two lowest pins stay and each pair
    above moves one more column right in draft, each pin one more column in
    NLQ, so a lowered character slants about its own byte.
    """

    double_strike_offset: int = inches(1) // 144
    nlq_pass_offset: int = inches(1) // 144
    nlq_underline_second_pass: bool = True

    def cell_columns(self, pitch: int) -> int:
        return _CELL_COLUMNS.get(pitch, super().cell_columns(pitch))

    def italic_offset(self, glyph: Glyph, row: int, step: int) -> int:
        bit = 7 - (row - glyph.lowered)
        return (bit // 2) * step

    def nlq_italic_offset(self, glyph: Glyph, row: int, step: int) -> int:
        bit = 7 - (row - 2 * glyph.lowered) // 2
        return bit * step

    def proportional_cell(self, glyph: Glyph) -> tuple[int, int]:
        """A proportional draft character is its span, printed flush left,
        and two blank columns."""
        if glyph.extent is None:
            return super().proportional_cell(glyph)
        first, last = glyph.extent
        return last - first + 1 + _PROPORTIONAL_GAP, -first

    def user_proportional_cell(self, first: int, last: int) -> tuple[int, int]:
        """A proportional download character is its columns from first to
        last, the last taken as the cell's end when it is column 11, and two
        blank columns."""
        columns = last - first + (0 if last == 11 else 1)
        return columns + _PROPORTIONAL_GAP, -first

    def nlq_proportional_cell(self, glyph: Glyph) -> tuple[int, int] | None:
        """A proportional NLQ character is its span, printed flush left
        without its left and right space, and four blank columns."""
        if glyph.extent is None:
            return None
        first, last = glyph.extent
        return last - first + 1 + _NLQ_PROPORTIONAL_GAP, -first
