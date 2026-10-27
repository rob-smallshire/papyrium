"""The abstract Transport interface."""

from __future__ import annotations

import ipaddress
from abc import abstractmethod
from collections.abc import AsyncIterator, Mapping
from dataclasses import dataclass
from typing import Any

from papyrium.core.options import construct
from papyrium.extension import Extension


@dataclass(frozen=True)
class Endpoint:
    """Somewhere a transport listens: its protocol, port and bound addresses.

    *protocol* names the protocol a sender speaks there, such as
    ``appsocket`` for raw bytes over TCP. *addresses* are as bound, so an
    unspecified address (``0.0.0.0`` or ``::``) stands for every interface.
    """

    protocol: str
    port: int
    addresses: tuple[str, ...]

    def __post_init__(self) -> None:
        if not 0 < self.port < 65536:
            raise ValueError(f"an endpoint needs a port from 1 to 65535, not {self.port}")
        if not self.addresses:
            raise ValueError("an endpoint needs at least one address")

    @property
    def local_only(self) -> bool:
        """Whether only this machine can reach the endpoint: every address is loopback."""
        return all(ipaddress.ip_address(address).is_loopback for address in self.addresses)


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

    @classmethod
    def from_config(cls, *, name: str, config: Mapping[str, Any]) -> Transport:
        """Build a transport from options, which may be strings from a command line.

        The default maps each option to the constructor's keyword parameter
        of the same name; see :func:`papyrium.core.options.construct`.
        """
        return construct(cls, name=name, config=config)

    @classmethod
    def all_interfaces_options(cls) -> dict[str, str]:
        """Options that make this transport listen on every network interface.

        Empty for a transport that does not listen on the network.
        """
        return {}

    def endpoints(self) -> tuple[Endpoint, ...]:
        """Where this transport listens while open; none for one off the network."""
        return ()

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
