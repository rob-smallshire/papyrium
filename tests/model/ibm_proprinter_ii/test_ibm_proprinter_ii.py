"""IBMProprinterII: the Proprinter II's switches, paper and stand-in characters."""

import pytest

from papyrium.core.conformance import PrinterModelConformance
from papyrium.exception import ConfigurationError
from papyrium.extension import create_extension, namespace_for
from papyrium.model.ibm_proprinter_ii import IBMProprinterII

SAMPLE_JOB = (
    b"IBM Proprinter II\r\n\x1bI\x02Near letter quality\x1bI\x00\r\n\x0cSecond page\r\n\x0c"
)


class TestIBMProprinterIIConformance(PrinterModelConformance):
    def make_model(self):
        return IBMProprinterII(name="ibm-proprinter-ii")

    def sample_job(self):
        return SAMPLE_JOB


def _mechanism(**options):
    return IBMProprinterII(name="ibm-proprinter-ii", **options).mechanism


def _text(data, **options):
    interpreter = IBMProprinterII(name="ibm-proprinter-ii", **options).create_interpreter()
    pages = interpreter.feed(data) + interpreter.finish()
    return "".join(mark.character for page in pages for mark in page.text)


def test_is_registered_on_the_model_axis():
    model = create_extension("model", namespace_for("model"), "ibm-proprinter-ii")
    assert isinstance(model, IBMProprinterII)


def test_identity_and_language():
    model = IBMProprinterII(name="ibm-proprinter-ii")
    assert model.identity().display_name == "IBM Proprinter II"
    assert model.languages() == ("proprinter",)


def test_defaults_match_the_us_factory_switch_settings():
    mechanism = _mechanism()
    assert mechanism.sheet_length == 11 * 4320
    assert not mechanism.form_feed_at_top_ignored
    assert not mechanism.auto_line_feed
    assert mechanism.ibm_set == 1
    assert not mechanism.line_feed_returns


def test_the_switches():
    mechanism = _mechanism(
        ignore_top_form_feed=True,
        auto_line_feed=True,
        form_length="12",
        character_set_2=True,
        auto_carriage_return=True,
    )
    assert mechanism.form_feed_at_top_ignored and mechanism.auto_line_feed
    assert mechanism.sheet_length == 12 * 4320
    assert mechanism.ibm_set == 2
    assert mechanism.line_feed_returns


def test_switch_5_chooses_character_set_2():
    assert _text(b"\x80A") == "A"
    assert _text(b"\x80A", character_set_2=True) == "ÇA"


def test_an_eight_inch_line_of_80_pica_or_137_condensed_columns():
    mechanism = _mechanism()
    assert (mechanism.columns, mechanism.condensed_columns) == (80, 137)


def test_the_star_lc10s_characters_stand_in():
    mechanism = _mechanism()
    assert mechanism.font.name == "lc10-draft"
    assert mechanism.fastfont.name == "lc10-draft-elite"
    assert mechanism.nlq_ii_font.name == "lc10-nlq-courier"
    assert mechanism.block_graphics_font.name == "lc10-block-graphics"


def test_fonts_can_be_replaced():
    mechanism = _mechanism(nlq_ii_font="lc10-nlq-sanserif")
    assert mechanism.nlq_ii_font.name == "lc10-nlq-sanserif"


def test_fonts_must_fit_their_faces():
    with pytest.raises(ConfigurationError):
        _mechanism(nlq_ii_font="lc10-draft")
    with pytest.raises(ConfigurationError):
        _mechanism(fastfont="lc10-draft")
