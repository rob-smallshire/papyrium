"""Mechanism settings for ESC/P printers that differ from the FX-80."""

from helpers import ESC, LEFT, LINE, dots, run

from papyrium.language.escp import CharacterSet
from papyrium.language.escp.charsets import character_for

M1109_CONTROLS = frozenset({8, 9, 10, 11, 12, 13, 14, 15, 18, 19, 20, 27})


def text(data, **options):
    (page,) = run(data, **options)
    return "".join(mark.character for mark in page.text)


def test_norway_denmark_ii_and_england_ii():
    assert character_for(0x24, CharacterSet.NORWAY) == chr(0xA4)
    assert character_for(0x24, CharacterSet.DENMARK_II) == "$"
    assert character_for(0x40, CharacterSet.DENMARK_II) == chr(0xC9)
    assert character_for(0x60, CharacterSet.UK_II) == chr(0xA3)
    assert character_for(0x23, CharacterSet.UK_II) == "#"


def test_the_fx80_ignores_the_extra_national_sets():
    assert text(ESC + b"R\x0b`") == "`"


def test_a_printer_with_twelve_sets_selects_them():
    assert text(ESC + b"R\x0b`", character_sets=12) == chr(0xA3)


def test_low_codes_that_stay_controls_are_the_mechanisms():
    # Code 24 is CAN on the FX-80 even with ESC I 1; on the M-1109 it prints.
    assert text(ESC + b"I\x01A\x18B") == "B"
    assert text(ESC + b"I\x01A\x18B", controls=M1109_CONTROLS) == "A" + chr(0xD6) + "B"


def test_without_default_vertical_tabs_vt_is_a_line_feed():
    assert dots(b"\x0bA", default_vertical_tabs=False) == [(LEFT + 36, LINE)]


def test_form_length_can_clear_the_vertical_tabs():
    data = ESC + b"B\x05\x00" + ESC + b"C\x42\x0bA"
    assert dots(data) == [(LEFT + 36, 5 * LINE)]
    assert dots(data, form_length_clears_vertical_tabs=True) == [(LEFT + 36, LINE)]


def test_cancel_can_end_one_line_enlarged():
    # Double width strikes each dot twice, a half column apart.
    assert len(dots(b"\x0e\x18A")) == 2
    assert len(dots(b"\x0e\x18A", cancel_ends_one_line_enlarged=True)) == 1


def test_condensed_elite_is_twenty_characters_an_inch():
    data = ESC + b"M\x0fAA"
    assert [x for x, _ in dots(data)] == [LEFT + 30, LEFT + 30 + 360]
    assert [x for x, _ in dots(data, condensed_elite=True)] == [LEFT + 18, LEFT + 18 + 216]


def test_bit_image_mode_7_is_144_dots_an_inch_without_adjacent_dots():
    data = ESC + b"*\x07\x03\x00\x80\x80\x80"
    assert run(data) == []
    assert dots(data, graphics_modes=frozenset(range(8))) == [(LEFT, 0), (LEFT + 60, 0)]


def test_nlq_prints_draft_double_struck_when_the_printer_has_it():
    # Without NLQ, ESC x is an unknown command and the 1 that follows prints.
    assert len(run(ESC + b"x1A")[0].text) == 2
    assert dots(ESC + b"x\x01A", nlq=True) == [(LEFT + 36, 0), (LEFT + 36, 20)]
    assert dots(ESC + b"x\x01" + ESC + b"x\x00A", nlq=True) == [(LEFT + 36, 0)]
