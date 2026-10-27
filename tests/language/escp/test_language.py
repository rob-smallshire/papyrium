"""EscpLanguage: the ESC/P plug-in on the language axis."""

from papyrium.core.conformance import LanguageConformance
from papyrium.extension import create_extension, namespace_for
from papyrium.language.escp import EscpLanguage


class TestEscpLanguageConformance(LanguageConformance):
    def make_language(self):
        return EscpLanguage(name="escp")


def test_is_registered_on_the_language_axis():
    assert isinstance(create_extension("language", namespace_for("language"), "escp"), EscpLanguage)


def test_identity_names_esc_p_for_9_pin_printers():
    identity = EscpLanguage(name="escp").identity()
    assert identity.name == "ESC/P"
    assert identity.command_set == "ESCP9"
