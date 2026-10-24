"""Dot fonts: parsing the text format and the Glyph model."""

import pytest

from papyrium.core.dotfont import Glyph, parse_dot_font
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
