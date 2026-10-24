"""ESC/P text: characters, pitch, styles and character sets."""

from helpers import ESC, FORM, LEFT, LINE, PICA, dots, run


def test_nothing_prints_no_pages():
    assert run(b"") == []


def test_a_character_prints_its_glyph_at_the_left_margin():
    assert dots(b"A") == [(LEFT + 36, 0)]


def test_page_is_letter_width_and_eleven_inches_long():
    (page,) = run(b"A")
    assert (page.width, page.height, page.dot_diameter) == (36720, FORM, 60)


def test_characters_advance_one_pica_column():
    assert dots(b"AA") == [(LEFT + 36, 0), (LEFT + PICA + 36, 0)]


def test_elite_columns_are_one_twelfth_inch():
    assert dots(ESC + b"MAA") == [(LEFT + 30, 0), (LEFT + 360 + 30, 0)]


def test_condensed_columns_are_seven_120ths_inch_until_dc2():
    assert dots(b"\x0fAA\x12A") == [(LEFT + 21, 0), (LEFT + 252 + 21, 0), (LEFT + 504 + 36, 0)]


def test_emphasized_strikes_each_dot_twice_half_a_column_apart():
    assert dots(ESC + b"EA" + ESC + b"FA") == [
        (LEFT + 36, 0),
        (LEFT + 54, 0),
        (LEFT + PICA + 36, 0),
    ]


def test_emphasized_overrides_condensed():
    assert dots(b"\x0f" + ESC + b"EA") == [(LEFT + 36, 0), (LEFT + 54, 0)]


def test_double_strike_repeats_each_dot_one_216th_inch_lower():
    assert dots(ESC + b"GA" + ESC + b"HA") == [
        (LEFT + 36, 0),
        (LEFT + 36, 20),
        (LEFT + PICA + 36, 0),
    ]


def test_double_width_doubles_columns_and_strikes_each_dot_twice():
    assert dots(ESC + b"W\x01AA" + ESC + b"W0A") == [
        (LEFT + 72, 0),
        (LEFT + 108, 0),
        (LEFT + 864 + 72, 0),
        (LEFT + 864 + 108, 0),
        (LEFT + 1728 + 36, 0),
    ]


def test_one_line_double_width_ends_at_the_line_feed():
    assert dots(b"\x0eA\nA") == [(LEFT + 72, 0), (LEFT + 108, 0), (LEFT + 36, LINE)]


def test_dc4_cancels_one_line_double_width():
    assert dots(b"\x0eA\x14A") == [(LEFT + 72, 0), (LEFT + 108, 0), (LEFT + 864 + 36, 0)]


def test_italic_leans_rows_above_the_baseline_right():
    # Row 0 is six rows above the baseline: half a column per row.
    assert dots(ESC + b"4A" + ESC + b"5A") == [(LEFT + 36 + 108, 0), (LEFT + PICA + 36, 0)]


def test_underline_runs_along_the_bottom_pin_for_the_whole_cell():
    underline = [(LEFT + x, 480) for x in range(0, PICA, 36)]
    assert dots(ESC + b"-\x01A" + ESC + b"-0A") == [
        (LEFT + 36, 0),
        *underline,
        (LEFT + PICA + 36, 0),
    ]


def test_superscript_and_subscript_compress_rows_to_half_pitch():
    # Each script dot is struck twice, the second 1/216 inch lower.
    assert dots(ESC + b"S0B" + ESC + b"S1B" + ESC + b"TB") == [
        (LEFT + 36, 0),
        (LEFT + 36, 20),
        (LEFT + 108, 180),
        (LEFT + 108, 200),
        (LEFT + PICA + 36, 240),
        (LEFT + PICA + 36, 260),
        (LEFT + PICA + 108, 420),
        (LEFT + PICA + 108, 440),
        (LEFT + 2 * PICA + 36, 0),
        (LEFT + 2 * PICA + 108, 360),
    ]


def test_proportional_width_follows_the_glyph():
    # A's only dot is in column 1: one column wide plus two of spacing.
    assert dots(ESC + b"p\x01AA")[::2] == [(LEFT + 36, 0), (LEFT + 3 * 36 + 36, 0)]


