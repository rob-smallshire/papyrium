"""The Centronics GLP and the printers made from it: conformance, switches and rules."""

import pytest

from papyrium.core.conformance import PrinterModelConformance
from papyrium.core.page import inches
from papyrium.exception import ConfigurationError
from papyrium.extension import create_extension, namespace_for
from papyrium.language.escp import CharacterSet
from papyrium.model.centronics_glp import BrotherM1009, CentronicsGlp, SchneiderNlq401

ESC = b"\x1b"

SAMPLE_JOB = (
    ESC
    + b"E"
    + b'10 PRINT "HELLO"'
    + ESC
    + b"F\r\n"
    + b"\x0fCondensed\x12\r\n"
    + ESC
    + b"=\x16\x1a\x1c\x00 boxed\r\n"
    + b"\x0c"
    + b"Second page\r\n"
)

MODELS = [
    ("centronics-glp", CentronicsGlp, "Centronics GLP"),
    ("schneider-nlq401", SchneiderNlq401, "Schneider NLQ 401"),
    ("brother-m1009", BrotherM1009, "Brother M-1009"),
]


class TestCentronicsGlpConformance(PrinterModelConformance):
    def make_model(self):
        return CentronicsGlp(name="centronics-glp")

    def sample_job(self):
        return SAMPLE_JOB


class TestSchneiderNlq401Conformance(PrinterModelConformance):
    def make_model(self):
        return SchneiderNlq401(name="schneider-nlq401")

    def sample_job(self):
        return SAMPLE_JOB


class TestBrotherM1009Conformance(PrinterModelConformance):
    def make_model(self):
        return BrotherM1009(name="brother-m1009")

    def sample_job(self):
        return SAMPLE_JOB


def _pages(model, data):
    interpreter = model.create_interpreter()
    return interpreter.feed(data) + interpreter.finish()


@pytest.mark.parametrize(("name", "model_class", "display_name"), MODELS)
def test_is_registered_on_the_model_axis(name, model_class, display_name):
    assert type(create_extension("model", namespace_for("model"), name)) is model_class


@pytest.mark.parametrize(("name", "model_class", "display_name"), MODELS)
def test_identity_and_language(name, model_class, display_name):
    model = model_class(name=name)
    assert model.identity().display_name == display_name
    assert model.languages() == ("escp",)


def test_switches_at_their_delivered_settings():
    mechanism = CentronicsGlp(name="glp").mechanism
    assert mechanism.character_set is CharacterSet.GERMANY
    assert mechanism.sheet_length == inches(11)
    assert not mechanism.near_letter_quality
    assert not mechanism.seven_bit_input
    assert mechanism.power_on_line_spacing == inches(1) // 6


def test_the_nlq401_powers_on_in_nlq_receiving_seven_bits_on_a4():
    mechanism = SchneiderNlq401(name="nlq401").mechanism
    assert mechanism.near_letter_quality
    assert mechanism.seven_bit_input
    assert mechanism.paper_width == inches(83) // 10


def test_the_nlq401s_switch_2_spaces_lines_1_8_inch():
    model = SchneiderNlq401.from_config(name="nlq401", config={"line-spacing": "1/8"})
    assert model.mechanism.power_on_line_spacing == inches(1) // 8


def test_the_m1009_has_no_near_letter_quality():
    mechanism = BrotherM1009(name="m1009").mechanism
    assert not mechanism.nlq
    assert {"x", "I"}.isdisjoint(mechanism.commands)


def test_a_byte_with_bit_7_prints_graphics_on_the_glp_and_ascii_on_the_nlq401():
    # 0xB0 is the CPC's alpha on the GLP; the NLQ401 hears 0.
    glp = _pages(CentronicsGlp(name="glp"), b"\xb0")
    nlq401 = _pages(SchneiderNlq401(name="nlq401", near_letter_quality=False), b"\xb0")
    assert [mark.character for mark in glp[0].text] == ["α"]
    assert [mark.character for mark in nlq401[0].text] == ["0"]


def test_esc_equals_reaches_the_graphics_from_seven_bits():
    pages = _pages(SchneiderNlq401(name="nlq401"), ESC + b"=\x30\x00A")
    assert [mark.character for mark in pages[0].text] == ["α", "A"]


def test_character_set_2_prints_german_characters_until_esc_7():
    pages = _pages(CentronicsGlp(name="glp"), b"[" + ESC + b"7[")
    assert [mark.character for mark in pages[0].text] == ["Ä", "["]


@pytest.mark.parametrize(
    ("option", "value", "message"),
    [("character-set", "3", "character-set"), ("line-spacing", "1/7", "line-spacing")],
)
def test_bad_options_are_configuration_errors(option, value, message):
    with pytest.raises(ConfigurationError, match=message):
        SchneiderNlq401.from_config(name="nlq401", config={option: value})


def test_the_glp_has_no_line_spacing_switch():
    with pytest.raises(ConfigurationError, match="line-spacing"):
        CentronicsGlp.from_config(name="glp", config={"line-spacing": "1/8"})
