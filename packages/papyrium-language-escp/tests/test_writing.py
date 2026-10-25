"""Writing ESC/P jobs in code: text lines and bit-image pictures."""

from helpers import LEFT, dots

from papyrium.language.escp.writing import line, picture


def test_a_line_is_text_and_bytes_then_cr_lf():
    assert line("A", b"\x1bE", "B") == b"A\x1bEB\r\n"


def test_a_picture_prints_its_inked_dots_in_bands_that_meet():
    # A diagonal 3 columns wide and 12 rows deep: two bands of eight pins.
    printed = dots(picture(3, 12, lambda x, y: y == 4 * x, mode=0))
    # Mode 0 is 60 dots an inch (72 units); rows are 1/72 inch (60 units).
    assert sorted(printed) == [(LEFT, 0), (LEFT + 72, 240), (LEFT + 144, 480)]


def test_the_bands_join_without_a_gap():
    printed = dots(picture(1, 16, lambda x, y: True, mode=0))
    assert sorted(y for _, y in printed) == [row * 60 for row in range(16)]
