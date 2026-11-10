"""The Panasonic KX-P1080 and KX-P1080U: switches, fonts and Panasonic's commands."""

import pytest

from papyrium.core.conformance import PrinterModelConformance
from papyrium.exception import ConfigurationError
from papyrium.extension import create_extension, namespace_for
from papyrium.font.kx_p1080 import (
    KXP1080DraftFont,
    KXP1080DraftItalicFont,
    KXP1080NlqFont,
    KXP1080NlqItalicFont,
)
from papyrium.language.escp import CharacterSet
from papyrium.model.panasonic_kx_p1080 import PanasonicKXP1080, PanasonicKXP1080U

SAMPLE_JOB = b"\x1b@Panasonic KX-P1080U\r\n\x1bnNear letter quality\x1bP\r\n\x0cSecond page\r\n\x0c"

#: Page units: a 1/120 inch column, a pin (1/72 inch), and the 1/216 inch
#: the second pass of NLQ and of double strike prints below the first.
COLUMN, PIN, PASS = 36, 60, 20
PICA = 432

DRAFT = KXP1080DraftFont(name="kx-p1080-draft")
DRAFT_ITALIC = KXP1080DraftItalicFont(name="kx-p1080-draft-italic")
NLQ = KXP1080NlqFont(name="kx-p1080-nlq")
NLQ_ITALIC = KXP1080NlqItalicFont(name="kx-p1080-nlq-italic")


class TestPanasonicKXP1080UConformance(PrinterModelConformance):
    def make_model(self):
        return PanasonicKXP1080U(name="panasonic-kx-p1080u")

    def sample_job(self):
        return SAMPLE_JOB


class TestPanasonicKXP1080Conformance(PrinterModelConformance):
    def make_model(self):
        return PanasonicKXP1080(name="panasonic-kx-p1080")

    def sample_job(self):
        return SAMPLE_JOB


def _dots(data, **options):
    """The dots of the first page, relative to the first dot's column and the top row."""
    interpreter = PanasonicKXP1080U(name="kx", **options).create_interpreter()
    pages = interpreter.feed(b"\x1b@" + data + b"\r\n\x0c") + interpreter.finish()
    return sorted(pages[0].dots)


def _relative(dots):
    left = min(x for x, _ in dots)
    top = min(y for _, y in dots)
    return {(x - left, y - top) for x, y in dots}


def _advance(prefix, **options):
    """The distance between two H's printed after *prefix*: the second H
    starts at the first column of dots that one H alone does not have."""
    one = {x for x, _ in _dots(prefix + b"H", **options)}
    two = {x for x, _ in _dots(prefix + b"HH", **options)}
    return min(two - one) - min(one)


