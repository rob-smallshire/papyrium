"""m1109-nlq covers printable ASCII on the NLQ grid."""

from papyrium.extension import create_extension, namespace_for
from papyrium.font.m1109 import M1109NlqFont

PRINTABLE_ASCII = frozenset(chr(c) for c in range(0x20, 0x7F))


def test_is_registered_on_the_font_axis():
    font = create_extension("font", namespace_for("font"), "m1109-nlq")
    assert (font.rows, font.columns) == (18, 24)


def test_covers_printable_ascii():
    assert PRINTABLE_ASCII <= M1109NlqFont(name="m1109-nlq").characters()


def test_space_is_blank():
    assert not M1109NlqFont(name="m1109-nlq").glyph(" ").dots


def test_capitals_start_on_row_2_below_room_for_accents():
    font = M1109NlqFont(name="m1109-nlq")
    assert min(row for _, row in font.glyph("H").dots) == 2
