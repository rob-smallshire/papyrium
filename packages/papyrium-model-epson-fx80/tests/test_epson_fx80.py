"""The Epson FX-80 model: conformance and its switch options."""

import pytest

from papyrium.core.conformance import PrinterModelConformance
from papyrium.exception import ConfigurationError
from papyrium.extension import create_extension, namespace_for
from papyrium.language.escp import CharacterSet
from papyrium.model.epson_fx80 import EpsonFx80

SAMPLE_JOB = (
    b"\x1b@"
    b'\x1bE10 PRINT "HELLO"\x1bF\r\n'
    b"\x1b-\x01Underlined\x1b-\x00 \x1b4italic\x1b5 \x0fcondensed\x12\r\n"
    b"\x1bK\x08\x00\x01\x02\x04\x08\x10\x20\x40\x80\r\n"
    b"\x0c"
    b"Second page\r\n"
)


class TestEpsonFx80Conformance(PrinterModelConformance):
    def make_model(self):
        return EpsonFx80(name="epson-fx80")

    def sample_job(self):
        return SAMPLE_JOB


def test_is_registered_on_the_model_axis():
    model = create_extension("model", namespace_for("model"), "epson-fx80")
    assert isinstance(model, EpsonFx80)


def test_defaults_match_the_factory_switch_settings():
    mechanism = EpsonFx80(name="epson-fx80").mechanism
    assert mechanism.auto_line_feed is False
    assert mechanism.character_set is CharacterSet.USA
    assert mechanism.sheet_length == 11 * 4320
    assert mechanism.top_offset == 4320 // 2
    assert mechanism.slashed_zero is False
    assert mechanism.stationery.name == "fanfold"
    assert mechanism.font.name == "draft-9"
    assert mechanism.software_select is False
    assert mechanism.emphasized is False
    assert mechanism.user_defined_characters is True


def test_paper_is_standard_fanfold_with_its_tear_off_strips():
    mechanism = EpsonFx80(name="epson-fx80").mechanism
    assert mechanism.paper_width == 9 * 4320 + 2160
    # The 8-inch line is centred on the 8.5 inches between the strips.
    assert mechanism.left_offset == 3 * 4320 // 4


def test_cut_sheets_are_8_5_inches_wide_by_default():
    mechanism = EpsonFx80(name="m", stationery="sheet").mechanism
    assert mechanism.paper_width == 8 * 4320 + 2160


def test_the_line_is_centred_on_other_widths_of_paper():
    assert EpsonFx80(name="m", paper_width="8.5").mechanism.left_offset == 4320 // 4
    assert EpsonFx80(name="m", paper_width="7").mechanism.left_offset == 0


def test_top_offset_is_where_the_operator_wound_the_paper():
    assert EpsonFx80(name="m", top_offset="1/6").mechanism.top_offset == 720


def test_underlines_below_the_descenders():
    assert EpsonFx80(name="epson-fx80").mechanism.underline_row == 9


def test_options_from_strings():
    model = EpsonFx80.from_config(
        name="epson-fx80",
        config={
            "auto-line-feed": "yes",
            "character-set": "uk",
            "form-length": "12",
            "skip-perforation": "yes",
            "paper-width": "10",
            "top-offset": "0.25",
            "slashed-zero": "yes",
            "stationery": "music-ruled",
            "software-select": "yes",
            "emphasized": "yes",
            "user-defined-characters": "no",
        },
    )
    mechanism = model.mechanism
    assert mechanism.auto_line_feed is True
    assert mechanism.character_set is CharacterSet.UK
    assert mechanism.sheet_length == 12 * 4320
    assert mechanism.skip_perforation_lines == 6
    assert mechanism.paper_width == 10 * 4320
    assert mechanism.top_offset == 4320 // 4
    assert mechanism.slashed_zero is True
    assert mechanism.stationery.name == "music-ruled"
    assert model.config["character-set"] == "uk"
    assert mechanism.software_select is True
    assert mechanism.emphasized is True
    assert mechanism.user_defined_characters is False


def test_character_set_by_number():
    assert EpsonFx80(name="m", character_set="2").mechanism.character_set is CharacterSet.GERMANY


@pytest.mark.parametrize(
    "options, message",
    [
        ({"character_set": "atlantis"}, "atlantis"),
        ({"form_length": "eleven"}, "form-length"),
        ({"font": "no-such-font"}, "no-such-font"),
        ({"top_offset": "-1"}, "top-offset"),
        ({"stationery": "papyrus"}, "papyrus"),
        ({"top_offset": "11"}, "top-offset"),
    ],
)
def test_bad_options_are_configuration_errors(options, message):
    with pytest.raises(ConfigurationError, match=message):
        EpsonFx80(name="epson-fx80", **options)
