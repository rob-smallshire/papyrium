"""lx800-draft meets the dot font contract and holds the LX-800's draft characters."""

from papyrium.core.conformance import DotFontConformance
from papyrium.extension import create_extension, namespace_for
from papyrium.font.lx800_draft import LX800DraftFont
from papyrium.language.escp.charsets import INTERNATIONAL_CHARACTERS


class TestLX800DraftConformance(DotFontConformance):
    # The ROM stores characters with dots in successive columns; the
    # printer, not the font, prints such a dot only once.
    allows_adjacent_dots = True

    def make_font(self):
        return LX800DraftFont(name="lx800-draft")


def _font():
    return LX800DraftFont(name="lx800-draft")


def test_is_registered_on_the_font_axis():
    font = create_extension("font", namespace_for("font"), "lx800-draft")
    assert (font.rows, font.columns) == (9, 11)


def test_covers_the_international_characters():
    assert set(INTERNATIONAL_CHARACTERS) <= _font().characters()


def test_has_a_slashed_zero():
    font = _font()
    assert font.glyph("0̸").dots != font.glyph("0").dots


def test_capitals_fill_rows_0_to_6_of_nine_columns():
    dots = _font().glyph("H").dots
    assert {row for _, row in dots} == set(range(7))
    assert {column for column, row in dots if row == 3} == set(range(9))


def test_descenders_print_a_pin_lower_onto_the_ninth_pin():
    font = _font()
    for character in "gpqy":
        rows = {row for _, row in font.glyph(character).dots}
        assert min(rows) == 2 and max(rows) == 8, character
    assert max(row for _, row in font.glyph("x").dots) == 6


def test_the_last_two_columns_are_left_for_spacing():
    font = _font()
    for character in font.characters():
        assert all(column < 9 for column, _ in font.glyph(character).dots), character
