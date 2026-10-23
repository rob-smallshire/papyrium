"""ESC/P paper and carriage motion: lines, pages, tabs, margins, editing."""

from helpers import ESC, LEFT, LINE, PICA, dots, mechanism, run

from papyrium.language.escp import EscpInterpreter


def test_carriage_return_alone_overprints():
    assert dots(b"A\rA") == [(LEFT + 36, 0), (LEFT + 36, 0)]


def test_auto_line_feed_turns_carriage_return_into_a_new_line():
    assert dots(b"A\rA", auto_line_feed=True) == [(LEFT + 36, 0), (LEFT + 36, LINE)]


def test_line_feed_moves_to_the_left_margin_of_the_next_line():
    assert dots(b"AA\nA") == [(LEFT + 36, 0), (LEFT + PICA + 36, 0), (LEFT + 36, LINE)]


def test_bbc_line_ending_lf_cr_gives_single_spacing():
    assert dots(b"A\n\rA") == [(LEFT + 36, 0), (LEFT + 36, LINE)]


def test_form_feed_ejects_the_page():
    first, second = run(b"A\x0cA")
    assert first.dots == second.dots == ((LEFT + 36, 0),)
    assert (first.number, second.number) == (1, 2)


def test_a_page_completes_as_soon_as_the_paper_passes_its_end():
    interpreter = EscpInterpreter(mechanism())
    assert interpreter.feed(b"A" + b"\n" * 65) == []
    (page,) = interpreter.feed(b"\n")
    assert page.dots == ((LEFT + 36, 0),)
    assert interpreter.finish() == []


def test_form_feed_on_an_empty_page_ejects_a_blank_sheet():
    blank, printed = run(b"\x0cA")
    assert blank.is_blank and not printed.is_blank


def test_line_spacing_commands():
    assert dots(ESC + b"3\x10A\nA") == [(LEFT + 36, 0), (LEFT + 36, 320)]
    assert dots(ESC + b"A\x0cA\nA") == [(LEFT + 36, 0), (LEFT + 36, 720)]
    assert dots(ESC + b"0A\nA") == [(LEFT + 36, 0), (LEFT + 36, 540)]
    assert dots(ESC + b"1A\nA") == [(LEFT + 36, 0), (LEFT + 36, 420)]
    assert dots(ESC + b"0" + ESC + b"2A\nA") == [(LEFT + 36, 0), (LEFT + 36, LINE)]


def test_immediate_feed_keeps_the_column():
    assert dots(b"A" + ESC + b"J\x09A") == [(LEFT + 36, 0), (LEFT + PICA + 36, 180)]


def test_form_length_in_lines_and_in_inches():
    (page, _) = run(ESC + b"C\x0cA\x0cA")
    assert page.height == 12 * LINE
    (page, _) = run(ESC + b"C\x00\x03A\x0cA")
    assert page.height == 3 * 4320


def test_a_line_printed_across_the_perforation_splits_between_pages():
    first, second = run(ESC + b"A\x05" + ESC + b"C\x01B")
    assert first.height == 300
    assert first.dots == ((LEFT + 36, 0),)
    assert second.dots == ((LEFT + 108, 60),)


def test_skip_over_perforation_jumps_to_the_next_top_of_form():
    interpreter = EscpInterpreter(mechanism())
    pages = interpreter.feed(ESC + b"N\x06A" + b"\n" * 60)
    assert len(pages) == 1
    assert interpreter.finish() == []


def test_vertical_tabs():
    assert dots(ESC + b"B\x02\x05\x00\x0bA\x0bA") == [(LEFT + 36, 2 * LINE), (LEFT + 36, 5 * LINE)]


def test_vertical_tab_without_stops_is_a_line_feed():
    assert dots(b"A\x0bA") == [(LEFT + 36, 0), (LEFT + 36, LINE)]


def test_horizontal_tabs_default_to_every_eight_columns():
    assert dots(b"\tA") == [(LEFT + 8 * PICA + 36, 0)]


def test_horizontal_tab_stops_can_be_set():
    assert dots(ESC + b"D\x03\x00\tA") == [(LEFT + 3 * PICA + 36, 0)]


def test_left_margin():
    assert dots(ESC + b"l\x0aA\nA") == [(LEFT + 10 * PICA + 36, 0), (LEFT + 10 * PICA + 36, LINE)]


def test_right_margin_wraps_the_line():
    assert dots(ESC + b"Q\x02AAA") == [
        (LEFT + 36, 0),
        (LEFT + PICA + 36, 0),
        (LEFT + 36, LINE),
    ]


def test_eighty_one_columns_wrap_at_the_power_on_margin():
    assert dots(b" " * 80 + b"A") == [(LEFT + 36, LINE)]


def test_backspace_overprints_the_previous_character():
    assert dots(b"A\x08B") == [(LEFT + 36, 0), (LEFT + 36, 0), (LEFT + 108, 360)]


def test_delete_removes_the_last_character_from_the_line():
    assert dots(b"AA\x7fB") == [(LEFT + 36, 0), (LEFT + PICA + 36, 0), (LEFT + PICA + 108, 360)]


def test_cancel_clears_the_line():
    assert dots(b"AA\x18B") == [(LEFT + 36, 0), (LEFT + 108, 360)]


def test_dots_beyond_the_paper_are_not_printed():
    assert dots(b"A", paper_width=1100) == []


def test_wrapping_ends_one_line_double_width():
    # A double-width character fills a two-column line; the next wraps to
    # a new line and prints at normal width, as does the one after.
    assert dots(ESC + b"Q\x02\x0eAAA") == [
        (LEFT + 72, 0),
        (LEFT + 108, 0),
        (LEFT + 36, LINE),
        (LEFT + PICA + 36, LINE),
    ]
