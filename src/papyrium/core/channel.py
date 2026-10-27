"""A bounded, closable channel of byte chunks between a transport and its reader."""

from __future__ import annotations

import asyncio

from papyrium.exception import InternalError


class _Closed:
    """Sentinel queued by close() to wake a reader waiting on an empty channel."""


_CLOSED = _Closed()


class ChannelClosedError(InternalError):
    """A chunk was sent into a channel that had already been closed."""


class ChunkChannel:
    """Carries byte chunks, in order, from producers to a single reader.

    The channel holds at most *capacity* chunks. A producer awaiting
    :meth:`send` on a full channel waits until the reader takes one, so a
    reader that stops reading stops the producer: this is how backpressure
    reaches a transport's connection, and through it the sender.

    :meth:`close` ends iteration once the chunks already in the channel have
    been read, so nothing a producer handed over before the close is lost.
    """

    def __init__(self, capacity: int = 16) -> None:
        self._queue: asyncio.Queue[bytes | _Closed] = asyncio.Queue(maxsize=capacity)
        self._closed = False

    @property
    def closed(self) -> bool:
        return self._closed

    async def send(self, chunk: bytes) -> None:
        """Hand *chunk* to the reader, waiting while the channel is full."""
        if self._closed:
            raise ChannelClosedError("cannot send into a closed chunk channel")
        if chunk:
            await self._queue.put(bytes(chunk))

    def close(self) -> None:
        """Close the channel; iteration ends after the chunks already queued."""
        if self._closed:
            return
        self._closed = True
        try:
            self._queue.put_nowait(_CLOSED)
        except asyncio.QueueFull:
            # The reader is behind; it finds the channel closed when it drains.
            pass

    def __aiter__(self) -> ChunkChannel:
        return self

    async def __anext__(self) -> bytes:
        if self._closed and self._queue.empty():
            raise StopAsyncIteration
        chunk = await self._queue.get()
        if isinstance(chunk, _Closed):
            raise StopAsyncIteration
        return chunk
