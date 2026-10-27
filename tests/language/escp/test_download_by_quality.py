"""Download characters as the Star LC-10 defines them: ESC % with one
argument, and ESC & defining NLQ characters when NLQ is selected."""

from helpers import ESC, LEFT, PICA, dots
from test_variants import _nlq_font

STAR = {"user_set_arguments": 1, "user_characters_by_quality": True}
NLQ = {**STAR, "nlq": True, "nlq_fonts": (_nlq_font(0),)}
RAM = ESC + b"%\x01"


def _draft(first, last, attribute, columns=b"\x80"):
    return ESC + b"&\x00" + bytes([first, last, attribute]) + columns.ljust(11, b"\x00")


def _nlq(location, attribute, first_pass, second_pass=b""):
    return (
        ESC + b"&\x00" + bytes([location, location, attribute])
        + first_pass.ljust(23, b"\x00") + second_pass.ljust(23, b"\x00")
    )  # fmt: skip


def test_esc_percent_may_take_one_argument():
    # The byte after ESC % 1 is printed, not taken as a second argument.
    assert dots(_draft(0x41, 0x41, 0x80) + RAM + b"A", **STAR) == [(LEFT, 0)]


def test_nlq_characters_are_defined_when_nlq_is_selected():
    # Pass one's top pin in column 0, pass two's in column 1: rows 0 and 1.
    data = ESC + b"x\x01" + _nlq(0x41, 0x80, b"\x80", b"\x00\x80") + RAM + b"A"
    assert dots(data, **NLQ) == [(LEFT, 0), (LEFT + 18, 20)]


def test_a_lowered_nlq_character_sits_two_rows_lower():
    data = ESC + b"x\x01" + _nlq(0x41, 0x00, b"\x80") + RAM + b"A"
    assert dots(data, **NLQ) == [(LEFT, 60)]


def test_defining_one_kind_erases_the_other():
    data = _draft(0x42, 0x42, 0x80) + ESC + b"x\x01" + _nlq(0x41, 0x80, b"\x80") + RAM + b"AB"
    # B, defined in draft, is gone: it prints blank.
    assert dots(data, **NLQ) == [(LEFT, 0)]


def test_a_reversed_range_is_taken_in_order():
    second = b"\x80" + b"\x80".ljust(11, b"\x00")
    data = _draft(0x42, 0x41, 0x80) + second + RAM + b"AB"
    assert dots(data, **STAR) == [(LEFT, 0), (LEFT + PICA, 0)]


def test_control_codes_are_not_defined_but_their_data_is_read():
    # Code 31's definition is read and dropped; code 32's is the next.
    second = b"\x80" + b"\x00\x80".ljust(11, b"\x00")
    data = _draft(0x1F, 0x20, 0x80, b"\x80") + second + RAM + b" "
    assert dots(data, **STAR) == [(LEFT + 36, 0)]
