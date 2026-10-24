"""ESC/P paper and carriage motion: lines, pages, tabs, margins, editing."""

from helpers import ESC, FORM, LEFT, LINE, PICA, dots, mechanism, run

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


def test_form_length_sets_how_far_a_form_feed_moves_but_not_the_sheet():
    (page,) = run(ESC + b"C\x0cA\x0cA")
    assert page.height == FORM
    assert page.dots == ((LEFT + 36, 0), (LEFT + 36, 12 * LINE))
    (page,) = run(ESC + b"C\x00\x03A\x0cA")
    assert page.dots == ((LEFT + 36, 0), (LEFT + 36, 3 * 4320))


def test_a_line_printed_across_the_perforation_splits_between_pages():
    first, second = run(b"B", sheet_length=300)
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


def test_vertical_tabs_default_to_every_other_line():
    assert dots(b"A\x0bA\nA\x0bA") == [
        (LEFT + 36, 0),
        (LEFT + 36, 2 * LINE),
        (LEFT + 36, 3 * LINE),
        (LEFT + 36, 4 * LINE),
    ]


def test_vertical_tab_in_a_channel_without_stops_is_a_line_feed():
    assert dots(ESC + b"/\x01A\x0bA") == [(LEFT + 36, 0), (LEFT + 36, LINE)]


def test_vertical_tab_channels_are_stored_and_selected():
    channels = ESC + b"b\x01\x05\x00" + ESC + b"b\x02\x03\x00"
    assert dots(channels + ESC + b"/\x01\x0bA") == [(LEFT + 36, 5 * LINE)]
    assert dots(channels + ESC + b"/\x02\x0bA") == [(LEFT + 36, 3 * LINE)]


def test_esc_b_stores_channel_zero():
    data = ESC + b"b\x00\x04\x00" + ESC + b"/\x01" + ESC + b"/\x00\x0bA"
    assert dots(data) == [(LEFT + 36, 4 * LINE)]


def test_vertical_tab_stops_beyond_the_form_are_ignored():
    data = ESC + b"C\x04" + ESC + b"B\x02\x04\x00\x0b\x0bA"
    assert dots(data) == [(LEFT + 36, 4 * LINE)]


def test_setting_the_form_length_cancels_skip_over_perforation():
    interpreter = EscpInterpreter(mechanism())
    pages = interpreter.feed(ESC + b"N\x06" + ESC + b"C\x42A" + b"\n" * 60 + b"A")
    assert pages == []
    (page,) = interpreter.finish()
    assert page.dots[-1] == (LEFT + 36, 60 * LINE)


def test_skip_over_perforation_as_long_as_the_form_is_ignored():
    data = ESC + b"C\x04" + ESC + b"N\x04A\nA"
    assert dots(data) == [(LEFT + 36, 0), (LEFT + 36, LINE)]


def test_line_spacing_beyond_85_72nds_is_ignored():
    assert dots(ESC + b"A\x56A\nA") == [(LEFT + 36, 0), (LEFT + 36, LINE)]


def test_horizontal_tabs_default_to_every_eight_columns():
    assert dots(b"\tA") == [(LEFT + 8 * PICA + 36, 0)]


def test_horizontal_tab_stops_can_be_set():
    assert dots(ESC + b"D\x03\x00\tA") == [(LEFT + 3 * PICA + 36, 0)]


def test_left_margin_takes_effect_at_the_next_carriage_return():
    assert dots(ESC + b"l\x0aA\rA") == [(LEFT + 36, 0), (LEFT + 10 * PICA + 36, 0)]


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


def test_a_zero_form_length_is_ignored():
    (page,) = run(ESC + b"3\x00" + ESC + b"C\x05A\n")
    assert page.height == FORM


def test_tab_stops_are_measured_from_the_left_margin():
    assert dots(ESC + b"l\x0a\r\tA") == [(LEFT + 18 * PICA + 36, 0)]


def test_setting_a_margin_restores_the_default_tabs():
    assert dots(ESC + b"D\x03\x00" + ESC + b"Q\x50\tA") == [(LEFT + 8 * PICA + 36, 0)]
    assert dots(ESC + b"D\x03\x00" + ESC + b"l\x00\tA") == [(LEFT + 8 * PICA + 36, 0)]


def test_right_margin_must_leave_two_pica_columns():
    # A one-column line is refused; the power-on margin stays.
    assert dots(ESC + b"l\x0a" + ESC + b"Q\x0b\r" + b" " * 20 + b"A") == [
        (LEFT + 30 * PICA + 36, 0)
    ]
    assert dots(ESC + b"l\x0a" + ESC + b"Q\x0c\rAAA") == [
        (LEFT + 10 * PICA + 36, 0),
        (LEFT + 11 * PICA + 36, 0),
        (LEFT + 10 * PICA + 36, LINE),
    ]


