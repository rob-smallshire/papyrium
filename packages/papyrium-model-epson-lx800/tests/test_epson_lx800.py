"""EpsonLX800: the LX-800's switches, paper and differences from the FX-80."""

import pytest

from papyrium.core.conformance import PrinterModelConformance
from papyrium.exception import ConfigurationError
from papyrium.extension import create_extension, namespace_for
from papyrium.language.escp import CharacterSet
from papyrium.language.escp.charsets import LX800_CHARACTER_SETS
from papyrium.model.epson_lx800 import EpsonLX800

SAMPLE_JOB = (
    b"\x1b@Epson LX-800\r\n\x1bx\x01Near letter quality\x1bx\x00\r\n\x0cSecond page\r\n\x0c"
)


class TestEpsonLX800Conformance(PrinterModelConformance):
    def make_model(self):
        return EpsonLX800(name="epson-lx800")

    def sample_job(self):
        return SAMPLE_JOB


def _mechanism(**options):
    return EpsonLX800(name="epson-lx800", **options).mechanism


def test_is_registered_on_the_model_axis():
    assert isinstance(create_extension("model", namespace_for("model"), "epson-lx800"), EpsonLX800)


def test_identity_and_language():
    model = EpsonLX800(name="epson-lx800")
    assert model.identity().display_name == "Epson LX-800"
    assert model.languages() == ("escp",)


def test_defaults_match_the_factory_switch_settings():
    mechanism = _mechanism()
    assert mechanism.condensed is False
    assert mechanism.slashed_zero is False
    assert mechanism.graphics_table is False
    assert mechanism.near_letter_quality is False
    assert mechanism.character_set is CharacterSet.USA
    assert mechanism.sheet_length == 11 * 4320
    assert mechanism.skip_perforation_lines == 0
    assert mechanism.auto_line_feed is False


def test_fonts_are_the_lx800s_with_no_sans_serif():
    mechanism = _mechanism()
    assert mechanism.font.name == "lx800-draft"
    roman, sans_serif = mechanism.nlq_fonts
    assert roman.name == "lx800-nlq-roman"
    assert sans_serif is None


def test_differs_from_the_fx80():
    mechanism = _mechanism()
    assert mechanism.character_sets == LX800_CHARACTER_SETS
    assert mechanism.nlq and mechanism.condensed_elite
    assert mechanism.default_vertical_tabs is False
    assert mechanism.underline_row == 8
    assert mechanism.prints_adjacent_dots_once
    assert mechanism.master_select_italic_underline
    assert mechanism.carriage_return_ends_one_line_enlarged
    assert mechanism.margins_clear_tabs
    assert mechanism.nlq_emphasized
    assert mechanism.justify_nlq_only
    assert set("xkatef\x19") <= mechanism.commands
    assert not set("Iijp=>#") & mechanism.commands


def test_options_from_strings():
    mechanism = EpsonLX800.from_config(
        name="epson-lx800",
        config={
            "condensed": "yes",
            "slashed-zero": "yes",
            "graphics-table": "yes",
            "near-letter-quality": "yes",
            "character-set": "11",
            "form-length": "12",
            "skip-perforation": "yes",
            "auto-line-feed": "yes",
            "stationery": "sheet",
        },
    ).mechanism
    assert mechanism.condensed and mechanism.slashed_zero and mechanism.graphics_table
    assert mechanism.near_letter_quality and mechanism.auto_line_feed
    assert mechanism.character_set is CharacterSet.SPAIN_II
    assert mechanism.sheet_length == 12 * 4320
    assert mechanism.skip_perforation_lines == 6
    assert mechanism.paper_width == 8 * 4320 + 2160


@pytest.mark.parametrize(
    "options, message",
    [
        ({"character_set": "uk_ii"}, "uk_ii"),
        ({"form_length": "eleven"}, "form-length"),
        ({"stationery": "papyrus"}, "papyrus"),
    ],
)
def test_bad_options_are_configuration_errors(options, message):
    with pytest.raises(ConfigurationError, match=message):
        EpsonLX800(name="epson-lx800", **options)
