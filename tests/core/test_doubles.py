"""The test doubles meet their axes' contracts."""

from papyrium.core.conformance import OutputConformance, PrinterModelConformance
from papyrium.core.testing import ByteDotModel, JsonOutput


class TestByteDotModelConformance(PrinterModelConformance):
    def make_model(self):
        return ByteDotModel(name="byte-dot")

    def sample_job(self):
        return b"HELLO\x0cWORLD"


class TestJsonOutputConformance(OutputConformance):
    def make_output(self):
        return JsonOutput(name="json")


def test_model_keeps_its_config():
    model = ByteDotModel.from_config(name="byte-dot", config={"width": "100"})
    assert model.config == {"width": "100"}


def test_language_identity_rejects_device_id_delimiters():
    import pytest

    from papyrium.core.language import LanguageIdentity

    with pytest.raises(ValueError, match="command_set"):
        LanguageIdentity(name="ESC/P", command_set="ESCP;9")
    with pytest.raises(ValueError, match="name"):
        LanguageIdentity(name="", command_set="ESCP9")


def test_model_identity_gives_a_display_name_and_rejects_device_id_delimiters():
    import pytest

    from papyrium.core.model import ModelIdentity

    assert ModelIdentity(manufacturer="Brother", model="M-1109").display_name == "Brother M-1109"
    with pytest.raises(ValueError, match="model"):
        ModelIdentity(manufacturer="Brother", model="M:1109")
    with pytest.raises(ValueError, match="manufacturer"):
        ModelIdentity(manufacturer="", model="M-1109")
