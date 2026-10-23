"""An in-process Transport for testing without sockets or files."""

from __future__ import annotations

from collections.abc import AsyncIterator

from papyrium.core.channel import ChunkChannel
from papyrium.core.transport import Transport


class MemoryConnection:
    """One connection into a :class:`MemoryTransport`."""

    def __init__(self, channel: ChunkChannel) -> None:
        self._channel = channel

    async def send(self, data: bytes) -> None:
        await self._channel.send(data)

    async def disconnect(self) -> None:
        """End this connection; the transport's stream carries on."""


class MemoryTransport(Transport):
    """An in-process transport for testing readers without sockets.

    Open connections with :meth:`connect` and send bytes through them, or
    :meth:`feed` bytes as a single short-lived connection.
    """

    def __init__(self, name: str, *, capacity: int = 16, **kwargs) -> None:
        super().__init__(name=name, **kwargs)
        self._channel = ChunkChannel(capacity)

    async def open(self) -> None:
        pass

    async def close(self) -> None:
        self._channel.close()

    def connect(self) -> MemoryConnection:
        """Open a new connection to this transport."""
        return MemoryConnection(self._channel)

    async def feed(self, data: bytes) -> None:
        """Send *data* over a new connection, then disconnect it."""
        connection = self.connect()
        await connection.send(data)
        await connection.disconnect()

    def __aiter__(self) -> AsyncIterator[bytes]:
        return self._channel
