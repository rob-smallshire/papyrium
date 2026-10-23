"""ESC/P bit-image graphics."""

from helpers import ESC, LEFT, PICA, dots


def test_esc_k_is_sixty_dots_per_inch_top_pin_first():
    assert dots(ESC + b"K\x02\x00\x80\x01") == [(LEFT, 0), (LEFT + 72, 420)]


def test_graphics_advance_the_head():
    assert dots(ESC + b"K\x02\x00\x00\x00A") == [(LEFT + 144 + 36, 0)]


def test_densities():
    assert dots(ESC + b"L\x02\x00\x80\x80") == [(LEFT, 0), (LEFT + 36, 0)]
    assert dots(ESC + b"Y\x02\x00\x80\x80") == [(LEFT, 0), (LEFT + 36, 0)]
    assert dots(ESC + b"Z\x02\x00\x80\x80") == [(LEFT, 0), (LEFT + 18, 0)]
    for mode, step in [(0, 72), (1, 36), (2, 36), (3, 18), (4, 54), (5, 60), (6, 48)]:
        assert dots(ESC + b"*" + bytes([mode]) + b"\x02\x00\x80\x80") == [
            (LEFT, 0),
            (LEFT + step, 0),
        ]


def test_reassigning_a_graphics_command():
    assert dots(ESC + b"?K\x03" + ESC + b"K\x02\x00\x80\x80") == [(LEFT, 0), (LEFT + 18, 0)]


def test_nine_pin_graphics_reach_the_ninth_pin():
    assert dots(ESC + b"^\x00\x01\x00\x80\x80") == [(LEFT, 0), (LEFT, 480)]


def test_graphics_beyond_the_right_margin_are_discarded():
    data = ESC + b"Q\x01" + ESC + b"K\x07\x00" + b"\x80" * 7
    assert dots(data) == [(LEFT + 72 * column, 0) for column in range(6)]


def test_graphics_count_uses_both_bytes():
    data = ESC + b"Z\x00\x01" + b"\x00" * 256 + b"A"
    assert dots(data) == [(LEFT + 256 * 18 + 36, 0)]
