"""The MPS-803's characters meet the dot font contract."""

from papyrium.core.conformance import DotFontConformance
from papyrium.extension import create_extension, namespace_for
from papyrium.font.mps803 import Mps803Font


class TestMps803FontConformance(DotFontConformance):
    allows_adjacent_dots = True

    def make_font(self):
        return Mps803Font(name="mps803")

    def test_covers_printable_ascii(self):
        # PETSCII has no \ ^ _ ` { | } ~: the font covers its own sets.
        pass


def test_is_registered_on_the_font_axis():
    assert isinstance(create_extension("font", namespace_for("font"), "mps803"), Mps803Font)


def test_holds_both_sets_in_seven_rows_of_six_columns():
    font = Mps803Font(name="mps803")
    assert (font.rows, font.columns) == (7, 6)
    for character in "AZaz09@£↑←π♠♥♦♣─│┼▒✓":
        assert font.glyph(character) is not None, character


def test_its_zero_is_slashed():
    zero = Mps803Font(name="mps803").glyph("0")
    assert (2, 3) in zero.dots
