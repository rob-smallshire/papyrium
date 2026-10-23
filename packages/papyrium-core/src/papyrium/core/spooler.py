"""The Spooler: pulls bytes from a transport into per-job captures."""

from __future__ import annotations

import asyncio
import logging

from papyrium.core.jobs import JobCapture, JobEndReason, JobStore
from papyrium.core.transport import Transport

logger = logging.getLogger(__name__)


class Spooler:
    """Captures every byte a transport delivers into the current job.

    A job starts with the first byte after the previous job ended. The
    spooler applies only the job rules that hold for every printer
    language: an idle timeout and an explicit request. A disconnect never
    ends a job; the transport does not even report one.

    *idle_timeout_seconds* of zero disables the idle rule.
    """

    def __init__(
        self,
        transport: Transport,
        job_store: JobStore,
        *,
        idle_timeout_seconds: float,
    ) -> None:
        self._transport = transport
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
            self._current_job = self._job_store.create_job(transport_name=self._transport.name)
        self._current_job.append(chunk)
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
        return job
