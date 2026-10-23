"""The abstract Transport interface."""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import AsyncIterator

from papyrium.extension import Extension


class Transport(Extension):
    """Delivers the bytes a computer sends to its printer, in order.

    A transport is the boundary between a printer instance and the
    connection that feeds it: a TCP socket standing in for a parallel
    cable, an RFC 2217 session standing in for a serial line, a file being
    replayed. It knows nothing of printer languages or jobs.

    It presents a *pull* interface: the reader iterates byte chunks with
    ``async for chunk in transport``. A transport reads from its connection
    no faster than chunks are pulled, so a reader that stops pulling
    applies backpressure to the sender.

    Connection lifetime is not job lifetime. Bytes from successive
    connections arrive as one continuous stream; a disconnect does not end
    iteration. Iteration ends only after :meth:`close`.

    Concrete transports plug in on the ``papyrium.transport`` extension
    axis.
    """

    @classmethod
    def _kind(cls) -> str:
        return "transport"

    @abstractmethod
    async def open(self) -> None:
        """Start accepting bytes."""

    @abstractmethod
    async def close(self) -> None:
        """Stop accepting bytes and end iteration once queued chunks are read."""

    async def __aenter__(self) -> Transport:
        await self.open()
        return self

    async def __aexit__(self, exc_type, exc, traceback) -> None:
        await self.close()

    @abstractmethod
    def __aiter__(self) -> AsyncIterator[bytes]:
        """Iterate non-empty byte chunks in the order they arrived."""
