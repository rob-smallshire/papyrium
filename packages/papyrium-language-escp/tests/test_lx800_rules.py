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


def _nlq(**options):
    from test_variants import _nlq_font

    return {"nlq": True, "nlq_fonts": (_nlq_font(),), "near_letter_quality": True, **options}


FULL_LINE = 80 * 432


def _first_x(data, **options):
    return min(x for x, _ in dots(data, **options))


def test_esc_a_centres_or_right_aligns_a_line():
    # Two NLQ characters, 864 units wide, on an 80-column line.
    assert _first_x(ESC + b"a\x01AA\r", **_nlq()) == LEFT + (FULL_LINE - 864) // 2
    assert _first_x(ESC + b"a\x02AA\r", **_nlq()) == LEFT + FULL_LINE - 864
    assert _first_x(ESC + b"a\x00AA\r", **_nlq()) == LEFT


def test_full_justification_widens_the_spaces():
    data = ESC + b"a\x03A A A\r"
    xs = sorted({x for x, y in dots(data, **_nlq()) if y == 0})
    # The two spaces share the spare room; the last A ends at the margin.
    assert xs[0] == LEFT
    assert xs[-1] == LEFT + FULL_LINE - 432
    assert xs[2] - xs[1] == xs[1] - xs[0]


def test_justification_can_be_for_nlq_only():
    assert _first_x(ESC + b"a\x02AA\r", justify_nlq_only=True) == LEFT + 36
    assert _first_x(ESC + b"a\x02AA\r") == LEFT + FULL_LINE - 864 + 36


def _text(data, **options):
    (page,) = run(data, **options)
    return "".join(mark.character for mark in page.text)


def test_esc_t_chooses_the_ibm_pc_table_for_the_high_codes():
    assert _text(b"\xc1") == "A"  # The italic table: an italic A.
    assert _text(ESC + b"t\x01\xc1\xe0\xb3") == "┴α│"
    assert _text(ESC + b"t\x01" + ESC + b"t\x00\xc1") == "A"


def test_the_ibm_tables_accented_letters_need_esc_6():
    assert _text(ESC + b"t\x01\x80A") == "A"
    assert _text(ESC + b"t\x01" + ESC + b"6\x80\x81") == "Çü"


def test_the_power_on_table_is_the_mechanisms():
    assert _text(b"\xe0", graphics_table=True) == "α"


def test_esc_t_takes_only_the_bytes_0_and_1():
    assert _text(ESC + b"t1\xc1") == "A"


def test_ibm_characters_are_never_italic():
    from papyrium.core.testing import MemoryDotFont

    # α: one dot at column 1 of the top row, which italic would move right.
    blank = "\n".join(["..........."] * 9)
    alpha = "\n".join([".#........."] + ["..........."] * 8)
    font = MemoryDotFont(
        name="alpha", text=f"rows 9\ncolumns 11\nU+0020\n{blank}\n\nU+03B1\n{alpha}\n"
    )
    upright = dots(ESC + b"t\x01\xe0", font=font)
    assert upright == [(LEFT + 36, 0)]
    assert dots(ESC + b"4" + ESC + b"t\x01\xe0", font=font) == upright
