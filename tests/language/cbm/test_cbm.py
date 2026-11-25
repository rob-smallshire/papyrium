"""The Commodore printer language, against the MPS-803's firmware."""

from papyrium.core.page import inches
from papyrium.font.mps803 import Mps803Font
from papyrium.language.cbm import CbmInterpreter, CbmMechanism

FONT = Mps803Font(name="mps803")
STEP = inches(1) // 60
WIRE = inches(1) // 72
LINE = inches(1) // 6
CR, LF, SO, SI, BS, POS, DOWN, RVS_ON, SUB, ESC = (
    bytes([code]) for code in b"\r\n\x0e\x0f\x08\x10\x11\x12\x1a\x1b"
)


def _mechanism(**options):
    return CbmMechanism(font=FONT, left_offset=0, **options)


def run(data, **options):
    interpreter = CbmInterpreter(_mechanism(**options))
    return interpreter.feed(data) + interpreter.finish()


def text(data, **options):
    return [
        (mark.character, mark.x // STEP, mark.y)
        for page in run(data, **options)
        for mark in page.text
    ]


def dots(data, **options):
    (page,) = run(data, **options)
    return sorted(page.dots)


def test_a_character_prints_its_glyph_six_dots_wide():
    assert text(b"A") == [("A", 0, 0)]
    assert {x // STEP for x, _ in dots(b"A")} == {0, 1, 2, 3, 4}
    assert {y // WIRE for _, y in dots(b"A")} == set(range(7))


def test_the_business_set_swaps_the_letters_cases():
    assert text(b"Aa") == [("A", 0, 0), ("♠", 6, 0)]
    assert text(b"A\xc1", business_set=True) == [("a", 0, 0), ("A", 6, 0)]


def test_code_17_chooses_the_business_set_until_the_end_of_the_line():
    assert [c for c, _, _ in text(DOWN + b"A" + CR + b"A")] == ["a", "A"]
    assert [c for c, _, _ in text(DOWN + b"A\x91A")] == ["a", "A"]


def test_double_width_prints_each_column_twice():
    assert text(SO + b"AB" + SI + b"C") == [("A", 0, 0), ("B", 12, 0), ("C", 24, 0)]
    xs = sorted({x // STEP for x, _ in dots(SO + b"A")})
    assert xs == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]


def test_reverse_inverts_the_whole_cell():
    assert len(dots(RVS_ON + b" ")) == 6 * 7


def test_cr_and_lf_end_reverse_and_feed_alike():
    assert dots(RVS_ON + b" " + CR + b" A") == dots(RVS_ON + b" " + LF + b" A")
    assert {y for _, y in dots(RVS_ON + b" " + CR + b"A")} >= {LINE}


def test_quote_mode_prints_controls_as_reversed_glyphs():
    # In quotes RVS ON prints as a reversed R instead of acting.
    marks = text(b'"' + RVS_ON + b'A"A')
    assert [c for c, _, _ in marks] == ['"', "R", "A", '"', "A"]
    reversed_r = [d for d in dots(b'"' + RVS_ON) if 6 * STEP <= d[0] < 12 * STEP]
    assert len(reversed_r) > len(FONT.glyph("R").dots)


def test_a_full_line_wraps_only_when_more_follows():
    assert text(b"A" * 81)[-1] == ("A", 0, LINE)
    # Exactly 80 characters, then CR, feed one line, not two.
    assert text(b"A" * 80 + CR + b"B")[-1] == ("B", 0, LINE)


def test_pos_moves_forwards_only():
    assert text(POS + b"10A") == [("A", 60, 0)]
    assert text(b"A" * 20 + POS + b"05B")[-1] == ("B", 120, 0)


def test_esc_pos_takes_bit_0_of_its_high_byte_and_ignores_480_on():
    assert text(ESC + POS + b"\x01\x00A") == [("A", 256, 0)]
    assert text(ESC + POS + b"\x03\x00A") == [("A", 256, 0)]
    assert text(ESC + POS + b"\x01\xe0A") == [("A", 0, 0)]
    # After ESC, a byte other than POS is swallowed.
    assert text(ESC + b"AB") == [("B", 0, 0)]


def test_bit_image_columns_put_bit_0_at_the_top():
    assert dots(BS + b"\x81\xc0") == [(0, 0), (STEP, 6 * WIRE)]


def test_a_bit_image_line_feeds_7_72_inch():
    pages = run(BS + b"\x81" + CR + b"\x81")
    assert sorted(pages[0].dots)[-1] == (0, 7 * WIRE)


def test_sub_repeats_a_column_in_bit_image_only():
    assert len(dots(BS + SUB + b"\x05\x81")) == 5
    assert text(SUB + b"\x05A") == [("A", 0, 0)]


def test_the_rear_switch_spaces_lines_1_8_inch():
    assert text(b"A" + CR + b"B", line_feed_steps=27)[-1] == ("B", 0, inches(1) // 8)