def test_left_margin_must_leave_two_columns_before_the_right():
    assert dots(ESC + b"l\x4f\rA") == [(LEFT + 36, 0)]
    assert dots(ESC + b"l\x4e\rA") == [(LEFT + 78 * PICA + 36, 0)]


def test_compressed_lines_hold_132_characters_at_the_power_on_margin():
    condensed = 252
    (wrapped,) = [dot for dot in dots(b"\x0f" + b" " * 132 + b"A")]
    assert wrapped == (LEFT + 21, LINE)
    assert dots(b"\x0f" + ESC + b"Q\x89" + b" " * 136 + b"A") == [(LEFT + 136 * condensed + 21, 0)]


def test_vertical_tab_to_a_stop_ends_one_line_double_width():
    assert dots(ESC + b"B\x02\x00\x0eA\x0bA") == [
        (LEFT + 72, 0),
        (LEFT + 108, 0),
        (LEFT + 36, 2 * LINE),
    ]


def test_setting_the_form_length_makes_the_current_line_the_top_of_form():
    (page,) = run(b"A\r\n" + ESC + b"C\x02A\x0cA")
    assert page.dots == ((LEFT + 36, 0), (LEFT + 36, LINE), (LEFT + 36, 3 * LINE))


def test_a_form_feed_after_a_mid_page_reset_ejects_the_printed_sheet_only():
    # A program that resets with ESC @ before its final form feed.
    (page,) = run(b"A\r\n" + ESC + b"@\x0c")
    assert page.dots == ((LEFT + 36, 0),)


def test_initialise_restores_the_power_on_form_length():
    # The form feed moves a whole sheet, not the two lines set before the reset.
    first, second = run(ESC + b"C\x02" + ESC + b"@A\x0cA")
    assert first.dots == second.dots == ((LEFT + 36, 0),)


def test_proportional_tabs_and_backspace_use_pica_columns():
    assert dots(ESC + b"p\x01" + ESC + b"D\x02\x00\tA")[0] == (LEFT + 2 * PICA + 36, 0)


def test_margins_in_condensed_emphasized_use_pica_columns():
    assert dots(b"\x0f" + ESC + b"E" + ESC + b"l\x02\rA") == [
        (LEFT + 2 * PICA + 36, 0),
        (LEFT + 2 * PICA + 54, 0),
    ]


def test_reset_discards_the_unprinted_line():
    assert dots(b"A\r\nA" + ESC + b"@") == [(LEFT + 36, 0)]


def test_graphics_print_the_line_before_them_and_themselves_at_once():
    # Text before graphics, and the graphics, survive a reset; text after does not.
    assert dots(b"A" + ESC + b"K\x01\x00\x80A" + ESC + b"@") == [
        (LEFT + 36, 0),
        (LEFT + PICA, 0),
    ]


def test_commands_that_flush_the_buffer_protect_text_from_cancel():
    for command in (b"\x08", b"\t", b"\x0f", ESC + b"4", ESC + b"R\x00"):
        assert dots(b"A" + command + b"\x18")[0] == (LEFT + 36, 0), command


def test_underline_does_not_flush_the_buffer():
    assert run(b"A" + ESC + b"-\x00\x18") == []


def test_margin_commands_cancel_the_buffered_text():
    assert run(b"A" + ESC + b"Q\x28") == []
    assert run(b"A" + ESC + b"l\x01") == []


def test_reverse_feed_moves_back_up_the_sheet_without_a_carriage_return():
    assert dots(b"\n\nA" + ESC + b"j\x12A") == [
        (LEFT + 36, 2 * LINE),
        (LEFT + PICA + 36, 2 * LINE - 360),
    ]


def test_reverse_feed_stops_at_the_top_of_the_sheet():
    assert dots(b"A" + ESC + b"j\xffA") == [(LEFT + 36, 0), (LEFT + PICA + 36, 0)]


def test_top_offset_places_the_first_line_below_the_top_of_the_sheet():
    assert dots(b"A", top_offset=1000) == [(LEFT + 36, 1000)]


def test_forms_start_at_the_top_offset_on_every_sheet():
    first, second = run(b"A\x0cA", top_offset=1000)
    assert first.dots == second.dots == ((LEFT + 36, 1000),)


def test_a_full_form_of_line_feeds_reaches_the_top_offset_of_the_next_sheet():
    first, second = run(b"\n" * 66 + b"A", top_offset=LINE // 2)
    assert first.dots == ()
    assert second.dots == ((LEFT + 36, LINE // 2),)
