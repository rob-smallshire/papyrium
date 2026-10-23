"""The abstract PrinterModel interface: a particular printer, chosen by the user."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any

from papyrium.core.options import construct
from papyrium.core.page import Page
from papyrium.extension import Extension


class Interpreter(ABC):
    """One job's bytes on their way to pages, as a particular printer would print them.

    An interpreter is fed the job's bytes in arrival order and returns each
    page as soon as it is complete. The pages depend only on the bytes, never
    on how they were split into chunks.
    """

    @abstractmethod
    def feed(self, data: bytes) -> list[Page]:
        """Interpret *data*, returning the pages it completed."""

    @abstractmethod
    def finish(self) -> list[Page]:
        """End the job, returning any part-printed page."""


class PrinterModel(Extension):
    """A specific printer: its command language, character set, paper and mechanics.

    A printer language is not a printer model. Models share language
    interpreters but differ in character ROM, command subset, printable
    area and mechanics; the model is what the user selects. Concrete models
    plug in on the ``papyrium.model`` extension axis, and their options
    model the printer's switches.
    """

    @classmethod
    def _kind(cls) -> str:
        return "model"

    @classmethod
    def from_config(cls, *, name: str, config: Mapping[str, Any]) -> PrinterModel:
        """Build a model from options, which may be strings from a command line.

        The options are kept as :attr:`config` so a job can record exactly
        how its printer was set up.
        """
        model = construct(cls, name=name, config=config)
        model._config = dict(config)
        return model

    @property
    def config(self) -> dict[str, Any]:
        """The options this model was built from, as given."""
        return dict(getattr(self, "_config", {}))

    @abstractmethod
    def create_interpreter(self) -> Interpreter:
        """Start interpreting a new job, with the printer freshly initialised."""
