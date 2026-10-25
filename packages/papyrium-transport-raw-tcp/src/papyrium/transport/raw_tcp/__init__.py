"""Raw TCP transport: the JetDirect-style port 9100 byte stream."""

from __future__ import annotations

import asyncio
import contextlib
import logging
from collections.abc import AsyncIterator

from papyrium.core.channel import ChunkChannel
from papyrium.core.transport import Endpoint, Transport

__version__ = "0.1.0"

__all__ = ["RawTcpTransport", "DEFAULT_PORT"]

logger = logging.getLogger(__name__)

#: The protocol a sender speaks: raw bytes over TCP, as AppSocket or JetDirect.
APPSOCKET = "appsocket"

#: The JetDirect / AppSocket raw printing port.
DEFAULT_PORT = 9100

_READ_SIZE = 4096


class RawTcpTransport(Transport):
    """Raw TCP printing, by default on port 9100.

    Stands in for a parallel cable. Each connection carries unframed bytes
    with no protocol; flow control is TCP's own, so a printer that stops
    reading stalls the sender. A disconnect does not end the stream, and
    bytes from successive connections continue it.

    One connection is read at a time, as a real printer has one input;
    a later connection waits until the earlier one ends.

    Options: ``host`` (default ``localhost``; empty for every interface),
    ``port`` (default 9100; 0 picks a free port).
    """

    def __init__(
        self,
        name: str,
        *,
        host: str = "localhost",
        port: int = DEFAULT_PORT,
        capacity: int = 16,
        **kwargs,
    ) -> None:
        super().__init__(name=name, **kwargs)
        self._host = host
        self._port = port
        self._channel = ChunkChannel(capacity)
        self._server: asyncio.Server | None = None
        self._turn = asyncio.Lock()
        self._handlers: set[asyncio.Task] = set()

    @property
    def host(self) -> str:
        return self._host

    @property
    def port(self) -> int:
        """The listening port; the bound port once open if 0 was asked for."""
        return self._port

    @classmethod
    def all_interfaces_options(cls) -> dict[str, str]:
        return {"host": ""}

    def endpoints(self) -> tuple[Endpoint, ...]:
        if self._server is None:
            return ()
        addresses = tuple(dict.fromkeys(s.getsockname()[0] for s in self._server.sockets))
        return (Endpoint(protocol=APPSOCKET, port=self._port, addresses=addresses),)

    async def open(self) -> None:
        self._server = await asyncio.start_server(self._handle, self._host, self._port)
        self._port = self._server.sockets[0].getsockname()[1]
        logger.info("listening for raw TCP on %s", _listening_place(self._host, self._port))

    async def close(self) -> None:
        if self._server is not None:
            self._server.close()
        for handler in list(self._handlers):
            handler.cancel()
        if self._handlers:
            await asyncio.gather(*self._handlers, return_exceptions=True)
        if self._server is not None:
            await self._server.wait_closed()
            self._server = None
        self._channel.close()

    def __aiter__(self) -> AsyncIterator[bytes]:
        return self._channel

    async def _handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        handler = asyncio.current_task()
        self._handlers.add(handler)
        peer = writer.get_extra_info("peername")
        try:
            async with self._turn:
                logger.info("connection from %s", peer)
                await self._pump(reader, peer)
        finally:
            self._handlers.discard(handler)
            writer.close()
            with contextlib.suppress(ConnectionError):
                await writer.wait_closed()
            logger.info("connection from %s ended", peer)

    async def _pump(self, reader: asyncio.StreamReader, peer) -> None:
        try:
            while chunk := await reader.read(_READ_SIZE):
                await self._channel.send(chunk)
        except ConnectionError as error:
            logger.warning("connection from %s failed: %s", peer, error)


def _listening_place(host: str, port: int) -> str:
    return f"{host}:{port}" if host else f"every interface, port {port}"
