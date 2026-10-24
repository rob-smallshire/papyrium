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
    # Made printable, 0x8A is the italic n with tilde, which the test font lacks.
    assert dots(ESC + b"6\x8aA") == [(LEFT + PICA + 36, 0)]


def test_esc_6_prints_the_italic_international_characters():
    assert dots(ESC + b"6\x86") == [(LEFT + 7 * 36 + 108, 0)]


def test_esc_i_prints_the_international_characters_behind_codes_0_to_31():
    assert dots(b"\x06A") == [(LEFT + 36, 0)]
    assert dots(ESC + b"I\x01\x06A") == [(LEFT + 7 * 36, 0), (LEFT + PICA + 36, 0)]
    assert dots(ESC + b"I1\x06" + ESC + b"I0\x06A") == [(LEFT + 7 * 36, 0), (LEFT + PICA + 36, 0)]


def test_esc_i_leaves_the_printer_s_own_control_codes_working():
    assert dots(ESC + b"I\x01A\rA") == [(LEFT + 36, 0), (LEFT + 36, 0)]


def test_code_255_is_delete_unless_high_codes_print():
    assert dots(b"AA\xffB") == [(LEFT + 36, 0), (LEFT + PICA + 36, 0), (LEFT + PICA + 108, 360)]


def test_dc3_deselects_until_dc1_when_software_select_is_switched_on():
    data = b"A\x13AAA\x11A"
    assert dots(data, software_select=True) == [(LEFT + 36, 0), (LEFT + PICA + 36, 0)]


def test_dc1_and_dc3_are_ignored_when_the_printer_is_always_selected():
    assert dots(b"A\x13A") == [(LEFT + 36, 0), (LEFT + PICA + 36, 0)]


def test_emphasized_can_be_the_power_on_weight():
    # Emphasized from power on, and again after a reset.
    assert dots(b"A\r" + ESC + b"F" + ESC + b"@A", emphasized=True) == [
        (LEFT + 36, 0),
        (LEFT + 54, 0),
        (LEFT + 36, 0),
        (LEFT + 54, 0),
    ]


def test_user_defined_characters_need_the_ram():
    data = ESC + b"&\x00AA\x80" + b"\x00" * 11 + ESC + b"%\x01\x00A"
    assert dots(data, user_defined_characters=False) == [(LEFT + 36, 0)]


def test_underline_can_print_below_the_descenders():
    (first, *_) = dots(ESC + b"-\x01A", underline_row=9)[1:]
    assert first == (LEFT, 540)


def test_immediate_mode_prints_each_character_as_it_arrives():
    assert dots(ESC + b"i\x01AB\x18") == [
        (LEFT + 36, 0),
        (LEFT + PICA + 36, 0),
        (LEFT + PICA + 108, 360),
    ]


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


def _define(location, attribute, columns):
    """ESC & for one character at *location*."""
    return ESC + b"&\x00" + bytes([location, location, attribute]) + columns.ljust(11, b"\x00")


RAM = ESC + b"%\x01\x00"


def test_undefined_ram_characters_print_blank():
    assert dots(_define(ord("B"), 0x80, b"\x80") + RAM + b"AB") == [(LEFT + PICA, 0)]


def test_copying_the_rom_fills_the_ram_before_definitions():
    data = ESC + b":\x00\x00\x00" + _define(ord("B"), 0x80, b"\x80") + RAM + b"AB"
    assert dots(data) == [(LEFT + 36, 0), (LEFT + PICA, 0)]


def test_ram_high_locations_are_characters_of_their_own():
    data = _define(0xC1, 0x80, b"\x80") + RAM
    assert dots(data + b"\xc1") == [(LEFT, 0)]
    assert run(data + b"A") == []


def test_user_defined_characters_never_fire_a_pin_in_adjacent_columns():
    assert dots(_define(ord("A"), 0x80, b"\x80\x80\x80") + RAM + b"A") == [
        (LEFT, 0),
        (LEFT + 72, 0),
    ]


def test_attribute_gives_the_proportional_columns():
    # Columns 2 to 5: four columns wide, starting at the dot in column 2.
    data = _define(ord("A"), 0x80 | (2 << 4) | 5, b"\x00\x00\x80") + RAM + ESC + b"p\x01AA"
    assert dots(data) == [(LEFT, 0), (LEFT + 18, 0), (LEFT + 144, 0), (LEFT + 162, 0)]


def test_national_codes_print_the_ram_location_they_point_to():
    # Spain prints location 8 for code 93.
    data = _define(8, 0x80, b"\x80") + RAM + ESC + b"R\x07]"
    assert dots(data) == [(LEFT, 0)]


def test_reset_erases_user_defined_characters():
    assert run(_define(ord("A"), 0x80, b"\x80") + ESC + b"@" + RAM + b"A") == []


def test_missing_glyph_prints_nothing_but_advances():
    assert dots(b"zA") == [(LEFT + PICA + 36, 0)]


def test_msb_control_applies_to_every_byte_received():
    # With bit 7 forced on, CR arrives as 141, still a carriage return.
    assert dots(ESC + b">A\rB" + ESC + b"#") == [
        (LEFT + 144, 0),
        (LEFT + 144, 0),
        (LEFT + 108, 360),
    ]


def test_msb_zero_keeps_graphics_off_the_top_pin():
    assert run(ESC + b"=" + ESC + b"K\x01\x00\x80") == []


def test_zero_prints_plain_by_default():
    assert dots(b"0") == [(LEFT + 36, 60)]


def test_the_slashed_zero_switch_prints_the_slashed_variant():
    assert dots(b"0", slashed_zero=True) == [(LEFT + 36, 2 * 60)]


def test_the_slashed_zero_is_still_text_zero():
    (page,) = run(b"0", slashed_zero=True)
    assert [mark.character for mark in page.text] == ["0"]


def test_pages_carry_the_mechanisms_stationery():
    from papyrium.core.stationery import stationery_named

    (page,) = run(b"A", stationery=stationery_named("music-ruled"))
    assert page.stationery.name == "music-ruled"
