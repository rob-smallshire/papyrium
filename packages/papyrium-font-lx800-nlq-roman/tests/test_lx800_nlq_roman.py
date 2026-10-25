"""lx800-nlq-roman meets the dot font contract and holds the LX-800's NLQ Roman."""

from papyrium.core.conformance import DotFontConformance
from papyrium.extension import create_extension, namespace_for
from papyrium.font.lx800_nlq_roman import LX800NlqRomanFont
from papyrium.language.escp.charsets import INTERNATIONAL_CHARACTERS


class TestLX800NlqRomanConformance(DotFontConformance):
    allows_adjacent_dots = True

    def make_font(self):
        return LX800NlqRomanFont(name="lx800-nlq-roman")


def _font():
    return LX800NlqRomanFont(name="lx800-nlq-roman")


def test_is_registered_on_the_font_axis():
    font = create_extension("font", namespace_for("font"), "lx800-nlq-roman")
    assert (font.rows, font.columns) == (18, 24)


def test_covers_the_international_characters():
    assert set(INTERNATIONAL_CHARACTERS) <= _font().characters()


def test_both_passes_print():
    rows = {row for _, row in _font().glyph("H").dots}
    assert any(row % 2 == 0 for row in rows) and any(row % 2 == 1 for row in rows)


def test_most_characters_lie_on_whole_columns():
    # Columns are 1/240 inch; most characters are drawn at 1/120 inch.
    assert all(column % 2 == 0 for column, _ in _font().glyph("H").dots)


def test_diagonals_use_the_half_columns():
    assert any(column % 2 == 1 for column, _ in _font().glyph("A").dots)


def test_descenders_reach_the_ninth_pin():
    font = _font()
    for character in "gpqy,":
        assert max(row for _, row in font.glyph(character).dots) >= 16, character
    assert max(row for _, row in font.glyph("H").dots) < 16
