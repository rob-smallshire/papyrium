"""The LC-10's character generator, as its firmware forms characters."""

import pytest

from papyrium.core.dotfont import Glyph
from papyrium.core.page import inches
from papyrium.language.escp.generator import CharacterStyle
from papyrium.model.star_lc10.generator import LC10CharacterGenerator

PIN = inches(1) // 72
DRAFT_STEP = inches(1) // 120
NLQ_STEP = inches(1) // 240
GENERATOR = LC10CharacterGenerator()


@pytest.mark.parametrize(
    "pitch, columns",
    [(inches(1) // 10, 12), (inches(1) // 12, 10), (252, 14), (inches(1) // 20, 12)],
)
def test_draft_cells_are_twelve_ten_fourteen_and_twelve_columns(pitch, columns):
    assert GENERATOR.cell_columns(pitch) == columns


def test_nlq_passes_are_half_a_dot_apart():
    glyph = Glyph(frozenset({(0, 1)}))
    assert GENERATOR.nlq_dots(glyph, 24, inches(1) // 10, CharacterStyle(step=0), PIN) == [
        (0, inches(1) // 144)
    ]


def _italic(rows, lowered=False):
    glyph = Glyph(frozenset((0, row) for row in rows), lowered=lowered)
    dots = GENERATOR.draft_dots(glyph, CharacterStyle(step=DRAFT_STEP, italic=True), PIN)
    return {row: dx // DRAFT_STEP for dx, row in ((x, y // PIN) for x, y in dots)}


def test_draft_italic_moves_each_pair_of_pins_a_column_further_up_the_byte():
    assert _italic(range(8)) == {0: 3, 1: 3, 2: 2, 3: 2, 4: 1, 5: 1, 6: 0, 7: 0}


def test_draft_italic_slants_a_lowered_character_about_its_own_byte():
    assert _italic(range(1, 9), lowered=True) == {1: 3, 2: 3, 3: 2, 4: 2, 5: 1, 6: 1, 7: 0, 8: 0}


def test_nlq_italic_moves_each_pin_a_column_further_up_the_pass():
    glyph = Glyph(frozenset({(0, 0), (0, 1), (0, 14), (0, 15)}))
    style = CharacterStyle(step=0, italic=True)
    dots = GENERATOR.nlq_dots(glyph, 24, inches(1) // 10, style, PIN)
    assert sorted(x // NLQ_STEP for x, _ in dots) == [0, 0, 7, 7]


def test_nlq_italic_slants_a_lowered_character_about_its_own_pass():
    glyph = Glyph(frozenset({(0, 2), (0, 17)}), lowered=True)
    style = CharacterStyle(step=0, italic=True)
    dots = GENERATOR.nlq_dots(glyph, 24, inches(1) // 10, style, PIN)
    assert sorted(x // NLQ_STEP for x, _ in dots) == [0, 7]


def test_a_proportional_draft_character_is_its_span_flush_left_and_two_columns():
    assert GENERATOR.proportional_cell(Glyph(frozenset({(3, 0)}), span=(1, 7))) == (9, -1)


def test_double_strike_repeats_each_dot_half_a_dot_lower():
    glyph = Glyph(frozenset({(0, 0)}))
    dots = GENERATOR.draft_dots(glyph, CharacterStyle(step=DRAFT_STEP, double_strike=True), PIN)
    assert dots == [(0, 0), (0, inches(1) // 144)]
