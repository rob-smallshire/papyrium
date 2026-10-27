"""The LC-10's fonts meet the dot font contract and hold the LC-10's characters."""

import pytest

from papyrium.core.conformance import DotFontConformance
from papyrium.extension import create_extension, namespace_for
from papyrium.font.lc10 import (
    LC10BlockGraphicsFont,
    LC10DraftEliteFont,
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


class TestLC10DraftEliteConformance(DotFontConformance):
    allows_adjacent_dots = True

    def make_font(self):
        return LC10DraftEliteFont(name="lc10-draft-elite")


class TestLC10NlqCourierConformance(DotFontConformance):
    def make_font(self):
        return LC10NlqCourierFont(name="lc10-nlq-courier")


class TestLC10NlqSanserifEliteConformance(DotFontConformance):
    def make_font(self):
        return LC10NlqSanserifEliteFont(name="lc10-nlq-sanserif-elite")


@pytest.mark.parametrize("name", ["lc10-draft", "lc10-draft-elite", *NLQ_FONTS])
def test_is_registered_on_the_font_axis(name):
    assert create_extension("font", namespace_for("font"), name).name == name


def test_pica_draft_is_nine_pins_by_a_pica_cell():
    font = LC10DraftFont(name="draft")
    assert (font.rows, font.columns) == (9, 12)


def test_elite_draft_is_nine_pins_by_the_roms_eleven_columns():
    font = LC10DraftEliteFont(name="draft")
    assert (font.rows, font.columns) == (9, 11)


def test_pica_draft_follows_the_sanserif_it_is_made_from():
    from papyrium.core.testing import MemoryDotFont

    rows = ["." * 24 for _ in range(18)]
    rows[1] = "#" + rows[1][1:]
    sanserif = MemoryDotFont(
        name="s", text="rows 18\ncolumns 24\nU+0041\n" + "\n".join(rows) + "\n"
    )
    draft = LC10DraftFont(name="draft", source=sanserif)
    assert draft.glyph("A").dots == frozenset({(0, 0)})


def test_pica_draft_is_sanserifs_second_pass_at_half_width():
    # Each draft column is two of Sanserif's second-pass columns ORed,
    # less any dot the previous column printed.
    draft = LC10DraftFont(name="draft")
    sanserif = LC10NlqSanserifFont(name="sanserif")
    for character in "AHgx":
        second_pass = {(c, r) for c, r in sanserif.glyph(character).dots if r % 2}
        halved = {(c // 2, (r - 1) // 2) for c, r in second_pass}
        assert draft.glyph(character).dots <= halved, character


def test_pica_draft_never_fires_a_pin_twice_running():
    font = LC10DraftFont(name="draft")
    assert not any(font.glyph(c).has_adjacent_dots for c in font.characters())


@pytest.mark.parametrize("cls", PICA_FONTS.values())
def test_pica_nlq_is_eighteen_rows_by_twenty_four_columns(cls):
    font = cls(name="nlq")
    assert (font.rows, font.columns) == (18, 24)


@pytest.mark.parametrize("cls", ELITE_FONTS.values())
def test_elite_nlq_is_eighteen_rows_by_twenty_columns(cls):
    font = cls(name="nlq")
    assert (font.rows, font.columns) == (18, 20)


@pytest.mark.parametrize("cls", [LC10DraftFont, LC10DraftEliteFont, *NLQ_FONTS.values()])
def test_covers_the_national_and_ibm_characters(cls):
    missing = set(NATIONAL + IBM + SYMBOLS) - cls(name="font").characters()
    assert not missing, sorted(missing)


@pytest.mark.parametrize("cls", [LC10DraftFont, LC10DraftEliteFont, *NLQ_FONTS.values()])
def test_has_the_slashed_zero(cls):
    assert cls(name="font").glyph("0̸").dots


@pytest.mark.parametrize("cls", [LC10DraftFont, LC10DraftEliteFont])
def test_draft_descenders_sit_a_pin_lower(cls):
    font = cls(name="draft")
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


BLOCK_GRAPHICS = "░▒▓│┤╡╢╖╕╣║╗╝╜╛┐└┴┬├─┼╞╟╚╔╩╦╠═╬╧╨╤╥╙╘╒╓╫╪┘┌█▄▌▐▀⌠⌡"


class TestLC10BlockGraphicsConformance(DotFontConformance):
    def make_font(self):
        return LC10BlockGraphicsFont(name="lc10-block-graphics")

    def test_covers_printable_ascii(self):
        # Block graphics only: the other characters come from the text fonts.
        pass

    def test_space_is_blank(self):
        pass


def test_block_graphics_are_twelve_dots_high():
    font = LC10BlockGraphicsFont(name="lc10-block-graphics")
    assert (font.rows, font.columns) == (12, 11)
    assert font.characters() == frozenset(BLOCK_GRAPHICS)


def test_vertical_lines_run_the_full_twelve_dots():
    font = LC10BlockGraphicsFont(name="lc10-block-graphics")
    for character in "│║┼⌠":
        rows = {row for _, row in font.glyph(character).dots}
        assert {8, 9, 10, 11} <= rows, character


def test_extension_rows_repeat_the_last_two():
    font = LC10BlockGraphicsFont(name="lc10-block-graphics")
    for character in BLOCK_GRAPHICS:
        dots = font.glyph(character).dots
        for row in (8, 9, 10, 11):
            source = 6 + row % 2
            assert {c for c, r in dots if r == row} == {c for c, r in dots if r == source}


def test_horizontal_lines_join_the_next_cell():
    # Dots every other column to the last, the cell's twelfth column blank.
    columns = {c for c, _ in LC10BlockGraphicsFont(name="g").glyph("─").dots}
    assert columns == {0, 2, 4, 6, 8, 10}