def test_master_select_sets_every_style_at_once():
    # Bit 3 emphasized, bit 5 double width.
    assert dots(ESC + b"!\x28A") == [
        (LEFT + 72, 0),
        (LEFT + 108, 0),
        (LEFT + 108, 0),
        (LEFT + 144, 0),
    ]


def test_master_select_leaves_italic_underline_and_proportional_alone():
    italic = dots(ESC + b"4" + ESC + b"!\x00A")
    assert italic == [(LEFT + 36 + 108, 0)]
    assert dots(ESC + b"!\xc2A") == [(LEFT + 36, 0)]


def test_elite_masks_emphasized_and_proportional():
    assert dots(ESC + b"M" + ESC + b"E" + ESC + b"p\x01AA") == [
        (LEFT + 30, 0),
        (LEFT + 360 + 30, 0),
    ]


def test_masked_modes_return_when_the_masking_mode_ends():
    assert dots(ESC + b"M\x0f" + ESC + b"PA") == [(LEFT + 21, 0)]


def test_proportional_characters_print_emphasized():
    assert dots(ESC + b"p\x01A") == [(LEFT + 36, 0), (LEFT + 54, 0)]


def test_script_prints_double_strike():
    assert dots(ESC + b"S0A") == [(LEFT + 36, 0), (LEFT + 36, 20)]


def test_esc_w_0_also_ends_one_line_double_width():
    assert dots(b"\x0e" + ESC + b"W\x00A") == [(LEFT + 36, 0)]


def test_uk_character_set_prints_pound_for_hash():
    assert dots(b"#" + ESC + b"R\x03#") == [(LEFT + 5 * 36, 0), (LEFT + PICA + 7 * 36, 0)]


def test_high_codes_print_italic():
    assert dots(b"\xc1") == [(LEFT + 36 + 108, 0)]


def test_msb_zero_forces_upright():
    assert dots(ESC + b"=\xc1" + ESC + b"#\xc1") == [(LEFT + 36, 0), (LEFT + PICA + 36 + 108, 0)]


def test_msb_one_forces_italic():
    assert dots(ESC + b">A") == [(LEFT + 36 + 108, 0)]


def test_codes_128_to_159_are_controls_unless_made_printable():
    assert dots(b"A\x8aA") == [(LEFT + 36, 0), (LEFT + 36, LINE)]
    # Made printable, 0x8A is an italic control position: no glyph, one column.
    assert dots(ESC + b"6\x8aA") == [(LEFT + PICA + 36, 0)]


def test_dc3_deselects_until_dc1():
    assert dots(b"A\x13AAA\x11A") == [(LEFT + 36, 0), (LEFT + PICA + 36, 0)]


def test_initialise_restores_power_on_settings():
    assert dots(ESC + b"E" + ESC + b"@A") == [(LEFT + 36, 0)]


def test_unknown_escape_is_ignored():
    assert dots(ESC + b"xA") == [(LEFT + 36, 0)]


def test_a_model_obeys_only_the_commands_it_supports():
    assert dots(ESC + b"MAA", commands=frozenset("E")) == [(LEFT + 36, 0), (LEFT + PICA + 36, 0)]


def test_user_defined_character_replaces_rom_glyph_when_selected():
    definition = ESC + b"&\x00AA" + b"\x80" + b"\x00\x80" + b"\x00" * 9
    assert dots(definition + b"A" + ESC + b"%\x01\x00A") == [
        (LEFT + 36, 0),
        (LEFT + PICA + 36, 0),
    ]


def test_user_defined_character_can_use_the_lower_eight_pins():
    definition = ESC + b"&\x00AA" + b"\x00" + b"\x01" + b"\x00" * 10
    assert dots(definition + ESC + b"%\x01\x00A") == [(LEFT, 480)]


def test_copy_rom_discards_user_definitions():
    definition = ESC + b"&\x00AA" + b"\x80" + b"\x80" + b"\x00" * 10
    assert dots(definition + ESC + b":\x00\x00\x00" + ESC + b"%\x01\x00A") == [(LEFT + 36, 0)]


def test_missing_glyph_prints_nothing_but_advances():
    assert dots(b"zA") == [(LEFT + PICA + 36, 0)]
