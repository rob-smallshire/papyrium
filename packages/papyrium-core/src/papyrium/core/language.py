"""The abstract Language interface: a printer command language."""

from __future__ import annotations

from papyrium.extension import Extension


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
