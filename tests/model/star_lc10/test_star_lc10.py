"""StarLC10: the LC-10's switches, paper, fonts and character generator."""

import pytest

from papyrium.core.conformance import PrinterModelConformance
from papyrium.extension import create_extension, namespace_for
from papyrium.language.escp import CharacterSet
from papyrium.model.star_lc10 import StarLC10
from papyrium.model.star_lc10.generator import LC10CharacterGenerator
from papyrium.model.star_lc10.interpreter import STANDARD_COMMANDS

SAMPLE_JOB = b"\x1b@Star LC-10\r\n\x1bx\x01Near letter quality\x1bx\x00\r\n\x0cSecond page\r\n\x0c"


class TestStarLC10Conformance(PrinterModelConformance):
    def make_model(self):
        return StarLC10(name="star-lc10")

    def sample_job(self):
        return SAMPLE_JOB


def _mechanism(**options):
    return StarLC10(name="star-lc10", **options).mechanism


def test_is_registered_on_the_model_axis():
    assert isinstance(create_extension("model", namespace_for("model"), "star-lc10"), StarLC10)


def test_identity_and_language():
    model = StarLC10(name="star-lc10")
    assert model.identity().display_name == "Star LC-10"
    assert model.languages() == ("escp", "proprinter")


def test_defaults_match_the_factory_switch_settings():
    mechanism = _mechanism()
    assert mechanism.sheet_length == 11 * 4320
    assert mechanism.character_set == CharacterSet.USA
    assert not mechanism.auto_line_feed
    assert not mechanism.graphics_table
    assert not mechanism.default_vertical_tabs


def test_the_switches_set_page_length_line_feed_graphics_and_character_set():
    mechanism = _mechanism(
        form_length="12", auto_line_feed=True, graphics_table=True, character_set="germany"
    )
    assert mechanism.sheet_length == 12 * 4320
    assert mechanism.auto_line_feed and mechanism.graphics_table
    assert mechanism.character_set == CharacterSet.GERMANY


def test_an_eight_inch_line_of_80_pica_or_137_condensed_columns():
    mechanism = _mechanism()
    assert (mechanism.columns, mechanism.condensed_columns) == (80, 137)


def test_fonts_by_pitch():
    mechanism = _mechanism()
    assert mechanism.font.name == "lc10-draft"
    assert mechanism.elite_font.name == "lc10-draft-elite"
    assert [font.name for font in mechanism.nlq_fonts] == [
        "lc10-nlq-courier",
        "lc10-nlq-sanserif",
        "lc10-nlq-orator-small-capitals",
        "lc10-nlq-orator",
    ]
    assert [font.name for font in mechanism.nlq_elite_fonts] == [
        "lc10-nlq-courier-elite",
        "lc10-nlq-sanserif-elite",
        "lc10-nlq-orator-small-capitals-elite",
        "lc10-nlq-orator-elite",
    ]
    assert mechanism.nlq and mechanism.nlq_elite and mechanism.condensed_elite


def test_prints_with_the_lc10s_character_generator():
    assert isinstance(_mechanism().generator, LC10CharacterGenerator)


@pytest.mark.parametrize("command", ["p", "4", "5", "k", "x", "a", "t", "-", "!", "j"])
def test_obeys_the_standard_mode_commands(command):
    assert command in STANDARD_COMMANDS


def test_ignores_the_commands_it_lacks():
    assert "I" not in STANDARD_COMMANDS
    assert _standard_text(b"\x1bI\x02A") == "A"


def test_block_graphics_are_twelve_dots_high_so_lines_join():
    model = StarLC10(name="star-lc10")
    interpreter = model.create_interpreter()
    # IBM code 0xB3 is a vertical line.
    (page,) = interpreter.feed(b"\x1bt\x01\xb3\r\n\x0c") + interpreter.finish()
    rows = sorted({y for _, y in page.dots})
    pin = 4320 // 72
    assert rows == [rows[0] + n * pin for n in range(12)]


def test_switch_1_2_makes_line_feed_return_the_head():
    assert _mechanism().line_feed_returns
    assert not _mechanism(auto_carriage_return=False).line_feed_returns


def test_spain_prints_an_acute_accent_at_96():
    interpreter = StarLC10(name="star-lc10", character_set="spain").create_interpreter()
    (page,) = interpreter.feed(b"`\r\n\x0c") + interpreter.finish()
    assert [mark.character for mark in page.text] == ["´"]


def test_switch_2_1_lets_the_ram_hold_download_characters():
    assert not _mechanism().user_defined_characters
    mechanism = _mechanism(download_characters=True)
    assert mechanism.user_defined_characters
    assert mechanism.user_set_arguments == 1 and mechanism.user_characters_by_quality


def test_fs_and_the_byte_after_it_are_ignored_in_standard_mode():
    interpreter = StarLC10(name="star-lc10").create_interpreter()
    (page,) = interpreter.feed(b"\x1c4AB\r\n\x0c") + interpreter.finish()
    assert [mark.character for mark in page.text] == ["A", "B"]


def _standard_text(data, **options):
    interpreter = StarLC10(name="star-lc10", **options).create_interpreter()
    pages = interpreter.feed(data + b"\r\n\x0c") + interpreter.finish()
    return "".join(mark.character for page in pages for mark in page.text).strip()


def test_the_ibm_table_starts_in_the_set_switch_1_7_chooses():
    # The firmware's power-on modes ($9060): set #2 with 1-7 off, #1 with it on.
    assert _standard_text(b"\x80A", graphics_table=True) == "ÇA"
    assert _standard_text(b"\x1bt\x01\x80A") == "A"


def test_esc_6_and_7_choose_the_ibm_set_only_while_the_ibm_table_is_in_use():
    assert _standard_text(b"\x1bt\x01\x1b6\x80") == "Ç"
    assert _standard_text(b"\x1b6\x1bt\x01\x80A") == "A"
    assert _standard_text(b"\x1b7\x80A", graphics_table=True) == "A"


def test_ibm_set_2_prints_the_card_suits_and_section_sign():
    assert _standard_text(b"\x03\x04\x05\x06\x15", graphics_table=True) == "♥♦♣♠§"
    assert _standard_text(b"\x03A") == "A"


def _dots(data, **options):
    interpreter = StarLC10(name="star-lc10", **options).create_interpreter()
    return [sorted(p.dots) for p in interpreter.feed(data + b"\r\n\x0c") + interpreter.finish()]


@pytest.mark.parametrize("ibm_mode", [False, True])
@pytest.mark.parametrize("code", [b"\xb3", b"\xdb", b"\xf4"])
def test_block_graphics_are_never_underlined_or_overlined(ibm_mode, code):
    # The column builder skips the lines for characters marked as block
    # graphics ($F81B), in either mode.
    table = b"" if ibm_mode else b"\x1bt\x01"
    lined = b"\x1b-\x01\x1b_\x01"
    assert _dots(table + lined + code, ibm_mode=ibm_mode) == _dots(table + code, ibm_mode=ibm_mode)
    assert _dots(table + lined + b"A", ibm_mode=ibm_mode) != _dots(table + b"A", ibm_mode=ibm_mode)
