"""IBM mode, as the Star LC-10 has it: an IBM Proprinter II's character sets
and commands on the same printer."""

from helpers import ESC, LEFT, LINE, PICA, dots, run

IBM = {"ibm_mode": True, "fs_prefix": True, "ibm_character_sets": True}
FS = b"\x1c"


def _text(data, **options):
    pages = run(data, **{**IBM, **options})
    return "".join(mark.character for page in pages for mark in page.text)


def test_set_2_prints_the_upper_half_of_the_ibm_pc_set():
    assert _text(b"\x80\x9b\xc4\xe0") == "Ç¢─α"


def test_set_1_takes_128_to_159_as_controls():
    assert _text(ESC + b"7\x80\xe0") == "α"
    assert _text(ESC + b"7" + ESC + b"6\x80") == "Ç"


def test_the_card_suits_and_section_sign_print_among_the_low_codes():
    assert _text(b"\x03\x04\x05\x06\x15") == "♥♦♣♠§"


def test_esc_backslash_prints_any_code_as_a_character():
    assert _text(ESC + b"\\\x03\x00\x01\x0dA") == "☺♪A"


def test_esc_caret_prints_one_code_as_a_character():
    assert _text(ESC + b"^\x0eA") == "♫A"


def test_fs_commands():
    assert dots(FS + b"4A", **IBM) == [(LEFT + 36 + 108, 0)]
    assert _text(FS + b"R\x02@") == "§"
    assert dots(FS + b"\\\x0a\x00A", **IBM) == [(LEFT + 10 * 36 + 36, 0)]


def test_fs_in_standard_mode_swallows_the_next_byte():
    options = {"fs_prefix": True}
    assert dots(FS + b"4A", **options) == [(LEFT + 36, 0)]


def test_esc_a_waits_for_esc_2():
    assert dots(ESC + b"A\x18\nA", **IBM) == [(LEFT + 36, LINE)]
    assert dots(ESC + b"A\x18" + ESC + b"2\nA", **IBM) == [(LEFT + 36, 24 * 60)]


def test_esc_a_0_and_esc_3_0_are_ignored():
    assert dots(ESC + b"A\x00" + ESC + b"2\nA", **IBM) == [(LEFT + 36, LINE)]
    assert dots(ESC + b"3\x00\nA", **IBM) == [(LEFT + 36, LINE)]


def test_esc_5_makes_carriage_return_feed():
    assert dots(ESC + b"5\x01A\rA", **IBM)[1] == (LEFT + 36, LINE)


def test_esc_4_makes_this_line_the_top_of_the_page():
    first, second = run(b"\n\n" + ESC + b"4A\x0cA", **IBM)
    assert first.dots == ((LEFT + 36, 2 * LINE),)
    assert second.dots == ((LEFT + 36, 2 * LINE),)


def test_pitch_commands():
    assert dots(ESC + b":AA", **IBM)[1] == (LEFT + 360 + 30, 0)
    # ESC M drops condensed; SI is always 17 to the inch; DC2 returns to pica.
    assert dots(b"\x0f" + ESC + b"MAA", **IBM)[1] == (LEFT + 360 + 30, 0)
    assert dots(ESC + b":\x0fAA", **IBM)[1] == (LEFT + 252 + 21, 0)
    assert dots(ESC + b":\x12AA", **IBM)[1] == (LEFT + PICA + 36, 0)


def test_esc_p_n_is_proportional():
    assert dots(ESC + b"P\x01AA", **IBM)[2] == (LEFT + 3 * 36 + 36, 0)


def test_esc_q_3_takes_the_printer_off_line_until_dc1():
    assert dots(ESC + b"Q\x03A\x11A", **IBM) == [(LEFT + 36, 0)]


def test_esc_r_resets_the_tabs():
    data = ESC + b"D\x02\x00" + ESC + b"R\tA"
    assert dots(data, **IBM) == [(LEFT + 8 * PICA + 36, 0)]


def test_standard_mode_commands_ibm_mode_lacks_are_ignored():
    # ESC SP is not a command here: the A after it prints.
    assert dots(ESC + b" AA", **IBM)[1] == (LEFT + PICA + 36, 0)
    assert _text(ESC + b"t\x00\x80") == "Ç"
