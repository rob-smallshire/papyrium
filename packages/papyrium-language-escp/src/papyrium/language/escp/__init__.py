"""The Epson ESC/P printer language for 9-pin dot-matrix printers."""

from __future__ import annotations

from papyrium.core.language import Language, LanguageIdentity
from papyrium.language.escp.charsets import CharacterSet, parse_character_set
from papyrium.language.escp.interpreter import EscpInterpreter
from papyrium.language.escp.mechanism import EscpMechanism

__version__ = "0.1.0"

__all__ = [
    "CharacterSet",
    "EscpInterpreter",
    "EscpLanguage",
    "EscpMechanism",
    "parse_character_set",
]


class EscpLanguage(Language):
    """Epson ESC/P, as spoken by 9-pin dot-matrix printers such as the FX-80.

    Text in pica, elite, condensed and proportional pitch with emphasized,
    double-strike, double-width, italic, underline and script styles;
    international character sets; bit-image graphics; user-defined
    characters; form, tab and margin control.
    """

    def identity(self) -> LanguageIdentity:
        # Epson's 9-pin printers name ESC/P in their IEEE 1284 device IDs so.
        return LanguageIdentity(name="ESC/P", command_set="ESCP9")
