"""The abstract Language interface: a printer command language."""

from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass

from papyrium.extension import Extension

#: Characters that delimit an IEEE 1284 device ID, so cannot appear in a token.
_DEVICE_ID_DELIMITERS = frozenset(":;,")


@dataclass(frozen=True)
class LanguageIdentity:
    """Who a command language is, in Papyrium's own terms.

    *name* is the language as people know it, such as ``ESC/P``.
    *command_set* is the token naming it in the command set (``CMD``) of an
    IEEE 1284 device ID, which network printers also advertise.
    """

    name: str
    command_set: str

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("a language identity needs a name")
        if not self.command_set or _DEVICE_ID_DELIMITERS & set(self.command_set):
            raise ValueError(
                f"command_set must be a non-empty token without ':', ';' or ',', "
                f"not {self.command_set!r}"
            )


class Language(Extension):
    """A printer command language, such as ESC/P, Diablo 630 or HP-GL.

    A language is not a printer model: models share a language's
    interpreter and configure it with their own character set, command
    subset and mechanics. Languages plug in on the ``papyrium.language``
    extension axis so the installed ones can be listed and described; a
    model package depends on its language package directly.
    """

    @classmethod
    def _kind(cls) -> str:
        return "language"

    @abstractmethod
    def identity(self) -> LanguageIdentity:
        """Who this language is, for describing and advertising a printer that speaks it."""
