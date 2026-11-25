"""The Commodore printers' language, as the MPS-803 speaks it over the serial bus."""

from __future__ import annotations

from papyrium.core.language import Language, LanguageIdentity
from papyrium.language.cbm.interpreter import CbmInterpreter
from papyrium.language.cbm.mechanism import CbmMechanism

__all__ = ["CbmInterpreter", "CbmLanguage", "CbmMechanism"]


class CbmLanguage(Language):
    """The language of Commodore's serial bus printers, as the MPS-803 speaks it.

    PETSCII text in the graphic set (upper case and graphics) or the
    business set (lower and upper case), chosen by the secondary address
    or within a line by codes 17 and 145; double width (SO, SI), reverse
    (RVS ON 18, RVS OFF 146) and quote mode; bit image (BS) with repeated
    columns (SUB); and positioning by column (POS) or dot (ESC POS).
    """

    def identity(self) -> LanguageIdentity:
        return LanguageIdentity(name="Commodore printer", command_set="CBM")
