"""draft-9 meets the dot font contract and covers the national characters."""

from papyrium.core.conformance import DotFontConformance
from papyrium.extension import create_extension, namespace_for
from papyrium.font.draft_9 import Draft9Font

# Code points rather than literals, to keep the source 7-bit ASCII.
NATIONAL_CHARACTERS = "".join(
    chr(code_point)
    for code_point in (
        0x00A3,
        0x00A7,
        0x00B0,
        0x00A8,
        0x00A4,
        0x00A1,
        0x00BF,
        0x00A5,
        0x20A7,
        0x00C4,
        0x00D6,
        0x00DC,
        0x00E4,
        0x00F6,
        0x00FC,
        0x00DF,
        0x00E9,
        0x00E8,
        0x00E0,
        0x00F9,
        0x00F2,
        0x00EC,
        0x00C9,
        0x00F1,
        0x00D1,
        0x00E7,
        0x00E5,
        0x00C5,
        0x00E6,
        0x00C6,
        0x00F8,
        0x00D8,
    )
)


class TestDraft9Conformance(DotFontConformance):
    def make_font(self):
        return Draft9Font(name="draft-9")


def test_is_registered_on_the_font_axis():
    font = create_extension("font", namespace_for("font"), "draft-9")
    assert (font.rows, font.columns) == (9, 11)


def test_covers_the_epson_national_characters():
    font = Draft9Font(name="draft-9")
    assert set(NATIONAL_CHARACTERS) <= font.characters()


def test_capitals_sit_on_row_6_and_descenders_reach_row_8():
    font = Draft9Font(name="draft-9")
    assert max(row for _, row in font.glyph("H").dots) == 6
    assert max(row for _, row in font.glyph("g").dots) == 8


def test_zero_is_plain_like_the_fx80s():
    dots = Draft9Font(name="draft-9").glyph("0").dots
    assert not [(column, row) for column, row in dots if 3 <= column <= 7 and 1 <= row <= 5]


def test_has_a_slashed_zero():
    font = Draft9Font(name="draft-9")
    slashed = font.glyph("0\u0338")
    assert slashed is not None and slashed.dots != font.glyph("0").dots
