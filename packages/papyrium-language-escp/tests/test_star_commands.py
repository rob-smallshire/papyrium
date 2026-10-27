"""Commands Star added to ESC/P, as the LC-10 has them: positioning, margins,
spacing, the slashed zero, reverse feeds and the macro."""

from helpers import ESC, LEFT, LINE, PICA, dots

UNIT_60 = 72  # 1/60 inch
UNIT_120 = 36  # 1/120 inch


def test_esc_dollar_moves_to_an_absolute_position_in_60ths_from_the_left_margin():
    assert dots(ESC + b"$\x0a\x00A") == [(LEFT + 10 * UNIT_60 + 36, 0)]
    assert dots(ESC + b"l\x02" + b"\r" + ESC + b"$\x00\x00A") == [(LEFT + 2 * PICA + 36, 0)]


def test_esc_dollar_beyond_the_right_margin_is_ignored():
    assert dots(b"A" + ESC + b"$\x00\x02A") == [(LEFT + 36, 0), (LEFT + PICA + 36, 0)]


def test_esc_backslash_moves_right_or_left_in_120ths():
    assert dots(ESC + b"\\\x0a\x00A") == [(LEFT + 10 * UNIT_120 + 36, 0)]
    assert dots(b"AA" + ESC + b"\\\x0c\x40A") == [
        (LEFT + 36, 0),
        (LEFT + PICA + 36, 0),
        (LEFT + 2 * PICA - 12 * UNIT_120 + 36, 0),
    ]


def test_esc_backslash_past_the_left_margin_is_ignored():
    assert dots(ESC + b"\\\x01\x40A") == [(LEFT + 36, 0)]


def test_esc_x_sets_both_margins():
    data = ESC + b"X\x05\x0a" + b"\rA" + b"AAAAA" + b"A"
    xs = [x for x, _ in dots(data)]
    assert xs[0] == LEFT + 5 * PICA + 36
    # The right margin at column 10 holds five characters; the sixth wraps.
    assert dots(data)[5] == (LEFT + 5 * PICA + 36, LINE)


def test_esc_space_adds_240ths_after_each_character():
    assert dots(ESC + b" \x0aAA") == [(LEFT + 36, 0), (LEFT + PICA + 10 * 18 + 36, 0)]


def test_esc_tilde_switches_the_slashed_zero():
    assert dots(ESC + b"~\x010" + ESC + b"~\x000") == [(LEFT + 36, 120), (LEFT + PICA + 36, 60)]


def test_esc_line_feed_feeds_back_a_line():
    assert dots(b"\n\nA" + ESC + b"\nA") == [(LEFT + 36, 2 * LINE), (LEFT + PICA + 36, LINE)]


def test_esc_form_feed_goes_back_to_the_top_of_the_page():
    assert dots(b"\n\n\nA" + ESC + b"\x0cA") == [(LEFT + 36, 3 * LINE), (LEFT + PICA + 36, 0)]


def test_a_macro_is_defined_up_to_rs_and_run_by_esc_plus_1():
    macro = ESC + b"+" + ESC + b" \x0a" + b"A" + b"\x1e"
    assert dots(macro + ESC + b"+\x01" + b"A") == [
        (LEFT + 36, 0),
        (LEFT + PICA + 10 * 18 + 36, 0),
    ]


def test_a_macro_keeps_sixteen_bytes():
    macro = ESC + b"+" + b"A" * 20 + b"\x1e"
    assert len(dots(macro + ESC + b"+\x01")) == 16


def test_a_command_ending_a_macro_takes_its_arguments_from_what_follows():
    macro = ESC + b"+" + ESC + b"$" + b"\x1e"
    assert dots(macro + ESC + b"+\x01" + b"\x0a\x00A") == [(LEFT + 10 * UNIT_60 + 36, 0)]
