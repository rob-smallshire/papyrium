"""Character sizes, as the Star LC-10 prints them: ESC h, ESC w and ESC [ @.

Enlarged characters are always near letter quality. The test NLQ font's A
has a dot in column 0 of row 0 and one in column 1 of row 1; columns are
1/240 inch apart (18 units), rows 1/144 inch.
"""

from helpers import ESC, LEFT, LINE, PICA, dots
from test_variants import _nlq_font

from papyrium.core.testing import MemoryDotFont

PIN = 60
NLQ = {"nlq": True, "nlq_fonts": (_nlq_font(0),)}


def _sorted(data, **options):
    return sorted(dots(data, **NLQ, **options))


def test_double_size_doubles_rows_into_pins_and_widens_each_column():
    assert _sorted(ESC + b"h\x01A") == [
        (LEFT, 0),
        (LEFT + 36, 0),
        (LEFT + 36, PIN),
        (LEFT + 72, PIN),
    ]


def test_enlarged_characters_print_in_nlq_even_in_draft():
    assert _sorted(ESC + b"h\x01A") == sorted(dots(ESC + b"x\x00" + ESC + b"h\x01A", **NLQ))


def test_double_size_advances_two_columns_and_feeds_two_lines():
    printed = dots(ESC + b"h\x01AA\nA", **NLQ)
    assert printed[4][0] == LEFT + 2 * PICA
    assert printed[8][1] == 2 * LINE


def test_quadruple_size_takes_two_pins_a_row_and_four_columns_a_column():
    # The LC-10 sends each column, ORed with the one before, twice every
    # other column ($D8E2), so its dots repeat across its place and the next's.
    assert _sorted(ESC + b"h\x02A") == sorted(
        [(LEFT + x, y) for x in (0, 36, 72, 108) for y in (0, PIN)]
        + [(LEFT + x, y) for x in (72, 108, 144, 180) for y in (2 * PIN, 3 * PIN)]
    )


def test_quadruple_size_feeds_four_lines():
    assert dots(ESC + b"h\x02A\nA", **NLQ)[16][1] == 4 * LINE


def test_esc_h_0_returns_to_normal_size():
    data = ESC + b"x\x01" + ESC + b"h\x01" + ESC + b"h\x00A"
    assert dots(data, **NLQ) == [(LEFT, 0), (LEFT + 18, 20)]


def _tall_font():
    rows = ["." * 24 for _ in range(18)]
    rows[0] = "#" + rows[0][1:]
    rows[16] = "#" + rows[16][1:]
    return MemoryDotFont(name="tall", text="rows 18\ncolumns 24\nU+0041\n" + "\n".join(rows) + "\n")


TALL = {"nlq": True, "nlq_fonts": (_tall_font(),)}


def test_the_upper_half_keeps_the_top_eight_pins():
    assert sorted(dots(ESC + b"h\x04A", **TALL)) == [(LEFT, 0), (LEFT + 36, 0)]


def test_the_lower_half_moves_the_bottom_up_to_the_line():
    # Row 16 doubles to pin 16; the lower half begins at pin 8.
    assert sorted(dots(ESC + b"h\x03A", **TALL)) == [(LEFT, 8 * PIN), (LEFT + 36, 8 * PIN)]


def test_halves_keep_the_line_spacing():
    assert dots(ESC + b"h\x04A\nA", **TALL)[2][1] == LINE


def test_esc_w_doubles_the_height_keeping_the_base_line_and_spacing():
    data = ESC + b"x\x01\n\n" + ESC + b"w\x01A" + ESC + b"w\x00\nA"
    printed = sorted(dots(data, **NLQ))
    assert printed[0] == (LEFT, 2 * LINE - 8 * PIN)
    # Single width; the next line is one line down.
    assert [x for x, y in printed if y < 3 * LINE] == [LEFT, LEFT + 18]
    assert max(y for _, y in printed) == 3 * LINE + 20


def test_esc_bracket_at_sets_height_spacing_and_width():
    size = ESC + b"[@\x04\x00\x00\x00"
    data = ESC + b"x\x01\n\n" + size + b"\x22\x02A\n" + size + b"\x11\x01A"
    printed = sorted(dots(data, **NLQ))
    assert printed[0] == (LEFT, 2 * LINE - 8 * PIN)
    assert (LEFT + 36, 2 * LINE - 8 * PIN) in printed  # double width
    assert max(y for _, y in printed) == 4 * LINE + 20  # double spacing


def test_a_line_holding_enlarged_characters_feeds_further_after_normal_size_returns():
    assert dots(ESC + b"h\x01A" + ESC + b"h\x00\nA", **NLQ)[4][1] == 2 * LINE
    assert dots(ESC + b"h\x01A" + ESC + b"h\x00\nA\nA", **NLQ)[5][1] == 3 * LINE


def test_double_strike_prints_each_enlarged_band_twice_half_a_dot_apart():
    # The LC-10's sequencer prints each band a second time 3 steps (1/144
    # inch) lower when double-strike is on ($CB65, $CC7A).
    from helpers import mechanism

    from papyrium.model.star_lc10.generator import LC10CharacterGenerator

    options = {"generator": LC10CharacterGenerator()}
    single = _sorted(ESC + b"h\x01A", **options)
    struck = _sorted(ESC + b"G" + ESC + b"h\x01A", **options)
    offset = mechanism(**NLQ, **options).generator.double_strike_offset
    assert struck == sorted(single + [(x, y + offset) for x, y in single])
