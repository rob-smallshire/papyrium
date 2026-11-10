"""The KX-P1080U's fonts meet the dot font contract and hold its characters."""

import pytest

from papyrium.core.conformance import DotFontConformance
from papyrium.extension import create_extension, namespace_for
from papyrium.font.kx_p1080 import (
    KXP1080DraftFont,
    KXP1080DraftItalicFont,
    KXP1080NlqFont,
    KXP1080NlqItalicFont,
)
from papyrium.language.escp.charsets import INTERNATIONAL_CHARACTERS

FONTS = {
    "kx-p1080-draft": (KXP1080DraftFont, 9, 12),
    "kx-p1080-draft-italic": (KXP1080DraftItalicFont, 9, 12),
    "kx-p1080-nlq": (KXP1080NlqFont, 18, 24),
    "kx-p1080-nlq-italic": (KXP1080NlqItalicFont, 18, 24),
}


class TestDraftConformance(DotFontConformance):
    # A few characters in the ROM have a dot in successive columns.
    allows_adjacent_dots = True

    def make_font(self):
        return KXP1080DraftFont(name="kx-p1080-draft")


class TestDraftItalicConformance(DotFontConformance):
    allows_adjacent_dots = True

    def make_font(self):
        return KXP1080DraftItalicFont(name="kx-p1080-draft-italic")


class TestNlqConformance(DotFontConformance):
    def make_font(self):
        return KXP1080NlqFont(name="kx-p1080-nlq")


class TestNlqItalicConformance(DotFontConformance):
    allows_adjacent_dots = True

    def make_font(self):
        return KXP1080NlqItalicFont(name="kx-p1080-nlq-italic")


def _font(name):
    return FONTS[name][0](name=name)


def _rows(font, character):
    return {row for _, row in font.glyph(character).dots}


@pytest.mark.parametrize("name", FONTS)
def test_is_registered_on_the_font_axis(name):
    font = create_extension("font", namespace_for("font"), name)
    assert (font.rows, font.columns) == FONTS[name][1:]


@pytest.mark.parametrize("name", FONTS)
def test_covers_ascii_the_international_characters_and_the_slashed_zero(name):
    characters = _font(name).characters()
    assert {chr(code) for code in range(0x20, 0x7F)} <= characters
    assert set(INTERNATIONAL_CHARACTERS) <= characters
    assert "0̸" in characters


def test_draft_capitals_fill_pins_1_to_7_of_nine_columns():
    font = _font("kx-p1080-draft")
    assert _rows(font, "H") == set(range(7))
    assert all(column < 9 for c in font.characters() for column, _ in font.glyph(c).dots)


def test_draft_descenders_are_lowered_two_pins_onto_the_ninth():
    font = _font("kx-p1080-draft")
    for character in "gpqy":
        assert max(_rows(font, character)) == 8, character
    assert _rows(font, "x") <= set(range(2, 7))


def test_draft_lowers_some_columns_of_a_character_and_not_others():
    # The j's stem and dot are not lowered; its hook is.
    rows = _rows(_font("kx-p1080-draft"), "j")
    assert 0 in rows and 8 in rows


def test_draft_italics_are_the_roms_own_and_lean_right():
    upright, italic = _font("kx-p1080-draft"), _font("kx-p1080-draft-italic")
    assert italic.glyph("l").dots != upright.glyph("l").dots
    top = min(column for column, row in italic.glyph("l").dots if row == 0)
    bottom = min(column for column, row in italic.glyph("l").dots if row == 6)
    assert top > bottom


def test_nlq_prints_both_passes_and_lowers_descenders_a_pin():
    font = _font("kx-p1080-nlq")
    rows = _rows(font, "H")
    assert any(row % 2 == 0 for row in rows) and any(row % 2 == 1 for row in rows)
    assert max(rows) < 16
    for character in "gpqy":
        assert max(_rows(font, character)) >= 16, character


def test_nlq_never_fires_a_pin_in_successive_columns():
    font = _font("kx-p1080-nlq")
    for character in font.characters():
        assert not font.glyph(character).has_adjacent_dots, character


def test_nlq_italic_moves_each_pair_of_pins_a_column_further_right():
    upright, italic = _font("kx-p1080-nlq"), _font("kx-p1080-nlq-italic")
    glyph = upright.glyph("l").dots
    expected = set()
    for column, row in glyph:
        pin = (row - row % 2) // 2
        shifted = column + 3 - pin // 2
        if shifted < 24:
            expected.add((shifted, row))
    assert italic.glyph("l").dots == expected
