"""PROPORTIONAL_WIDTHS: IBM's character width table, Figure A-1."""

from papyrium.language.proprinter.widths import PROPORTIONAL_WIDTHS


def test_every_code_has_a_width_and_offset():
    assert len(PROPORTIONAL_WIDTHS) == 256


def test_a_sample_of_the_figure():
    assert PROPORTIONAL_WIDTHS[ord("!")] == (5, 4)
    assert PROPORTIONAL_WIDTHS[ord("i")] == (8, 2)
    assert PROPORTIONAL_WIDTHS[ord("|")] == (4, 4)
    assert PROPORTIONAL_WIDTHS[ord("o")] == (11, 0)
    assert PROPORTIONAL_WIDTHS[ord("W")] == (12, 0)
    assert PROPORTIONAL_WIDTHS[4] == (10, 1)
    assert PROPORTIONAL_WIDTHS[254] == (8, 2)


def test_the_skipped_and_printed_columns_fit_the_cell():
    assert all(width + offset <= 12 for width, offset in PROPORTIONAL_WIDTHS)
