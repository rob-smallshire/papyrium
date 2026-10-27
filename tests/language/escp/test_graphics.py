"""ESC/P bit-image graphics."""

from helpers import ESC, LEFT, PICA, dots


def test_esc_k_is_sixty_dots_per_inch_top_pin_first():
    assert dots(ESC + b"K\x02\x00\x80\x01") == [(LEFT, 0), (LEFT + 72, 420)]


def test_graphics_advance_the_head():
    assert dots(ESC + b"K\x02\x00\x00\x00A") == [(LEFT + 144 + 36, 0)]


def test_densities():
    # The pins alternate so that no density drops a dot.
    assert dots(ESC + b"L\x02\x00\x80\x40") == [(LEFT, 0), (LEFT + 36, 60)]
    assert dots(ESC + b"Y\x02\x00\x80\x40") == [(LEFT, 0), (LEFT + 36, 60)]
    assert dots(ESC + b"Z\x02\x00\x80\x40") == [(LEFT, 0), (LEFT + 18, 60)]
    for mode, step in [(0, 72), (1, 36), (2, 36), (3, 18), (4, 54), (5, 60), (6, 48)]:
        assert dots(ESC + b"*" + bytes([mode]) + b"\x02\x00\x80\x40") == [
            (LEFT, 0),
            (LEFT + step, 60),
        ]


def test_reassigning_a_graphics_command():
    assert dots(ESC + b"?K\x03" + ESC + b"K\x02\x00\x80\x40") == [(LEFT, 0), (LEFT + 18, 60)]


def test_nine_pin_graphics_reach_the_ninth_pin():
    assert dots(ESC + b"^\x00\x01\x00\x80\x80") == [(LEFT, 0), (LEFT, 480)]


def test_graphics_beyond_the_right_margin_are_discarded():
    data = ESC + b"Q\x02" + ESC + b"K\x0d\x00" + b"\x80" * 13
    assert dots(data) == [(LEFT + 72 * column, 0) for column in range(12)]


def test_graphics_count_uses_both_bytes():
    data = ESC + b"Z\x00\x01" + b"\x00" * 256 + b"A"
    assert dots(data) == [(LEFT + 256 * 18 + 36, 0)]


def test_high_speed_densities_drop_the_second_of_two_adjacent_dots():
    for command, step in ((b"Y", 36), (b"Z", 18)):
        data = ESC + command + b"\x04\x00\x81\x81\x01\x80"
        assert dots(data) == [(LEFT, 0), (LEFT, 420), (LEFT + 2 * step, 420), (LEFT + 3 * step, 0)]


def test_low_speed_double_density_prints_adjacent_dots():
    assert dots(ESC + b"L\x02\x00\x80\x80") == [(LEFT, 0), (LEFT + 36, 0)]
