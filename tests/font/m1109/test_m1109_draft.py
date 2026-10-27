"""m1109-draft meets the dot font contract and covers what the M-1109 prints."""

from papyrium.core.conformance import DotFontConformance
from papyrium.extension import create_extension, namespace_for
from papyrium.font.m1109 import M1109DraftFont
from papyrium.language.escp.charsets import INTERNATIONAL_CHARACTERS


class TestM1109DraftConformance(DotFontConformance):
    def make_font(self):
        return M1109DraftFont(name="m1109-draft")


def test_is_registered_on_the_font_axis():
    font = create_extension("font", namespace_for("font"), "m1109-draft")
    assert (font.rows, font.columns) == (9, 11)


def test_covers_the_international_characters():
    font = M1109DraftFont(name="m1109-draft")
    assert set(INTERNATIONAL_CHARACTERS) <= font.characters()


def test_has_a_slashed_zero():
    font = M1109DraftFont(name="m1109-draft")
    assert font.glyph("0̸").dots > font.glyph("0").dots


def test_capitals_sit_on_row_6_and_descenders_reach_row_8():
    font = M1109DraftFont(name="m1109-draft")
    assert max(row for _, row in font.glyph("H").dots) == 6
    assert max(row for _, row in font.glyph("g").dots) == 8
    assert min(row for _, row in font.glyph("x").dots) == 2
