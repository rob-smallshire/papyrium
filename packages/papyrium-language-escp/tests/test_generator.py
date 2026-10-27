"""The default character generator: the Epson FX-80's rules."""

from papyrium.core.dotfont import Glyph
from papyrium.core.page import inches
from papyrium.language.escp.generator import (
    DOUBLE_STRIKE_OFFSET,
    CharacterGenerator,
    CharacterStyle,
    printable_once,
)

PIN = inches(1) // 72
STEP = inches(1) // 120
GENERATOR = CharacterGenerator()


def _draft(dots, **style):
    return GENERATOR.draft_dots(Glyph(frozenset(dots)), CharacterStyle(step=STEP, **style), PIN)


def test_a_dot_lies_at_its_column_and_row():
    assert _draft({(2, 3)}) == [(2 * STEP, 3 * PIN)]


def test_italics_lean_half_a_column_a_row_about_row_6():
    assert _draft({(0, 0), (0, 6), (0, 8)}, italic=True) == [
        (3 * STEP, 0),
        (0, 6 * PIN),
        (-STEP, 8 * PIN),
    ]


def test_emphasized_repeats_each_dot_half_a_column_right():
    assert _draft({(0, 0)}, emphasized=True) == [(0, 0), (STEP // 2, 0)]


def test_double_strike_repeats_each_dot_1_216_inch_lower():
    assert _draft({(0, 0)}, double_strike=True) == [(0, 0), (0, DOUBLE_STRIKE_OFFSET)]


def test_nlq_passes_fall_on_alternate_rows_1_216_inch_apart():
    glyph = Glyph(frozenset({(0, 0), (0, 1), (0, 2)}))
    dots = GENERATOR.nlq_dots(glyph, 24, inches(1) // 10, CharacterStyle(step=0), PIN)
    assert dots == [(0, 0), (0, DOUBLE_STRIKE_OFFSET), (0, PIN)]


def test_printable_once_drops_a_dot_that_follows_a_printed_one():
    glyph = Glyph(frozenset({(0, 0), (1, 0), (2, 0)}), span=(0, 4))
    assert printable_once(glyph) == Glyph(frozenset({(0, 0), (2, 0)}), span=(0, 4))


def test_a_proportional_cell_is_the_extent_with_a_column_either_side():
    assert GENERATOR.proportional_cell(Glyph(frozenset({(2, 0), (5, 3)}))) == (6, -1)
    assert GENERATOR.proportional_cell(Glyph(frozenset({(2, 0)}), span=(0, 4))) == (7, 1)


def test_a_blank_proportional_cell_is_ten_columns():
    assert GENERATOR.proportional_cell(Glyph(frozenset())) == (10, 0)


def test_a_printer_may_space_its_nlq_passes_otherwise():
    generator = CharacterGenerator(nlq_pass_offset=inches(1) // 144)
    glyph = Glyph(frozenset({(1, 1)}))
    dots = generator.nlq_dots(glyph, 24, inches(1) // 10, CharacterStyle(step=0), PIN)
    assert dots == [(inches(1) // 240, inches(1) // 144)]


def test_an_nlq_fonts_columns_span_its_cell():
    glyph = Glyph(frozenset({(1, 0)}))
    dots = GENERATOR.nlq_dots(glyph, 20, inches(1) // 12, CharacterStyle(step=0), PIN)
    assert dots == [(inches(1) // 240, 0)]


def test_a_draft_cell_is_twelve_columns_at_every_pitch():
    assert {GENERATOR.cell_columns(inches(1) // n) for n in (10, 12, 20)} == {12}
