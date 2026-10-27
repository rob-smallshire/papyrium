"""The in-process MemoryTransport meets the transport contract."""

from papyrium.core.conformance import TransportConformance
from papyrium.core.testing import MemoryTransport


class TestMemoryTransportConformance(TransportConformance):
    def make_transport(self):
        return MemoryTransport(name="memory")

    async def connect(self, transport):
        return transport.connect()


async def test_feed_is_a_one_shot_connection():
    async with MemoryTransport(name="memory") as transport:
        await transport.feed(b"HELLO\n\r")
        assert await anext(aiter(transport)) == b"HELLO\n\r"
