"""The page model: physical units, paper and dot marks."""

from fractions import Fraction

import pytest

from papyrium.core.page import UNITS_PER_INCH, Page, inches, units_from_fraction


def test_units_divide_every_impact_printer_step():
    # FX-80 graphics and pitches, 1/216 and 1/72 inch feeds, condensed
    # columns (7/1440 inch) and Diablo 630 steps (1/120, 1/48 inch).
    for step in [
        Fraction(1, 60),
        Fraction(1, 72),
        Fraction(1, 80),
        Fraction(1, 90),
        Fraction(1, 120),
        Fraction(1, 144),
        Fraction(1, 216),
        Fraction(1, 240),
        Fraction(7, 1440),
        Fraction(1, 48),
    ]:
        assert (step * UNITS_PER_INCH).denominator == 1, step


def test_inches_converts_to_whole_units():
    assert inches(1) == UNITS_PER_INCH
    assert inches(Fraction(17, 2)) == UNITS_PER_INCH * 17 // 2


def test_units_from_fraction_rejects_inexact_values():
    with pytest.raises(ValueError):
        units_from_fraction(Fraction(1, 7))


def test_page_size_in_inches():
    page = Page(number=1, width=inches(Fraction(17, 2)), height=inches(11), dot_diameter=60)
    assert page.width_inches == Fraction(17, 2)
    assert page.height_inches == 11
    assert page.dots == ()


def test_pages_with_the_same_marks_are_equal():
    first = Page(number=1, width=100, height=100, dot_diameter=6, dots=((1, 2), (3, 4)))
    second = Page(number=1, width=100, height=100, dot_diameter=6, dots=((1, 2), (3, 4)))
    assert first == second
    assert first.is_blank is False


def test_a_page_without_marks_is_blank():
    assert Page(number=1, width=100, height=100, dot_diameter=6).is_blank


def test_text_marks_describe_content_without_making_a_page_printed():
    from papyrium.core.page import TextMark

    page = Page(
        number=1,
        width=100,
        height=100,
        dot_diameter=6,
        text=(TextMark(x=0, y=0, width=10, height=20, character=" "),),
    )
    assert page.is_blank
    assert page.text[0].character == " "


def test_dots_struck_through_a_coloured_band_mark_a_page():
    from papyrium.core.page import Ink, InkDots

    page = Page(number=1, width=432, height=432, dot_diameter=60)
    assert page.is_blank
    inked = Page(
        number=1, width=432, height=432, dot_diameter=60,
        ink_dots=(InkDots(Ink.CYAN, ((60, 60),)),),
    )  # fmt: skip
    assert not inked.is_blank
    assert inked.all_dots() == ((60, 60),)
