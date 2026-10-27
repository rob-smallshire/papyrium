"""The LC-10's fonts meet the dot font contract and hold the LC-10's characters."""

import pytest

from papyrium.core.conformance import DotFontConformance
from papyrium.extension import create_extension, namespace_for
from papyrium.font.lc10 import (
    LC10DraftFont,
    LC10NlqCourierEliteFont,
    LC10NlqCourierFont,
    LC10NlqOratorEliteFont,
    LC10NlqOratorFont,
    LC10NlqOratorSmallCapitalsEliteFont,
    LC10NlqOratorSmallCapitalsFont,
    LC10NlqSanserifEliteFont,
    LC10NlqSanserifFont,
)

PICA_FONTS = {
    "lc10-nlq-courier": LC10NlqCourierFont,
    "lc10-nlq-sanserif": LC10NlqSanserifFont,
    "lc10-nlq-orator": LC10NlqOratorFont,
    "lc10-nlq-orator-small-capitals": LC10NlqOratorSmallCapitalsFont,
}
ELITE_FONTS = {
    "lc10-nlq-courier-elite": LC10NlqCourierEliteFont,
    "lc10-nlq-sanserif-elite": LC10NlqSanserifEliteFont,
    "lc10-nlq-orator-elite": LC10NlqOratorEliteFont,
    "lc10-nlq-orator-small-capitals-elite": LC10NlqOratorSmallCapitalsEliteFont,
}
NLQ_FONTS = PICA_FONTS | ELITE_FONTS

#: The characters of the national sets, the IBM PC's upper half (less its
#: block and box drawing and the integral halves) and its low symbols.
NATIONAL = "£¥₧§°´¨¤ÄÅÆÉÑÖÜßàáäåæçèéìíñòóöøùúüØ¡¿"
IBM = "Çâêëïîôûÿ¢ƒªº⌐¬½¼«»αβΓπΣσµτΦΘΩδ∞ε∩≡±≥≤÷≈∙·√ⁿ²■⌂"
SYMBOLS = "☺☻♥♦♣♠•◘○◙♂♀♪♫☼►◄↕‼¶▬↨↑↓→←∟↔▲▼"


class TestLC10DraftConformance(DotFontConformance):
    allows_adjacent_dots = True

    def make_font(self):
        return LC10DraftFont(name="lc10-draft")


class TestLC10NlqCourierConformance(DotFontConformance):
    def make_font(self):
        return LC10NlqCourierFont(name="lc10-nlq-courier")


class TestLC10NlqSanserifEliteConformance(DotFontConformance):
    def make_font(self):
        return LC10NlqSanserifEliteFont(name="lc10-nlq-sanserif-elite")


@pytest.mark.parametrize("name", ["lc10-draft", *NLQ_FONTS])
def test_is_registered_on_the_font_axis(name):
    assert create_extension("font", namespace_for("font"), name).name == name


def test_draft_is_nine_pins_on_the_pica_grid():
    font = LC10DraftFont(name="lc10-draft")
    assert (font.rows, font.columns) == (9, 11)


@pytest.mark.parametrize("cls", PICA_FONTS.values())
def test_pica_nlq_is_eighteen_rows_by_twenty_four_columns(cls):
    font = cls(name="nlq")
    assert (font.rows, font.columns) == (18, 24)


@pytest.mark.parametrize("cls", ELITE_FONTS.values())
def test_elite_nlq_is_eighteen_rows_by_twenty_columns(cls):
    font = cls(name="nlq")
    assert (font.rows, font.columns) == (18, 20)


@pytest.mark.parametrize("cls", [LC10DraftFont, *NLQ_FONTS.values()])
def test_covers_the_national_and_ibm_characters(cls):
    missing = set(NATIONAL + IBM + SYMBOLS) - cls(name="font").characters()
    assert not missing, sorted(missing)


@pytest.mark.parametrize("cls", [LC10DraftFont, *NLQ_FONTS.values()])
def test_has_the_slashed_zero(cls):
    assert cls(name="font").glyph("0̸").dots


def test_draft_descenders_sit_a_pin_lower():
    font = LC10DraftFont(name="lc10-draft")
    assert max(row for _, row in font.glyph("g").dots) == 8
    assert min(row for _, row in font.glyph("H").dots) == 0
    assert max(row for _, row in font.glyph("H").dots) < 8


@pytest.mark.parametrize(
    "cls",
    [LC10NlqCourierFont, LC10NlqSanserifFont, LC10NlqCourierEliteFont, LC10NlqSanserifEliteFont],
)
def test_nlq_descenders_sit_a_pin_lower(cls):
    font = cls(name="nlq")
    assert max(row for _, row in font.glyph("p").dots) == 17
    assert max(row for _, row in font.glyph("H").dots) < 16


def test_orator_lower_case_dips_at_most_half_a_dot_below_the_baseline():
    font = LC10NlqOratorFont(name="nlq")
    baseline = max(row for _, row in font.glyph("o").dots)
    assert all(max(row for _, row in font.glyph(c).dots) <= baseline + 1 for c in "gjpqy")


def test_orator_is_a_dot_taller_than_courier():
    def baseline(font):
        return max(row for _, row in font.glyph("H").dots)

    orator, courier = LC10NlqOratorFont(name="o"), LC10NlqCourierFont(name="c")
    assert baseline(orator) == baseline(courier) + 2


@pytest.mark.parametrize("cls", NLQ_FONTS.values())
def test_nlq_prints_both_passes(cls):
    rows = {row for _, row in cls(name="nlq").glyph("H").dots}
    assert any(row % 2 == 0 for row in rows) and any(row % 2 == 1 for row in rows)


def test_orator_variants_differ_only_in_lower_case():
    lower = LC10NlqOratorFont(name="lower")
    small = LC10NlqOratorSmallCapitalsFont(name="small")
    assert lower.glyph("A") == small.glyph("A")
    assert lower.glyph("a") != small.glyph("a")


def test_small_capitals_are_shorter_than_capitals():
    font = LC10NlqOratorSmallCapitalsFont(name="small")
    top = min(row for _, row in font.glyph("a").dots)
    assert top > min(row for _, row in font.glyph("A").dots)


def test_elite_narrows_the_widest_characters():
    pica = LC10NlqCourierFont(name="pica")
    elite = LC10NlqCourierEliteFont(name="elite")
    assert max(c for c, _ in elite.glyph("M").dots) < max(c for c, _ in pica.glyph("M").dots)
