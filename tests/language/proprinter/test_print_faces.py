"""ESC I's faces, and how the print modes mask one another."""

from proprinter_helpers import (
    ELITE,
    ESC,
    HALF_ROW,
    LEFT,
    NLQ_STEP,
    PICA,
    PIN,
    STEP,
    dots,
    faces,
)


def test_draft_prints_a_dot_following_a_printed_one_once():
    assert dots(b"C") == [(LEFT + STEP, 0)]


def test_nlq_fills_in_a_vertical_line_half_a_dot_lower():
    assert dots(ESC + b"I\x02B") == [
        (LEFT + 2 * NLQ_STEP, 0),
        (LEFT + 2 * NLQ_STEP, HALF_ROW),
        (LEFT + 2 * NLQ_STEP, PIN),
    ]


def test_nlq_prints_every_dot_of_a_horizontal_line():
    assert dots(ESC + b"I\x02C") == [(LEFT + 2 * NLQ_STEP, 0), (LEFT + 4 * NLQ_STEP, 0)]


def test_double_strike_prints_nlq():
    assert dots(ESC + b"GC") == dots(ESC + b"I\x02C")
    assert dots(ESC + b"G" + ESC + b"HC") == [(LEFT + STEP, 0)]


def test_condensed_masks_nlq():
    assert dots(b"\x0f" + ESC + b"I\x02C") == [(LEFT + 21, 0)]


def test_emphasized_masks_nlq():
    assert dots(ESC + b"E" + ESC + b"I\x02A") == [(LEFT + STEP, 0), (LEFT + STEP + STEP // 2, 0)]


def test_nlq_prints_at_12_cpi():
    assert dots(ESC + b":" + ESC + b"I\x02A") == [(LEFT + 2 * ELITE // 24, 0)]


def test_fastfont_prints_its_own_characters_at_12_cpi():
    assert dots(ESC + b"I\x01AA", **faces()) == [(LEFT + STEP, 0), (LEFT + ELITE + STEP, 0)]


def test_without_fastfont_esc_i_1_prints_draft():
    assert dots(ESC + b"I\x01AA") == [(LEFT + STEP, 0), (LEFT + PICA + STEP, 0)]


def test_nlq_ii_prints_its_own_characters():
    assert dots(ESC + b"I\x03A", **faces()) == [(LEFT + 2 * NLQ_STEP, 0)]


def test_without_nlq_ii_esc_i_3_prints_nlq():
    assert dots(ESC + b"I\x03B") == dots(ESC + b"I\x02B")


def test_esc_i_beyond_7_is_ignored():
    assert dots(ESC + b"I\x08C") == [(LEFT + STEP, 0)]


def test_condensed_with_12_cpi_prints_12_cpi():
    assert dots(ESC + b":\x0fAA") == [(LEFT + 30, 0), (LEFT + ELITE + 30, 0)]


def test_condensed_with_emphasized_prints_emphasized():
    assert dots(b"\x0f" + ESC + b"EAA")[2] == (LEFT + PICA + STEP, 0)


def test_dc2_cancels_condensed_and_12_cpi():
    assert dots(ESC + b":\x0f\x12AA")[1] == (LEFT + PICA + STEP, 0)
