"""The Brother M-1109 model: conformance, its switches and its Mode I differences."""

import pytest

from papyrium.core.conformance import PrinterModelConformance
from papyrium.exception import ConfigurationError
from papyrium.extension import create_extension, namespace_for
from papyrium.language.escp import CharacterSet
from papyrium.language.escp.charsets import M1109_CHARACTER_SETS
from papyrium.model.brother_m1109 import BrotherM1109

ESC = b"\x1b"

SAMPLE_JOB = (
    ESC
    + b"@"
    + ESC
    + b'E10 PRINT "HELLO"'
    + ESC
    + b"F\r\n"
    + ESC
    + b"x\x01Near letter quality"
    + ESC
    + b"x\x00\r\n"
    + ESC
    + b"M\x0fCondensed elite\x12"
    + ESC
    + b"P\r\n"
    + ESC
    + b"*\x07\x08\x00\x01\x02\x04\x08\x10\x20\x40\x80\r\n"
    + b"\x0c"
    + b"Second page\r\n"
)


class TestBrotherM1109Conformance(PrinterModelConformance):
    def make_model(self):
        return BrotherM1109(name="brother-m1109")

    def sample_job(self):
        return SAMPLE_JOB


def _mechanism(**options):
    return BrotherM1109(name="brother-m1109", **options).mechanism


def test_is_registered_on_the_model_axis():
    model = create_extension("model", namespace_for("model"), "brother-m1109")
    assert isinstance(model, BrotherM1109)


def test_defaults_match_the_factory_switch_settings():
    mechanism = _mechanism()
    assert mechanism.auto_line_feed is False
    assert mechanism.character_set is CharacterSet.USA
    assert mechanism.sheet_length == 11 * 4320
    assert mechanism.skip_perforation_lines == 0
    assert mechanism.slashed_zero is False
    assert mechanism.near_letter_quality is False
    assert mechanism.software_select is False
    assert mechanism.font.name == "m1109-draft"
    assert [font.name for font in mechanism.nlq_fonts] == ["m1109-nlq"]


def test_paper_is_a_letter_cut_sheet_with_the_line_centred():
    mechanism = _mechanism()
    assert mechanism.stationery.name == "sheet"
    assert mechanism.paper_width == 8 * 4320 + 2160
    assert mechanism.left_offset == 4320 // 4


def test_fanfold_is_9_5_inches_wide_by_default():
    mechanism = BrotherM1109(name="brother-m1109", stationery="green-bar").mechanism
    assert mechanism.paper_width == 9 * 4320 + 2160
    assert mechanism.left_offset == 3 * 4320 // 4


def test_the_first_line_is_19_36_inch_below_the_top_of_the_sheet():
    assert _mechanism().top_offset == 4320 * 19 // 36


def test_mode_i_differs_from_the_fx80():
    mechanism = _mechanism()
    assert mechanism.character_sets == M1109_CHARACTER_SETS
    assert mechanism.default_vertical_tabs is False
    assert mechanism.form_length_clears_vertical_tabs is True
    assert mechanism.cancel_ends_one_line_enlarged is True
    assert mechanism.condensed_elite is True
    assert mechanism.nlq is True
    assert 7 in mechanism.graphics_modes
    assert 24 not in mechanism.controls and 27 in mechanism.controls
    assert mechanism.condensed_columns == 136
    # Commands the FX-80 has and the M-1109 lacks.
    assert not {"^", "?", "j", "i", "\x0e", "\x0f"} & mechanism.commands


def test_options_from_strings():
    mechanism = BrotherM1109.from_config(
        name="brother-m1109",
        config={
            "auto-line-feed": "yes",
            "character-set": "norway",
            "form-length": "12",
            "skip-perforation": "yes",
            "slashed-zero": "yes",
            "near-letter-quality": "yes",
            "paper-width": "10",
            "stationery": "fanfold",
            "top-offset": "0.5",
        },
    ).mechanism
    assert mechanism.auto_line_feed is True
    assert mechanism.character_set is CharacterSet.NORWAY
    assert mechanism.sheet_length == 12 * 4320
    assert mechanism.skip_perforation_lines == 6
    assert mechanism.slashed_zero is True
    assert mechanism.near_letter_quality is True
    assert mechanism.paper_width == 10 * 4320
    assert mechanism.stationery.name == "fanfold"
    assert mechanism.top_offset == 2160


@pytest.mark.parametrize(
    "options, message",
    [
        ({"character_set": "atlantis"}, "atlantis"),
        ({"stationery": "papyrus"}, "papyrus"),
        ({"top_offset": "11"}, "top-offset"),
    ],
)
def test_bad_options_are_configuration_errors(options, message):
    with pytest.raises(ConfigurationError, match=message):
        BrotherM1109(name="brother-m1109", **options)


def test_three_lines_sit_centred_in_the_first_band_of_listing_paper():
    from papyrium.core.stationery import BAND_HEIGHT

    model = BrotherM1109(name="brother-m1109", stationery="green-bar")
    interpreter = model.create_interpreter()
    (page,) = interpreter.feed(b"Hg\r\n" * 3 + b"\x0c")
    radius = page.dot_diameter // 2
    top = min(y for _, y in page.dots) - radius
    bottom = max(y for _, y in page.dots) + radius
    # The band runs from 1/2 to 1 inch; the ink has equal room above and below.
    assert top - BAND_HEIGHT == 2 * BAND_HEIGHT - bottom


def test_identity_and_language():
    model = BrotherM1109(name="brother-m1109")
    assert model.identity().display_name == "Brother M-1109"
    assert model.languages() == ("escp",)
