"""Rules and commands the Epson LX-800 adds to the FX-80's."""

from helpers import ESC, LEFT, LINE, dots, run


def _xs(data, **options):
    return sorted({x for x, _ in dots(data, **options)})


def test_master_select_can_set_italic_and_underline():
    # Bit 6 slants the dot of A to the right; bit 7 underlines on row 8.
    upright = dots(b"A")
    assert dots(ESC + b"!\x40A") == upright
    slanted = dots(ESC + b"!\x40A", master_select_italic_underline=True)
    assert slanted[0][0] > upright[0][0]
    underlined = dots(ESC + b"!\x80A", master_select_italic_underline=True)
    assert any(y == 8 * 60 for _, y in underlined)


def test_one_line_double_width_can_end_at_carriage_return():
    data = b"\x0eA\rA"
    assert len(dots(data)) == 4
    assert len(dots(data, carriage_return_ends_one_line_enlarged=True)) == 3


def test_margins_can_clear_the_tab_stops():
    # The head is still at column 0: HT goes to the first stop, 8 columns
    # past the new margin; with the stops cleared it stays put.
    data = ESC + b"l\x02\tA"
    assert _xs(data) == [LEFT + 10 * 432 + 36]
    assert _xs(data, margins_clear_tabs=True) == [LEFT + 36]


def test_nlq_can_keep_emphasized():
    from test_variants import _nlq_font

    options = {"nlq": True, "nlq_fonts": (_nlq_font(),)}
    data = ESC + b"x\x01" + ESC + b"EA"
    assert len(dots(data, **options)) == 2
    assert dots(data, nlq_emphasized=True, **options) == [
        (LEFT, 0),
        (LEFT + 18, 0),
        (LEFT + 18, 20),
        (LEFT + 36, 20),
    ]


def test_esc_e_sets_tab_stops_at_regular_intervals():
    assert _xs(ESC + b"e\x00\x03\tA") == [LEFT + 3 * 432 + 36]
    assert dots(ESC + b"e\x01\x04\x0bA") == [(LEFT + 36, 4 * LINE)]


def test_esc_f_prints_spaces_or_feeds_lines():
    assert dots(ESC + b"f\x00\x05A") == [(LEFT + 5 * 432 + 36, 0)]
    assert dots(b"A" + ESC + b"f\x01\x02A") == [(LEFT + 36, 0), (LEFT + 432 + 36, 2 * LINE)]


def test_esc_em_is_accepted_and_ignored():
    assert dots(ESC + b"\x194A") == dots(b"A")
    (page,) = run(ESC + b"\x194A")
    assert [mark.character for mark in page.text] == ["A"]
