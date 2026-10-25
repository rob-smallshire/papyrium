"""The abstract PrinterModel interface: a particular printer, chosen by the user."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
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


@dataclass(frozen=True)
class ModelIdentity:
    """Who a printer is: its manufacturer and model, as on its case.

    These also name it in an IEEE 1284 device ID (``MFG`` and ``MDL``),
    so neither may contain ``:`` or ``;``.
    """

    manufacturer: str
    model: str

    def __post_init__(self) -> None:
        for field in ("manufacturer", "model"):
            value = getattr(self, field)
            if not value or set(value) & {":", ";"}:
                raise ValueError(f"{field} must be non-empty without ':' or ';', not {value!r}")

    @property
    def display_name(self) -> str:
        """As a person would name the printer, such as ``Brother M-1109``."""
        return f"{self.manufacturer} {self.model}"


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
    def demo(self) -> bytes:
        """A job showing what this printer can do, written by Papyrium itself."""

    @abstractmethod
    def create_interpreter(self) -> Interpreter:
        """Start interpreting a new job, with the printer freshly initialised."""

    @abstractmethod
    def identity(self) -> ModelIdentity:
        """Which printer this is."""

    @abstractmethod
    def languages(self) -> tuple[str, ...]:
        """The command languages this printer accepts as configured, by plug-in name.

        A printer whose switches choose one personality at power-on
        accepts only that one, so this reports the configured printer, not
        every language its model can speak.
        """
