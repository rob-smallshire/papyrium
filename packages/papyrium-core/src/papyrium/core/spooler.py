"""The Spooler: pulls bytes from a transport into per-job captures."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Mapping
from typing import Any, Protocol

from papyrium.core.jobs import JobCapture, JobEndReason, JobStore
from papyrium.core.transport import Transport

logger = logging.getLogger(__name__)


class SpoolerListener(Protocol):
    """Told of each job's start, its captured bytes, and its end, in order."""

    def job_started(self, job: JobCapture) -> None: ...

    def bytes_captured(self, job: JobCapture, chunk: bytes) -> None: ...

    def job_ended(self, job: JobCapture) -> None: ...


class Spooler:
    """Captures every byte a transport delivers into the current job.

    A job starts with the first byte after the previous job ended. The
    spooler applies only the job rules that hold for every printer
    language: an idle timeout and an explicit request. A disconnect never
    ends a job; the transport does not even report one.

    *idle_timeout_seconds* of zero disables the idle rule. *printer_setup*
    is recorded with each job so its capture can be replayed. A *listener*
    hears of each job and of every chunk once it is in the capture.
    """

    def __init__(
        self,
        transport: Transport,
        job_store: JobStore,
        *,
        idle_timeout_seconds: float,
        printer_setup: Mapping[str, Any] | None = None,
        listener: SpoolerListener | None = None,
    ) -> None:
        self._transport = transport
        self._printer_setup = printer_setup
        self._listener = listener
        self._job_store = job_store
        self._idle_timeout_seconds = idle_timeout_seconds
        self._current_job: JobCapture | None = None
        self._idle_handle: asyncio.TimerHandle | None = None

    @property
    def current_job(self) -> JobCapture | None:
        """The job now receiving bytes, or None between jobs."""
        return self._current_job

    async def run(self) -> None:
        """Spool until the transport closes, then end any open job."""
        try:
            async for chunk in self._transport:
                self._receive(chunk)
        finally:
            self._end_current_job(JobEndReason.SHUTDOWN)

    def end_job(self) -> JobCapture | None:
        """End the current job on request, returning it, or None if there is none."""
        return self._end_current_job(JobEndReason.REQUESTED)

    def _receive(self, chunk: bytes) -> None:
        if self._current_job is None:
            self._current_job = self._job_store.create_job(
                transport_name=self._transport.name, printer_setup=self._printer_setup
            )
            if self._listener is not None:
                self._listener.job_started(self._current_job)
        self._current_job.append(chunk)
        if self._listener is not None:
            self._listener.bytes_captured(self._current_job, chunk)
        self._restart_idle_timer()

    def _restart_idle_timer(self) -> None:
        if self._idle_timeout_seconds <= 0:
            return
        if self._idle_handle is not None:
            self._idle_handle.cancel()
        self._idle_handle = asyncio.get_running_loop().call_later(
            self._idle_timeout_seconds, self._end_current_job, JobEndReason.IDLE
        )

    def _end_current_job(self, reason: JobEndReason) -> JobCapture | None:
        if self._idle_handle is not None:
            self._idle_handle.cancel()
            self._idle_handle = None
        job = self._current_job
        if job is None:
            return None
        self._current_job = None
        job.close(reason)
        if self._listener is not None:
            self._listener.job_ended(job)
        return job
