"""PrinterInstance: one running printer, from its transport to its rendered pages."""

from __future__ import annotations

import asyncio

from papyrium.core.advertising import Advertising
from papyrium.core.model import ModelIdentity
from papyrium.core.rendering import JobRenderer
from papyrium.core.spooler import Spooler
from papyrium.core.transport import Transport


def default_printer_name(identity: ModelIdentity | None) -> str:
    """The name a printer goes by unless given one, such as ``Brother M-1109 (Papyrium)``.

    A printer capturing jobs with no printer model is plain ``Papyrium``.
    """
    return "Papyrium" if identity is None else f"{identity.display_name} (Papyrium)"


class PrinterInstance:
    """A transport, the spooler capturing its jobs, and the renderer printing them.

    Without a renderer, jobs are captured but not printed. With
    *advertising*, the printer is announced on the network while its
    transport listens.
    """

    def __init__(
        self,
        transport: Transport,
        spooler: Spooler,
        renderer: JobRenderer | None = None,
        *,
        advertising: Advertising | None = None,
    ) -> None:
        self._transport = transport
        self._spooler = spooler
        self._renderer = renderer
        self._advertising = advertising

    async def run(self, stop: asyncio.Event) -> None:
        """Print until *stop* is set, then shut down gracefully.

        Shutting down withdraws any advertisement, closes the transport,
        ends the current job, and finishes rendering every job already
        received.
        """
        renderer = self._renderer
        render_task = None if renderer is None else asyncio.create_task(renderer.run())
        await self._transport.open()
        spool_task = asyncio.create_task(self._spooler.run())
        try:
            if self._advertising is not None:
                await self._advertising.start(self._transport.endpoints())
            await stop.wait()
        finally:
            # Withdrawn first, so nobody is sent to a printer that has stopped listening.
            if self._advertising is not None:
                await self._advertising.stop()
            await self._transport.close()
            await spool_task
            if renderer is not None:
                renderer.close()
                await render_task
