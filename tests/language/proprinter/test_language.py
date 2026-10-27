"""ProprinterLanguage: the Proprinter's language on the language axis."""

from papyrium.core.conformance import LanguageConformance
from papyrium.extension import create_extension, namespace_for
from papyrium.language.proprinter import ProprinterLanguage


class TestProprinterLanguageConformance(LanguageConformance):
    def make_language(self):
        return ProprinterLanguage(name="proprinter")


def test_is_registered_on_the_language_axis():
    language = create_extension("language", namespace_for("language"), "proprinter")
    assert isinstance(language, ProprinterLanguage)


def test_identity_names_the_ibm_proprinter():
    identity = ProprinterLanguage(name="proprinter").identity()
    assert identity.name == "IBM Proprinter"
    assert identity.command_set == "IBMPPR"
