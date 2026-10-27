"""nlq_from_draft: the dots the Proprinter adds to a draft character in NLQ."""

from papyrium.core.dotfont import Glyph
from papyrium.language.proprinter import nlq_from_draft


def nlq(*dots, span=None):
    return set(nlq_from_draft(Glyph(frozenset(dots), span=span)).dots)


def test_a_dot_standing_alone_moves_to_the_finer_grid():
    assert nlq((3, 2)) == {(6, 4)}


def test_a_vertical_line_prints_solid():
    assert nlq((1, 0), (1, 1), (1, 2)) == {(2, 0), (2, 1), (2, 2), (2, 3), (2, 4)}


def test_a_diagonal_fills_in_either_way():
    assert nlq((1, 0), (2, 1)) == {(2, 0), (3, 1), (4, 2)}
    assert nlq((2, 0), (1, 1)) == {(4, 0), (3, 1), (2, 2)}


def test_a_horizontal_line_keeps_every_dot_and_adds_none():
    assert nlq((1, 0), (2, 0), (3, 0)) == {(2, 0), (4, 0), (6, 0)}


def test_no_diagonal_dot_meets_a_dot_inside_a_horizontal_line():
    # A diagonal down onto the middle of a horizontal line.
    line = [(1, 1), (2, 1), (3, 1)]
    assert nlq((1, 0), *line) == {(2, 0), (2, 1), (2, 2), (4, 2), (6, 2)}
    # And up from below it.
    assert nlq(*[(c, 0) for c in (1, 2, 3)], (3, 1)) == {(2, 0), (4, 0), (6, 0), (6, 1), (6, 2)}


def test_the_ends_of_a_horizontal_line_make_diagonals():
    assert nlq((1, 0), (2, 0), (3, 1)) == {(2, 0), (4, 0), (5, 1), (6, 2)}


def test_the_span_doubles_with_the_grid():
    assert nlq_from_draft(Glyph(frozenset(), span=(1, 5))).span == (2, 10)
