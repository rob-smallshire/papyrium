"""Character sets 1 and 2, and the All Characters Chart."""

from proprinter_helpers import ESC, LEFT, PICA, STEP, dots, text


def test_set_1_obeys_128_to_159_as_controls():
    assert text(b"\x80\xe0") == "α"


def test_set_1_takes_141_as_carriage_return():
    assert dots(b"A\x8dA") == [(LEFT + STEP, 0)] * 2


def test_esc_6_chooses_set_2_which_prints_128_to_159():
    assert text(ESC + b"6\x80") == "Ç"
    assert text(ESC + b"6" + ESC + b"7\x80") == ""


def test_switch_5_powers_on_in_set_2():
    assert text(b"\x80", ibm_set=2) == "Ç"


def test_set_2_prints_the_card_suits_and_section_sign_among_the_low_codes():
    assert text(ESC + b"6\x03\x04\x05\x06\x15") == "♥♦♣♠§"
    assert text(b"\x03\x04\x05\x06\x15") == ""


def test_255_prints_a_space():
    assert text(b"\xffA") == " A"


def test_delete_is_ignored():
    assert dots(b"A\x7fA") == [(LEFT + STEP, 0), (LEFT + PICA + STEP, 0)]


def test_esc_backslash_prints_codes_from_the_all_characters_chart():
    assert text(ESC + b"\\\x03\x00\x01\x0dA") == "☺♪A"


def test_esc_caret_prints_one_code_from_the_all_characters_chart():
    assert text(ESC + b"^\x0eA") == "♫A"
    assert text(ESC + b"^\x00A") == " A"
