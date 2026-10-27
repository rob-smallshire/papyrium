"""The IBM Proprinter's printer language, for its 9-wire printers."""

from __future__ import annotations

from papyrium.core.language import Language, LanguageIdentity
from papyrium.language.proprinter.interpreter import ProprinterInterpreter
from papyrium.language.proprinter.mechanism import ProprinterMechanism
from papyrium.language.proprinter.nlq import nlq_from_draft

__all__ = [
    "ProprinterInterpreter",
    "ProprinterLanguage",
    "ProprinterMechanism",
    "nlq_from_draft",
]


class ProprinterLanguage(Language):
    """The IBM Proprinter's language, as the 9-wire Proprinter II speaks it.

    Text in 10, 12 and 17.1 cpi and proportional spacing, in draft,
    Fastfont, NLQ (made from the draft characters) and NLQ II, with
    emphasized, double-strike, double-width, underscore, overscore and
    script styles; IBM character sets 1 and 2 and the All Characters
    Chart; bit-image graphics; download characters; form, tab and margin
    control.
    """

    def identity(self) -> LanguageIdentity:
        # Printers that emulate the Proprinter name it so in their IEEE 1284
        # device IDs.
        return LanguageIdentity(name="IBM Proprinter", command_set="IBMPPR")
