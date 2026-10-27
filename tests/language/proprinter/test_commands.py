"""The Proprinter's commands for spacing, forms, tabs and the line."""

from proprinter_helpers import ESC, FS, LEFT, LINE, NLQ_STEP, PICA, PIN, STEP, dots, run, text


def test_esc_a_waits_for_esc_2():
    assert dots(ESC + b"A\x18\nA") == [(LEFT + STEP, LINE)]
    assert dots(ESC + b"A\x18" + ESC + b"2\nA") == [(LEFT + STEP, 24 * PIN)]


def test_esc_a_0_keeps_the_stored_spacing():
    assert dots(ESC + b"A\x18" + ESC + b"A\x00" + ESC + b"2\nA") == [(LEFT + STEP, 24 * PIN)]


def test_esc_2_without_esc_a_is_a_sixth_of_an_inch():
    assert dots(ESC + b"0" + ESC + b"2\nA") == [(LEFT + STEP, LINE)]


def test_a_line_feed_only_feeds_unless_switch_6_is_on():
    assert dots(b"A\nA")[1] == (LEFT + PICA + STEP, LINE)
    assert dots(b"A\nA", line_feed_returns=True)[1] == (LEFT + STEP, LINE)


def test_esc_5_makes_carriage_return_feed():
    assert dots(ESC + b"5\x01A\rA")[1] == (LEFT + STEP, LINE)


def test_esc_j_returns_the_carriage_with_switch_6():
    assert dots(b"A" + ESC + b"J\x03A")[1] == (LEFT + PICA + STEP, 3 * 20)
    assert dots(b"A" + ESC + b"J\x03A", line_feed_returns=True)[1] == (LEFT + STEP, 3 * 20)


def test_esc_4_makes_this_line_the_top_of_form():
    first, second = run(b"\n\n" + ESC + b"4A\x0cA")
    assert first.dots == ((LEFT + STEP, 2 * LINE),)
    assert second.dots == ((LEFT + STEP, 2 * LINE),)


def test_switch_1_ignores_a_form_feed_at_the_top_of_a_blank_form():
    (page,) = run(b"\x0cA", form_feed_at_top_ignored=True)
    assert page.dots == ((LEFT + STEP, 0),)
    assert len(run(b"\x0cA")) == 2
    assert len(run(b"A\r\x0cA", form_feed_at_top_ignored=True)) == 2


def test_esc_b_numbers_lines_from_1_at_the_top_of_form():
    assert dots(ESC + b"B\x03\x00\x0bA") == [(LEFT + STEP, 2 * LINE)]


def test_vertical_tab_with_no_stop_below_is_a_line_feed():
    assert dots(b"\x0bA") == [(LEFT + STEP, LINE)]
    assert dots(ESC + b"B\x02\x00\n\n\x0bA") == [(LEFT + STEP, 3 * LINE)]


def test_esc_d_numbers_columns_from_1_at_the_left_margin():
    assert dots(ESC + b"D\x05\x00\tA") == [(LEFT + 4 * PICA + STEP, 0)]


def test_power_on_tabs_are_every_eight_columns_from_column_9():
    assert dots(b"\tA") == [(LEFT + 8 * PICA + STEP, 0)]


def test_esc_r_restores_the_power_on_tabs():
    assert dots(ESC + b"D\x02\x00" + ESC + b"R\tA") == [(LEFT + 8 * PICA + STEP, 0)]


def test_esc_r_clears_the_vertical_tabs():
    assert dots(ESC + b"B\x05\x00" + ESC + b"R\x0bA") == [(LEFT + STEP, LINE)]


def test_esc_w_ends_one_line_double_width():
    assert dots(b"\x0e" + ESC + b"W\x00AA")[1] == (LEFT + PICA + STEP, 0)
    assert dots(b"\x0e" + ESC + b"W\x01" + ESC + b"W\x00AA")[1] == (LEFT + PICA + STEP, 0)


def test_one_line_double_width_ends_at_carriage_return():
    assert dots(b"\x0e\rAA")[1] == (LEFT + PICA + STEP, 0)


def test_esc_p_1_spaces_by_ibms_widths_and_offsets():
    # ! is 5 columns wide, its first 4 skipped; A takes the whole cell.
    assert dots(ESC + b"P\x01!A") == [(LEFT + STEP, 0), (LEFT + 5 * STEP + STEP, 0)]
    assert dots(ESC + b"P\x01AA")[1] == (LEFT + PICA + STEP, 0)


def test_proportional_nlq_takes_the_same_widths_on_its_finer_grid():
    assert dots(ESC + b"P\x01" + ESC + b"I\x02!A") == [
        (LEFT + 2 * NLQ_STEP, 0),
        (LEFT + 10 * NLQ_STEP + 2 * NLQ_STEP, 0),
    ]


def test_esc_q_3_deselects_the_printer_until_dc1():
    assert dots(ESC + b"Q\x03A\x11A") == [(LEFT + STEP, 0)]


def test_dc3_is_ignored():
    assert dots(b"\x13A") == [(LEFT + STEP, 0)]


def test_underscore_passes_under_characters_but_not_block_graphics():
    underlined = dots(ESC + b"-\x01A")
    assert (LEFT, 8 * PIN) in underlined
    assert dots(ESC + b"-\x01\xb0") == [(LEFT + STEP, 0)]


def test_esc_p_commands_the_proprinter_lacks_are_ignored():
    # ESC SP is no command here: the A after it prints.
    assert dots(ESC + b" AA")[1] == (LEFT + PICA + STEP, 0)
    assert text(ESC + b"t\x00\xe0") == "α"


def test_without_star_commands_fs_is_ignored():
    assert text(FS + b"4A") == "4A"
