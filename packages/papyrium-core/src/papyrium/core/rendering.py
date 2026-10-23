"""JobRendering: one job's bytes through a printer model into its outputs."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from pathlib import Path

from papyrium.core.model import PrinterModel
from papyrium.core.output import Output
from papyrium.core.page import Page

logger = logging.getLogger(__name__)


class JobRendering:
    """Feeds one job's bytes to a model's interpreter and its pages to every output.

    Synchronous and deterministic; the server runs it off the event loop.
    """

    def __init__(self, model: PrinterModel, outputs: Sequence[Output], dirpath: Path) -> None:
        self._interpreter = model.create_interpreter()
        self._documents = [output.open_document(dirpath) for output in outputs]
        self._page_count = 0
        self._closed = False

    @property
    def page_count(self) -> int:
        return self._page_count

    def feed(self, data: bytes) -> None:
        self._add_pages(self._interpreter.feed(data))

    def finish(self) -> list[Path]:
        """End the job, returning every file the outputs wrote."""
        if self._closed:
            return []
        self._closed = True
        self._add_pages(self._interpreter.finish())
        filepaths = []
        for document in self._documents:
            filepaths.extend(document.close())
        return filepaths

    def _add_pages(self, pages: list[Page]) -> None:
        for page in pages:
            self._page_count += 1
            for document in self._documents:
                document.add_page(page)
            logger.info("page %d complete", page.number)
