"""A reusable conformance suite for Transport implementations.

Subclass :class:`TransportConformance` in a transport package's test suite,
implement :meth:`~TransportConformance.make_transport` and
:meth:`~TransportConformance.connect`, and pytest runs the inherited
contract checks against your transport.

This module deliberately imports no test framework, so it is safe to import
anywhere; the concrete subclass lives in a test module that pytest collects.
"""

from __future__ import annotations

import asyncio
from typing import Protocol

from papyrium.core.transport import Transport

#: How long a check waits for bytes before deciding they are not coming.
TIMEOUT_SECONDS = 2.0

#: How long a check waits to be confident that nothing more is coming.
QUIET_SECONDS = 0.1


class Connection(Protocol):
    """One connection from a sender to the transport under test."""

    async def send(self, data: bytes) -> None:
        """Send *data* to the transport."""

    async def disconnect(self) -> None:
        """End this connection."""


async def receive(transport: Transport, count: int) -> bytes:
    """Pull chunks from *transport* until *count* bytes have arrived."""
    received = bytearray()
    iterator = aiter(transport)
    while len(received) < count:
        received += await asyncio.wait_for(anext(iterator), TIMEOUT_SECONDS)
    return bytes(received)


class TransportConformance:
    """The contract every :class:`Transport` implementation must satisfy."""

    def make_transport(self) -> Transport:
        """Return a fresh, unopened transport to exercise. Override this."""
        raise NotImplementedError

    async def connect(self, transport: Transport) -> Connection:
        """Open a new connection to the opened *transport*. Override this."""
        raise NotImplementedError

    def test_kind_is_transport(self):
        assert type(self.make_transport()).kind() == "transport"

    async def test_context_manager_yields_self(self):
        transport = self.make_transport()
        async with transport as entered:
            assert entered is transport

    async def test_bytes_arrive_in_order(self):
        data = bytes(range(256)) * 4
        async with self.make_transport() as transport:
            connection = await self.connect(transport)
            await connection.send(data[:300])
            await connection.send(data[300:])
            assert await receive(transport, len(data)) == data
            await connection.disconnect()

    async def test_chunks_are_non_empty_bytes(self):
        async with self.make_transport() as transport:
            connection = await self.connect(transport)
            await connection.send(b"HELLO")
            chunk = await asyncio.wait_for(anext(aiter(transport)), TIMEOUT_SECONDS)
            assert isinstance(chunk, bytes)
            assert chunk
            await connection.disconnect()

    async def test_disconnect_does_not_end_the_stream(self):
        async with self.make_transport() as transport:
            first = await self.connect(transport)
            await first.send(b"ONE")
            await first.disconnect()
            assert await receive(transport, 3) == b"ONE"
            second = await self.connect(transport)
            await second.send(b"TWO")
            await second.disconnect()
            assert await receive(transport, 3) == b"TWO"

    async def test_iteration_waits_for_bytes_after_disconnect(self):
        async with self.make_transport() as transport:
            connection = await self.connect(transport)
            await connection.send(b"X")
            await connection.disconnect()
            assert await receive(transport, 1) == b"X"
            try:
                await asyncio.wait_for(anext(aiter(transport)), QUIET_SECONDS)
            except TimeoutError:
                pass
            else:
                raise AssertionError("iteration produced data or ended after a disconnect")

    async def test_iteration_ends_after_close(self):
        transport = self.make_transport()
        async with transport:
            pass
        received = [chunk async for chunk in transport]
        assert received == []
