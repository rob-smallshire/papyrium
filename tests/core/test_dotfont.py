"""Dot fonts: parsing the text format and the Glyph model."""

import pytest

from papyrium.core.dotfont import DerivedDotFont, Glyph, half_width, parse_dot_font, pass_rows
from papyrium.exception import DataError

POUND_SIGN = chr(0x00A3)

_FONT_TEXT = """\
# A two-glyph test font.
rows 3
columns 5

U+0041 A
..#..
.#.#.
#...#

U+00A3 pound sign
.#.#.
.....
#.#.#
"""


def test_parse_reads_dimensions_and_glyphs():
    font = parse_dot_font(_FONT_TEXT)
    assert (font.rows, font.columns) == (3, 5)
    assert sorted(font.glyphs) == ["A", POUND_SIGN]
    assert font.glyphs["A"].dots == frozenset({(2, 0), (1, 1), (3, 1), (0, 2), (4, 2)})


def test_a_glyph_may_be_named_by_a_sequence_of_code_points():
    font = parse_dot_font("rows 1\ncolumns 3\nU+0030 U+0338 slashed zero\n.#.\n")
    assert font.glyphs["0\u0338"].dots == frozenset({(1, 0)})


def test_glyph_extent():
    glyph = parse_dot_font(_FONT_TEXT).glyphs[POUND_SIGN]
    assert (glyph.leftmost, glyph.rightmost) == (0, 4)
    assert Glyph(frozenset()).leftmost is None


def test_a_glyph_may_give_its_span_before_any_comment():
    font = parse_dot_font("rows 1\ncolumns 5\nU+0021 span 1 3 EXCLAMATION MARK\n..#..\n")
    glyph = font.glyphs["!"]
    assert glyph.span == (1, 3)
    assert glyph.extent == (1, 3)


def test_a_glyph_may_say_it_prints_a_pin_lower():
    text = "rows 2\ncolumns 3\nU+0067 lowered span 0 2 SMALL G\n...\n.#.\nU+0061 a\n.#.\n...\n"
    font = parse_dot_font(text)
    assert font.glyphs["g"].lowered and font.glyphs["g"].span == (0, 2)
    assert not font.glyphs["a"].lowered


def test_a_glyphs_extent_is_its_dots_without_a_span():
    glyph = parse_dot_font(_FONT_TEXT).glyphs[POUND_SIGN]
    assert glyph.span is None
    assert glyph.extent == (0, 4)
    assert Glyph(frozenset()).extent is None


def test_glyph_reports_horizontally_adjacent_dots():
    assert Glyph(frozenset({(0, 0), (1, 0)})).has_adjacent_dots
    assert not Glyph(frozenset({(0, 0), (1, 1)})).has_adjacent_dots


@pytest.mark.parametrize(
    "text, message",
    [
        ("rows 3\ncolumns 5\nU+0041\n..#..\n", "rows"),
        ("rows 1\ncolumns 5\nU+0041\n..#\n", "columns"),
        ("rows 1\ncolumns 3\nU+0041\n.x.\n", "'x'"),
        ("rows 1\ncolumns 3\nU+0041\n...\nU+0041\n...\n", "U\\+0041 is defined twice"),
        ("rows 1\ncolumns 3\nU+0030 U+0338\n...\nU+0030 U+0338\n...\n", "U\\+0030 U\\+0338"),
        ("columns 3\nU+0041\n...\n", "rows"),
        ("rows 1\ncolumns 3\nfoo\n", "foo"),
        ("rows 1\ncolumns 3\nU+0041 span 1\n...\n", "span"),
        ("rows 1\ncolumns 3\nU+0041 span 2 1\n...\n", "span"),
        ("rows 1\ncolumns 3\nU+0041 span 0 3\n...\n", "span"),
        ("rows 1\ncolumns 3\nU+0041 lowered lowered\n...\n", "lowered"),
    ],
)
def test_malformed_fonts_are_data_errors(text, message):
    with pytest.raises(DataError, match=message):
        parse_dot_font(text)


def test_a_font_file_on_disk_is_a_dot_font(tmp_path):
    from papyrium.core.dotfont import FileDotFont

    font_filepath = tmp_path / "local.txt"
    font_filepath.write_text(_FONT_TEXT)
    font = FileDotFont(name="local", filepath=font_filepath)
    assert (font.rows, font.columns) == (3, 5)
    assert font.characters() == frozenset({"A", POUND_SIGN})
    assert font.glyph("A") == parse_dot_font(_FONT_TEXT).glyphs["A"]


def test_pass_rows_keeps_one_passes_rows_as_pin_rows():
    glyph = Glyph(frozenset({(0, 0), (1, 1), (2, 3), (3, 4)}))
    assert pass_rows(glyph, 0) == Glyph(frozenset({(0, 0), (3, 2)}))
    assert pass_rows(glyph, 1) == Glyph(frozenset({(1, 0), (2, 1)}))


def test_half_width_ors_pairs_of_columns():
    glyph = Glyph(frozenset({(0, 0), (1, 1), (4, 2), (5, 2)}))
    assert half_width(glyph) == Glyph(frozenset({(0, 0), (0, 1), (2, 2)}))


def test_half_width_drops_a_dot_the_previous_column_printed():
    glyph = Glyph(frozenset({(0, 0), (3, 0), (5, 0), (6, 1)}))
    # Column 1 would repeat column 0's dot; column 2 follows a blank column.
    assert half_width(glyph) == Glyph(frozenset({(0, 0), (2, 0), (3, 1)}))


class _Doubled(DerivedDotFont):
    rows, columns = 3, 10

    def derive(self, glyph):
        return Glyph(frozenset((2 * c, r) for c, r in glyph.dots))


def _source_font():
    from papyrium.core.testing import MemoryDotFont

    return MemoryDotFont(name="source", text=_FONT_TEXT)


def test_a_derived_font_makes_each_glyph_from_its_sources():
    font = _Doubled(name="doubled", source=_source_font())
    assert font.characters() == frozenset({"A", POUND_SIGN})
    assert font.glyph("A").dots == frozenset({(4, 0), (2, 1), (6, 1), (0, 2), (8, 2)})
    assert font.glyph("Z") is None


def test_transforms_keep_a_glyphs_attributes():
    glyph = Glyph(frozenset({(2, 1)}), span=(2, 5), lowered=True)
    assert pass_rows(glyph, 1) == Glyph(frozenset({(2, 0)}), span=(2, 5), lowered=True)
    assert half_width(glyph) == Glyph(frozenset({(1, 1)}), span=(1, 2), lowered=True)
