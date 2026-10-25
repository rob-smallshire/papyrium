"""PrinterInstance: one running printer, from its transport to its rendered pages."""

from __future__ import annotations

import asyncio

from papyrium.core.rendering import JobRenderer
from papyrium.core.spooler import Spooler
from papyrium.core.transport import Transport


class PrinterInstance:
    """A transport, the spooler capturing its jobs, and the renderer printing them.

    Without a renderer, jobs are captured but not printed.
    """

    def __init__(
        self, transport: Transport, spooler: Spooler, renderer: JobRenderer | None = None
    ) -> None:
        self._transport = transport
        self._spooler = spooler
        self._renderer = renderer

    async def run(self, stop: asyncio.Event) -> None:
        """Print until *stop* is set, then shut down gracefully.

        Shutting down closes the transport, ends the current job, and
        finishes rendering every job already received.
        """
        renderer = self._renderer
        render_task = None if renderer is None else asyncio.create_task(renderer.run())
        await self._transport.open()
        spool_task = asyncio.create_task(self._spooler.run())
        try:
            await stop.wait()
        finally:
            await self._transport.close()
            await spool_task
            if renderer is not None:
                renderer.close()
                await render_task
