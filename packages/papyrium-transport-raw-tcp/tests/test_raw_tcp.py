"""RawTcpTransport over real loopback sockets."""

import asyncio

from papyrium.core.conformance import QUIET_SECONDS, TransportConformance, receive
from papyrium.extension import create_extension, namespace_for
from papyrium.transport.raw_tcp import RawTcpTransport


class _TcpConnection:
    def __init__(self, reader, writer):
        self._reader = reader
        self._writer = writer

    async def send(self, data):
        self._writer.write(data)
        await self._writer.drain()

    async def disconnect(self):
        self._writer.close()
        await self._writer.wait_closed()


async def _connect(transport):
    reader, writer = await asyncio.open_connection("127.0.0.1", transport.port)
    return _TcpConnection(reader, writer)


def _make_transport():
    return RawTcpTransport(name="raw-tcp", host="127.0.0.1", port=0)


class TestRawTcpConformance(TransportConformance):
    def make_transport(self):
        return _make_transport()

    async def connect(self, transport):
        return await _connect(transport)


def test_defaults_to_port_9100():
    assert RawTcpTransport(name="raw-tcp").port == 9100


def test_is_registered_on_the_transport_axis():
    transport = create_extension("transport", namespace_for("transport"), "raw-tcp")
    assert isinstance(transport, RawTcpTransport)


async def test_port_zero_reports_the_bound_port():
    async with _make_transport() as transport:
        assert transport.port > 0


async def test_a_second_connection_waits_for_the_first_to_end():
    async with _make_transport() as transport:
        first = await _connect(transport)
        await first.send(b"FIRST")
        assert await receive(transport, 5) == b"FIRST"
        second = await _connect(transport)
        await second.send(b"SECOND")
        try:
            await asyncio.wait_for(anext(aiter(transport)), QUIET_SECONDS)
        except TimeoutError:
            pass
        else:
            raise AssertionError("second connection was read while the first was open")
        await first.send(b"MORE")
        await first.disconnect()
        assert await receive(transport, 10) == b"MORESECOND"
        await second.disconnect()


async def test_close_drops_open_connections():
    transport = _make_transport()
    async with transport:
        connection = await _connect(transport)
        await connection.send(b"X")
        assert await receive(transport, 1) == b"X"
    assert await asyncio.wait_for(connection._reader.read(), 1.0) == b""


def test_has_no_endpoint_until_open():
    assert _make_transport().endpoints() == ()


async def test_reports_its_endpoint_once_open():
    async with _make_transport() as transport:
        (endpoint,) = transport.endpoints()
        assert endpoint.protocol == "appsocket"
        assert endpoint.port == transport.port
        assert endpoint.addresses == ("127.0.0.1",)
        assert endpoint.local_only


def test_listens_on_every_interface_given_an_empty_host():
    assert RawTcpTransport.all_interfaces_options() == {"host": ""}


def test_describes_listening_on_every_interface(caplog):
    from papyrium.transport.raw_tcp import _listening_place

    assert _listening_place("", 9100) == "every interface, port 9100"
    assert _listening_place("127.0.0.1", 9100) == "127.0.0.1:9100"
