"""Rules of the Centronics GLP's firmware, as the Schneider NLQ401 has them."""

from helpers import ESC, LEFT, LINE, PICA, dots

from papyrium.core.testing import MemoryDotFont
from papyrium.language.escp import CharacterSet

# A full block: one dot, column 1 row 3.
BLOCK_FONT = MemoryDotFont(
    "glp-blocks",
    text="rows 8\ncolumns 11\n\nU+2588\n"
    + "...........\n" * 3
    + ".#.........\n"
    + "...........\n" * 4,
)

#: Codes 128-255: the full block at 0xC1, the others blank.
HIGH = "".join("█" if code == 0xC1 else " " for code in range(0x80, 0x100))

GLP = {
    "seven_bit_input": True,
    "high_shift_until_nul": True,
    "high_characters": HIGH,
    "high_codes_printable": True,
    "block_graphics_font": BLOCK_FONT,
}


def test_bit_7_of_every_byte_is_dropped():
    assert dots(b"\xc1", seven_bit_input=True) == dots(b"A")


def test_esc_equals_prints_the_codes_above_128_until_a_nul():
    assert dots(ESC + b"=A", **GLP) == [(LEFT + 36, 3 * 60)]
    assert dots(ESC + b"=A\x00A", **GLP) == [(LEFT + 36, 3 * 60), (LEFT + PICA + 36, 0)]


def test_inside_esc_equals_even_carriage_return_prints():
    # CR arrives as 0x8D, a graphics character, so the line goes on.
    assert dots(ESC + b"=\rA", **GLP) == [(LEFT + PICA + 36, 3 * 60)]


def test_esc_6_and_7_can_choose_character_sets():
    sets = {"esc_6_and_7_select": (CharacterSet.UK, CharacterSet.USA)}
    assert dots(ESC + b"6#", **sets) == dots(b"#", character_set=CharacterSet.UK)
    assert dots(ESC + b"6" + ESC + b"7#", **sets) == dots(b"#")


def test_esc_i_can_select_near_letter_quality():
    from test_variants import _nlq_font

    options = {"nlq": True, "nlq_fonts": (_nlq_font(),), "esc_i_selects_nlq": True}
    nlq = dots(ESC + b"x\x01A", **options)
    assert dots(ESC + b"I\x03A", **options) == nlq
    assert dots(ESC + b"I\x03" + ESC + b"I\x01A", **options) == dots(b"A", **options)
    assert dots(ESC + b"I\x03" + ESC + b"I\x02A", **options) == nlq


def test_esc_a_can_store_a_spacing_for_esc_2_to_select():
    options = {"esc_a_stores_for_esc_2": True}
    assert dots(ESC + b"A\x18\nA", **options) == [(LEFT + 36, LINE)]
    assert dots(ESC + b"A\x18" + ESC + b"2\nA", **options) == [(LEFT + 36, 2 * LINE)]
    assert dots(ESC + b"2\nA", **options) == [(LEFT + 36, LINE)]


def test_esc_3_can_ignore_zero():
    assert dots(ESC + b"3\x00\nA", esc_3_ignores_zero=True) == [(LEFT + 36, LINE)]


def test_on_off_arguments_can_go_by_their_lowest_bit():
    from test_variants import _nlq_font

    options = {"nlq": True, "nlq_fonts": (_nlq_font(),)}
    assert dots(ESC + b"x\x03A", **options) == dots(b"A", **options)
    assert dots(ESC + b"x\x03A", flags_by_lowest_bit=True, **options) == dots(
        ESC + b"x\x01A", **options
    )
