"""The GLP's fonts meet the dot font contract and hold the GLP's characters."""

import pytest

from papyrium.core.conformance import DotFontConformance
from papyrium.extension import create_extension, namespace_for
from papyrium.font.glp import GlpDraftFont, GlpGraphicsFont, GlpNlqFont

ASCII = "".join(chr(code) for code in range(0x20, 0x7F))
GERMAN = "§ÄÖÜäöüß"
DESCENDERS = ";_gpqy"


class TestGlpDraftConformance(DotFontConformance):
    def make_font(self):
        return GlpDraftFont(name="glp-draft")


class TestGlpNlqConformance(DotFontConformance):
    def make_font(self):
        return GlpNlqFont(name="glp-nlq")


class TestGlpGraphicsConformance(DotFontConformance):
    def make_font(self):
        return GlpGraphicsFont(name="glp-graphics")

    def test_covers_printable_ascii(self):
        # Graphics only: the other characters come from the draft font.
        pass

    def test_space_is_blank(self):
        pass


@pytest.mark.parametrize(
    ("name", "font_class"),
    [
        ("glp-draft", GlpDraftFont),
        ("glp-graphics", GlpGraphicsFont),
        ("glp-nlq", GlpNlqFont),
    ],
)
def test_is_registered_on_the_font_axis(name, font_class):
    assert isinstance(create_extension("font", namespace_for("font"), name), font_class)


def test_draft_covers_ascii_and_the_german_set():
    font = GlpDraftFont(name="glp-draft")
    assert font.rows == 9
    for character in ASCII + GERMAN:
        assert font.glyph(character) is not None, character


def test_only_the_firmwares_descenders_sit_a_pin_lower():
    font = GlpDraftFont(name="glp-draft")
    reaching_the_ninth_pin = {
        character
        for character in ASCII + GERMAN
        if 8 in {row for _, row in font.glyph(character).dots}
    }
    assert reaching_the_ninth_pin == set("_gpqy")
    assert 0 not in {row for _, row in font.glyph(";").dots}


def test_graphics_cover_the_cpc_codes_129_to_255():
    font = GlpGraphicsFont(name="glp-graphics")
    for character in "▘█┼αΩ☺♠⭤\U0001fbc5":
        assert font.glyph(character) is not None, character


def test_a_full_block_joins_its_neighbours():
    glyph = GlpGraphicsFont(name="glp-graphics").glyph("█")
    assert glyph.dots == frozenset((column, row) for column in range(0, 11, 2) for row in range(8))


def test_nlq_covers_ascii_and_the_german_set_in_two_passes():
    font = GlpNlqFont(name="glp-nlq")
    assert (font.rows, font.columns) == (18, 39)
    for character in ASCII + GERMAN:
        assert font.glyph(character) is not None, character


def test_nlq_lowers_the_firmwares_descenders_a_pin():
    font = GlpNlqFont(name="glp-nlq")

    def top(character):
        return min(row for _, row in font.glyph(character).dots)

    assert top("g") == top("a") == 4
    assert top("y") == top("x")
