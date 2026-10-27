"""Colour, as the Star LC-10 Colour prints it: ESC r chooses ribbon bands."""

import pytest
from helpers import ESC, LEFT, PICA, run

from papyrium.core.page import Ink

COLOUR = {"colour_ribbon": True}


def _inks(page):
    return {inked.ink: inked.dots for inked in page.ink_dots}


@pytest.mark.parametrize(
    "n, inks",
    [
        (1, {Ink.MAGENTA}),
        (2, {Ink.CYAN}),
        (3, {Ink.MAGENTA, Ink.CYAN}),
        (4, {Ink.YELLOW}),
        (5, {Ink.YELLOW, Ink.MAGENTA}),
        (6, {Ink.YELLOW, Ink.CYAN}),
    ],
)
def test_esc_r_strikes_the_dots_through_its_bands(n, inks):
    (page,) = run(ESC + b"r" + bytes([n]) + b"A", **COLOUR)
    assert page.dots == ()
    assert _inks(page) == {ink: ((LEFT + 36, 0),) for ink in inks}


def test_esc_r_0_is_black_and_the_digits_serve_too():
    (page,) = run(ESC + b"r3A" + ESC + b"r0A", **COLOUR)
    assert page.dots == ((LEFT + PICA + 36, 0),)
    assert set(_inks(page)) == {Ink.MAGENTA, Ink.CYAN}


def test_without_a_colour_ribbon_esc_r_is_ignored():
    (page,) = run(ESC + b"r\x01A")
    assert page.dots == ((LEFT + 36, 0),) and page.ink_dots == ()


def test_colour_may_change_within_a_line_and_lines_carry_it():
    (page,) = run(ESC + b"r\x02A\r\n" + ESC + b"r\x00A" + ESC + b"r\x01\x1b-\x01A", **COLOUR)
    inks = _inks(page)
    assert inks[Ink.CYAN] == ((LEFT + 36, 0),)
    assert page.dots == ((LEFT + 36, 720),)
    # The underline is struck in the character's colour.
    assert len(inks[Ink.MAGENTA]) > 1


def test_reset_returns_to_black():
    (page,) = run(ESC + b"r\x01" + ESC + b"@A", **COLOUR)
    assert page.dots == ((LEFT + 36, 0),)


def test_graphics_are_struck_in_colour():
    (page,) = run(ESC + b"r\x04" + ESC + b"K\x01\x00\x80", **COLOUR)
    assert _inks(page) == {Ink.YELLOW: ((LEFT, 0),)}
