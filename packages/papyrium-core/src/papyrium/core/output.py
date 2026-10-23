"""The abstract Output interface: turning pages into documents."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from papyrium.core.options import construct
from papyrium.core.page import Page
from papyrium.extension import Extension


class Document(ABC):
    """One job's pages on their way into an output's files."""

    @abstractmethod
    def add_page(self, page: Page) -> None:
        """Add the next page of the job."""

    @abstractmethod
    def close(self) -> list[Path]:
        """Finish the document, returning the files written for the whole job.

        A document that received no pages writes no files.
        """


class Output(Extension):
    """Renders pages from the page model into files: images, PDF, and so on.

    Outputs are synchronous and deterministic: the same pages always give
    byte-identical files. Concrete outputs plug in on the
    ``papyrium.output`` extension axis.
    """

    @classmethod
    def _kind(cls) -> str:
        return "output"

    @classmethod
    def from_config(cls, *, name: str, config: Mapping[str, Any]) -> Output:
        """Build an output from options, which may be strings from a command line."""
        return construct(cls, name=name, config=config)

    @abstractmethod
    def open_document(self, dirpath: Path) -> Document:
        """Start a document whose files are written into the existing *dirpath*."""