def _nlq_y(row):
    """Where an NLQ glyph's *row* prints: its pin, and the second pass
    1/216 inch lower ($4850)."""
    return (row // 2) * PIN + (row % 2) * PASS


def test_are_registered_on_the_model_axis():
    models = (("panasonic-kx-p1080", PanasonicKXP1080), ("panasonic-kx-p1080u", PanasonicKXP1080U))
    for name, cls in models:
        assert isinstance(create_extension("model", namespace_for("model"), name), cls)


def test_identity_and_language():
    model = PanasonicKXP1080U(name="kx")
    assert model.identity().display_name == "Panasonic KX-P1080U"
    assert PanasonicKXP1080(name="kx").identity().display_name == "Panasonic KX-P1080"
    assert model.languages() == ("escp",)


def test_the_u_ships_with_england_and_the_us_model_with_usa():
    assert PanasonicKXP1080U(name="kx").mechanism.character_set is CharacterSet.UK
    assert PanasonicKXP1080(name="kx").mechanism.character_set is CharacterSet.USA


def test_fonts_are_the_kx_p1080s():
    mechanism = PanasonicKXP1080U(name="kx").mechanism
    assert mechanism.font.name == "kx-p1080-draft"
    assert [font.name for font in mechanism.nlq_fonts] == ["kx-p1080-nlq"]


def test_commands_are_the_manuals():
    commands = PanasonicKXP1080U(name="kx").mechanism.commands
    assert set("!#*-0123456789<=>?@ABCDEFGHJKLMNOPQRSTUWYZ^aeflnopswxyz") <= commands
    assert not set("$\\&%:j tIikb/m") & commands


def test_bel_is_not_a_control():
    assert 7 not in PanasonicKXP1080U(name="kx").mechanism.controls


@pytest.mark.parametrize("n, pitch", [(0, PICA), (1, 360), (2, 288), (3, 252), (ord("2"), 288)])
def test_esc_w_selects_the_pitch(n, pitch):
    assert _advance(b"\x1bw" + bytes([n])) == pitch


def test_esc_w_3s_compressed_is_not_masked_by_emphasized():
    assert _advance(b"\x1bw\x03\x1bE") == 252
    # SI's compressed is, returning when emphasized ends.
    assert _advance(b"\x0f\x1bE") == PICA


def test_semi_compressed_and_emphasized_whichever_came_last():
    assert _advance(b"\x1bE\x1bw\x02") == 288
    assert _advance(b"\x1bw\x02\x1bE") == PICA


def test_esc_m_and_p_return_to_draft_and_cancel_compressed():
    assert _advance(b"\x0f\x1bM") == 360
    dots = _dots(b"\x1bn\x1bPH")
    assert all(y % PIN == 0 for _, y in _relative(dots))


def test_draft_prints_the_roms_characters():
    dots = _relative(_dots(b"H"))
    expected = {(c * COLUMN, r * PIN) for c, r in DRAFT.glyph("H").dots}
    assert dots == expected


def test_draft_j_lowers_only_its_hook_onto_the_ninth_pin():
    rows = {y // PIN for _, y in _relative(_dots(b"j"))}
    assert rows == {row for _, row in DRAFT.glyph("j").dots} and 8 in rows


def test_italic_prints_the_roms_draft_italics_unslanted():
    dots = _relative(_dots(b"\x1b4l"))
    expected = _relative({(c * COLUMN, r * PIN) for c, r in DRAFT_ITALIC.glyph("l").dots})
    assert dots == expected


def test_codes_160_to_254_print_draft_italics():
    assert _relative(_dots(b"\xec")) == _relative(_dots(b"\x1b4l"))


def test_esc_n_and_x_print_nlq_in_two_passes():
    for command in (b"\x1bn", b"\x1bx\x01"):
        dots = _relative(_dots(command + b"H"))
        expected = _relative({(c * 18, _nlq_y(r)) for c, r in NLQ.glyph("H").dots})
        assert dots == expected


def test_esc_o_prints_nlq_elite():
    assert _advance(b"\x1bo") == 360
    assert any(y % PIN for _, y in _relative(_dots(b"\x1boH")))


def test_nlq_italic_prints_the_slanted_columns():
    dots = _relative(_dots(b"\x1bn\x1b4l"))
    expected = _relative({(c * 18, _nlq_y(r)) for c, r in NLQ_ITALIC.glyph("l").dots})
    assert dots == expected


def test_master_select_has_no_proportional_bit():
    assert _advance(b"\x1b!\x02") == PICA
    assert _advance(b"\x1b!\x01") == 360


def _proportional(text):
    interpreter = PanasonicKXP1080U(name="kx").create_interpreter()
    pages = interpreter.feed(b"\x1b@\x1bp\x01" + text + b"\r\n\x0c") + interpreter.finish()
    return pages[0]


def test_proportional_widths_and_placement_are_the_roms():
    # "I" is 8 columns, its glyph moved a column left to start in column 1;
    # "!" follows, its glyph's column 4 moved three left to column 1 of its own.
    xs = sorted({x for x, _ in _proportional(b"I!").dots})
    i_xs = sorted({x for x, _ in _proportional(b"I").dots})
    bang = min(set(xs) - set(i_xs))
    assert bang - i_xs[0] == 8 * COLUMN


def test_a_proportional_h_moves_one_column_right():
    plain = min(x for x, _ in _dots(b"H"))
    proportional = min(x for x, _ in _proportional(b"H").dots)
    assert proportional - plain == COLUMN


def test_proportional_advance_follows_the_width_table():
    # "i" is 8 columns and "w" 12, where both manuals print 13.
    after_i = max(x for x, _ in _proportional(b"HiH").dots)
    after_w = max(x for x, _ in _proportional(b"HwH").dots)
    assert after_w - after_i == (12 - 8) * COLUMN


def test_esc_y_downloads_a_character_and_esc_z_releases_it():
    columns = bytes([0xFF, 0, 0x81, 0, 0x81, 0, 0x81, 0, 0xFF])
    dots = _relative(_dots(b"\x1byA" + columns + b"A"))
    assert (0, 0) in dots and (0, 7 * PIN) in dots and (8 * COLUMN, 0) in dots
    assert _relative(_dots(b"\x1byA" + columns + b"\x1bzAA")) == _relative(_dots(b"A"))


def test_a_download_drops_a_dot_that_follows_one():
    dots = _relative(_dots(b"\x1byA" + bytes([0x80, 0x80, 0, 0, 0, 0, 0, 0, 0]) + b"A"))
    assert dots == {(0, 0)}


def test_the_nlq_position_keeps_nlq_against_commands():
    dots = _relative(_dots(b"\x1bx\x00\x1bPH", print_mode="nlq"))
    assert any(y % PIN for _, y in dots)


def test_the_comp_position_keeps_compressed():
    assert _advance(b"", print_mode="comp") == 252
    assert _advance(b"\x12\x1bE\x1bp\x01", print_mode="comp") == 252


def test_seven_bit_data_clears_bit_7():
    assert _relative(_dots(b"\xc8", data_bits="7")) == _relative(_dots(b"H"))


def test_options_from_strings():
    mechanism = PanasonicKXP1080U.from_config(
        name="kx",
        config={
            "character-set": "germany",
            "form-length": "12",
            "skip-perforation": "yes",
            "auto-line-feed": "yes",
            "stationery": "sheet",
        },
    ).mechanism
    assert mechanism.character_set is CharacterSet.GERMANY
    assert mechanism.sheet_length == 12 * 4320
    assert mechanism.skip_perforation_lines == 6
    assert mechanism.auto_line_feed


@pytest.mark.parametrize(
    "options, message",
    [
        ({"print_mode": "fast"}, "print-mode"),
        ({"data_bits": "9"}, "data-bits"),
        ({"character_set": "uk_ii"}, "uk_ii"),
    ],
)
def test_bad_options_are_configuration_errors(options, message):
    with pytest.raises(ConfigurationError, match=message):
        PanasonicKXP1080U(name="kx", **options)


def test_code_255_prints_an_italic_slashed_zero_after_esc_6():
    dots = _relative(_dots(b"\x1b6\xff"))
    expected = _relative({(c * COLUMN, r * PIN) for c, r in DRAFT_ITALIC.glyph("0̸").dots})
    assert dots == expected
    assert not _dots(b"\xff")


BOX = bytes([0xFF, 0, 0x81, 0, 0x81, 0, 0x81, 0, 0xFF])
BOX_DOTS = {(0, 0), (0, 7 * PIN), (8 * COLUMN, 0), (8 * COLUMN, 7 * PIN)}


def test_a_download_replaces_the_code_received_whatever_the_national_set():
    # Defined in the USA set, it still replaces code 35 in England's, where
    # the ROM's character for 35 is the pound sign.
    assert BOX_DOTS <= _relative(_dots(b"\x1bR\x00\x1by#" + BOX + b"\x1bR\x03#"))


def test_under_italic_a_download_is_found_at_the_code_plus_128():
    # A download at "A" does not replace an italic A ...
    italic_a = _relative(_dots(b"\x1b4A"))
    assert _relative(_dots(b"\x1byA" + BOX + b"\x1b4A")) == italic_a
    # ... one at 0xC1 does, and prints for code 0xC1 too, upright.
    assert BOX_DOTS <= _relative(_dots(b"\x1by\xc1" + BOX + b"\x1b4A"))
    assert BOX_DOTS <= _relative(_dots(b"\x1by\xc1" + BOX + b"\xc1"))


def test_a_download_prints_in_draft_struck_twice_in_nlq():
    draft = _relative(_dots(b"\x1byA" + BOX + b"A"))
    nlq = _relative(_dots(b"\x1bn\x1byA" + BOX + b"A"))
    assert nlq == {(x, y + d) for x, y in draft for d in (0, PASS)}


def test_a_download_keeps_the_fixed_pitch_in_proportional_spacing():
    assert _advance(b"\x1byH" + BOX + b"\x1bp\x01") == PICA


def test_codes_up_to_31_and_127_cannot_be_downloaded():
    # The command ends at the code, and the nine bytes print as text.
    for code in (b"\x1f", b"\x7f"):
        assert _relative(_dots(b"\x1by" + code + b"HHHHHHHHH")) == _relative(_dots(b"HHHHHHHHH"))


def test_at_most_forty_downloads_are_held():
    data = b"".join(b"\x1by" + bytes([0x21 + n]) + BOX for n in range(40))
    # A forty-first ends at its code, and its nine bytes print as text.
    dots = _dots(data + b"\x1byZHHHHHHHHH")
    assert dots == _dots(data + b"HHHHHHHHH")


def test_nlq_takes_its_proportional_placement_from_its_own_tables():
    # The draft table moves W a column right; NLQ's ($5D70) leaves it in place.
    fixed = min(x for x, _ in _dots(b"\x1bnW"))
    proportional = min(x for x, _ in _proportional(b"\x1bnW").dots)
    assert proportional == fixed


def _pages(data, **options):
    interpreter = PanasonicKXP1080U(name="kx", **options).create_interpreter()
    return interpreter.feed(b"\x1b@" + data) + interpreter.finish()


def _form_feed_distance(setup):
    """How far down the paper B prints from A, after *setup*, A, a line
    feed and a form feed, across sheets."""
    tops = []
    for number, page in enumerate(_pages(setup + b"A\r\n\x0cB\r\n\x0c")):
        rows = sorted({y for _, y in page.dots})
        if rows:
            # A and B each print rows 0-6 of a 9-pin cell; a sheet may hold both.
            starts = [rows[0]] + [b for a, b in zip(rows, rows[1:]) if b - a > 6 * PIN]
            tops.extend(number * page.height + start for start in starts)
    return tops[1] - tops[0]


def test_esc_c_takes_lines_without_bit_7():
    assert _form_feed_distance(b"\x1bC\x8c") == _form_feed_distance(b"\x1bC\x0c") == 2 * 4320


def test_esc_c_0_takes_inches_from_1_to_22_and_ignores_others():
    eleven = _form_feed_distance(b"")
    assert _form_feed_distance(b"\x1bC\x00\x03") == _form_feed_distance(b"\x1bC\x12")
    for inches in (0, 23):
        assert _form_feed_distance(b"\x1bC\x00" + bytes([inches])) == eleven


def test_esc_c_is_ignored_entirely_with_no_line_spacing():
    # Nothing changes, the vertical tab stops included.
    assert _form_feed_distance(b"\x1b3\x00\x1bC\x0c\x1b2") == _form_feed_distance(b"")


def _vt_drop(setup):
    """How far a VT after *setup* moves down: A and B both end on row 6."""
    return max(y for _, y in _dots(setup + b"A\x0bB")) - max(y for _, y in _dots(setup + b"A"))


def test_esc_e_1_0_makes_vt_print_without_feeding():
    assert _vt_drop(b"\x1be\x01\x00") == 0


def test_esc_e_1_1_makes_vt_a_line_feed():
    assert _vt_drop(b"\x1be\x01\x01") == _vt_drop(b"")


def test_esc_e_0_0_cancels_the_horizontal_stops():
    tabbed = min(x for x, _ in _dots(b"\tA"))
    assert min(x for x, _ in _dots(b"\x1be\x00\x00\tA")) < tabbed
