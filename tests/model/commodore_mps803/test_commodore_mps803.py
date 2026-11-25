"""The Commodore MPS-803 model: conformance and options."""

import pytest

from papyrium.core.conformance import PrinterModelConformance
from papyrium.exception import ConfigurationError
from papyrium.extension import create_extension, namespace_for
from papyrium.model.commodore_mps803 import CommodoreMps803


class TestCommodoreMps803Conformance(PrinterModelConformance):
    def make_model(self):
        return CommodoreMps803(name="commodore-mps-803")

    def sample_job(self):
        # No form feed: 70 lines run onto a second 11-inch sheet.
        return b'10 PRINT "HELLO"\r\x0eWIDE\x0f\r\x08\x81\x82\x84\r\x0f' + b"LINE\r" * 70


def test_is_registered_on_the_model_axis():
    model = create_extension("model", namespace_for("model"), "commodore-mps-803")
    assert isinstance(model, CommodoreMps803)


def test_identity_and_language():
    model = CommodoreMps803(name="mps803")
    assert model.identity().display_name == "Commodore MPS-803"
    assert model.languages() == ("cbm",)


def test_secondary_address_7_chooses_the_business_set():
    assert not CommodoreMps803(name="m").mechanism.business_set
    model = CommodoreMps803.from_config(name="m", config={"secondary-address": "7"})
    assert model.mechanism.business_set


def test_line_spacing_sets_the_text_feed():
    model = CommodoreMps803.from_config(name="m", config={"line-spacing": "1/8"})
    assert model.mechanism.line_feed_steps == 27


@pytest.mark.parametrize(("option", "value"), [("secondary-address", "4"), ("line-spacing", "1/7")])
def test_bad_options_are_configuration_errors(option, value):
    with pytest.raises(ConfigurationError, match=option):
        CommodoreMps803.from_config(name="m", config={option: value})
