"""JobRendering: one job's bytes through a printer model into its outputs."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Sequence
from pathlib import Path

from papyrium.core.jobs import JobCapture
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


class _Stop:
    """Sentinel queued by close() to end :meth:`JobRenderer.run`."""


class JobRenderer:
    """Renders jobs as the spooler captures them, a spooler listener.

    Events are queued in arrival order and handled one at a time by
    :meth:`run`, which does the synchronous interpretation and output work
    in a worker thread so the event loop keeps reading the transport.
    A rendering failure is logged and abandons that job's rendering; its
    capture is unaffected and can be replayed.
    """

    def __init__(self, model: PrinterModel, outputs: Sequence[Output]) -> None:
        self._model = model
        self._outputs = list(outputs)
        self._events: asyncio.Queue = asyncio.Queue()
        self._renderings: dict[int, JobRendering] = {}

    def job_started(self, job: JobCapture) -> None:
        self._events.put_nowait(("start", job, b""))

    def bytes_captured(self, job: JobCapture, chunk: bytes) -> None:
        self._events.put_nowait(("bytes", job, chunk))

    def job_ended(self, job: JobCapture) -> None:
        self._events.put_nowait(("end", job, b""))

    def close(self) -> None:
        """Stop :meth:`run` once the events already queued are handled."""
        self._events.put_nowait(_Stop())

    async def run(self) -> None:
        while not isinstance(event := await self._events.get(), _Stop):
            kind, job, chunk = event
            try:
                await asyncio.to_thread(self._handle, kind, job, chunk)
            except Exception:
                logger.exception("rendering job %d failed; its capture is intact", job.number)
                self._renderings.pop(job.number, None)

    def _handle(self, kind: str, job: JobCapture, chunk: bytes) -> None:
        if kind == "start":
            self._renderings[job.number] = JobRendering(self._model, self._outputs, job.dirpath)
            return
        rendering = self._renderings.get(job.number)
        if rendering is None:
            return
        if kind == "bytes":
            rendering.feed(chunk)
        else:
            del self._renderings[job.number]
            filepaths = rendering.finish()
            logger.info(
                "job %d rendered: %d pages, %s",
                job.number,
                rendering.page_count,
                ", ".join(path.name for path in filepaths) or "no files",
            )
