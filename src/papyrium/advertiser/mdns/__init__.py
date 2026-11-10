"""Announcing Papyrium printers on the local network with multicast DNS.

A printer is announced as a DNS-SD service, the way Bonjour and Avahi
announce network printers, using python-zeroconf (LGPL-2.1-or-later) as
its own responder. A raw TCP printer is a ``_pdl-datastream._tcp``
service, as Apple's Bonjour Printing specification gives for raw port
printing, so it appears like any other network printer, and its TXT
record names it as a Papyrium printer so a client can tell it apart from
a real one.
"""

from __future__ import annotations

import ipaddress
import logging
import socket
from collections.abc import Callable, Iterable

import ifaddr
from zeroconf import ServiceInfo
from zeroconf.asyncio import AsyncZeroconf

from papyrium.core.advertising import Advertisement, Advertiser
from papyrium.core.transport import Endpoint

__all__ = ["MdnsAdvertiser", "service_infos"]

logger = logging.getLogger(__name__)

#: The DNS-SD service type of each protocol a printer can be reached by.
SERVICE_TYPES = {"appsocket": "_pdl-datastream._tcp.local."}

InterfaceAddresses = Callable[[], Iterable[str]]

#: Documentation addresses (RFC 5737, RFC 3849), never routed: connecting
#: a UDP socket towards one asks the system which of its addresses it
#: would send from, without sending anything.
_ROUTE_PROBES = {socket.AF_INET: "192.0.2.1", socket.AF_INET6: "2001:db8::1"}


def _machine_addresses() -> list[str]:
    """Every address of this machine's network interfaces, IPv6 without its scope."""
    addresses = []
    for adapter in ifaddr.get_adapters():
        for ip in adapter.ips:
            addresses.append(ip.ip if isinstance(ip.ip, str) else ip.ip[0])
    return addresses


def _primary_addresses() -> list[str]:
    """The addresses this machine sends from by its default routes, one for
    each family that has one."""
    addresses = []
    for family, probe in _ROUTE_PROBES.items():
        try:
            with socket.socket(family, socket.SOCK_DGRAM) as probe_socket:
                probe_socket.connect((probe, 9))
                addresses.append(probe_socket.getsockname()[0].split("%")[0])
        except OSError as error:
            logger.debug("no default route for %s: %s", family.name, error)
    return addresses


def _every_address(
    version: int, interface_addresses: InterfaceAddresses, primary_addresses: InterfaceAddresses
) -> list[str]:
    """This machine's addresses of one IP *version* that a client may reach.

    Loopback is left out, and link-local addresses too while there are
    others, since they reach only their own link, which the announcement
    cannot say. The address the default route sends from comes first: a
    client that tries only the first address announced then reaches the
    machine whenever it can be reached by its usual route.
    """
    candidates = [
        candidate
        for candidate in interface_addresses()
        if ipaddress.ip_address(candidate).version == version
        and not ipaddress.ip_address(candidate).is_loopback
    ]
    routable = [c for c in candidates if not ipaddress.ip_address(c).is_link_local]
    candidates = routable or candidates
    primary = [address for address in primary_addresses() if address in candidates]
    return primary + [candidate for candidate in candidates if candidate not in primary]


def _announced_addresses(
    endpoint: Endpoint,
    interface_addresses: InterfaceAddresses,
    primary_addresses: InterfaceAddresses = _primary_addresses,
) -> list[str]:
    """The addresses to announce for *endpoint*.

    An unspecified address (``0.0.0.0`` or ``::``) stands for every
    address of its family on this machine a client may reach (see
    :func:`_every_address`); any other is announced as bound.
    """
    announced = []
    for bound in endpoint.addresses:
        address = ipaddress.ip_address(bound)
        if address.is_unspecified:
            every = _every_address(address.version, interface_addresses, primary_addresses)
            announced.extend(every)
        elif not address.is_loopback:
            announced.append(bound)
    return list(dict.fromkeys(announced))


def _txt_record(advertisement: Advertisement) -> dict[str, str]:
    """The TXT record, in the keys of the Bonjour Printing specification.

    A printer with no model says only that it is a Papyrium printer.
    """
    model = advertisement.model
    record = {"txtvers": "1", "qtotal": "1"}
    if model is None:
        record["ty"] = "Papyrium"
    else:
        record["ty"] = f"{model.display_name} (Papyrium)"
        record["product"] = f"({model.display_name})"
    record["note"] = "Papyrium virtual printer"
    if model is not None:
        record["usb_MFG"] = model.manufacturer
        record["usb_MDL"] = model.model
    if advertisement.languages:
        record["usb_CMD"] = ",".join(language.command_set for language in advertisement.languages)
    record["uuid"] = str(advertisement.printer_uuid)
    return record


def service_infos(
    advertisement: Advertisement,
    interface_addresses: InterfaceAddresses = _machine_addresses,
    primary_addresses: InterfaceAddresses = _primary_addresses,
) -> list[ServiceInfo]:
    """The DNS-SD services announcing *advertisement*, one for each endpoint it can describe.

    The services name their own host, ``papyrium-<first 8 hex digits of the
    UUID>.local.``, so the responder never answers for the machine's own
    name, which the system's responder owns.
    """
    server = f"papyrium-{advertisement.printer_uuid.hex[:8]}.local."
    properties = _txt_record(advertisement)
    infos = []
    for endpoint in advertisement.endpoints:
        service_type = SERVICE_TYPES.get(endpoint.protocol)
        if service_type is None:
            logger.warning(
                "not advertising port %d: no DNS-SD service type for %s",
                endpoint.port,
                endpoint.protocol,
            )
            continue
        addresses = _announced_addresses(endpoint, interface_addresses, primary_addresses)
        if not addresses:
            logger.warning("not advertising port %d: no network address to give", endpoint.port)
            continue
        infos.append(
            ServiceInfo(
                service_type,
                f"{advertisement.name}.{service_type}",
                port=endpoint.port,
                properties=properties,
                server=server,
                parsed_addresses=addresses,
            )
        )
    return infos


class MdnsAdvertiser(Advertiser):
    """Announces printers with multicast DNS, as Bonjour and Avahi do.

    It runs its own responder on every interface, alongside any the system
    runs. If the printer's name is taken on the network, the responder
    picks a free variant, and the name actually registered is logged.
    """

    def __init__(
        self,
        name: str,
        *,
        zeroconf_factory: Callable[[], AsyncZeroconf] = AsyncZeroconf,
        interface_addresses: InterfaceAddresses = _machine_addresses,
        primary_addresses: InterfaceAddresses = _primary_addresses,
        **kwargs,
    ) -> None:
        super().__init__(name=name, **kwargs)
        self._zeroconf_factory = zeroconf_factory
        self._interface_addresses = interface_addresses
        self._primary_addresses = primary_addresses
        self._zeroconf: AsyncZeroconf | None = None
        self._infos: list[ServiceInfo] = []

    async def start(self, advertisement: Advertisement) -> None:
        infos = service_infos(advertisement, self._interface_addresses, self._primary_addresses)
        if not infos:
            return
        self._zeroconf = self._zeroconf_factory()
        for info in infos:
            await (await self._zeroconf.async_register_service(info, allow_name_change=True))
            self._infos.append(info)
            instance = info.name.removesuffix(f".{info.type}")
            logger.info(
                'advertising "%s" as %s on port %d at %s',
                instance,
                info.type.removesuffix(".local."),
                info.port,
                ", ".join(info.parsed_addresses()),
            )

    async def stop(self) -> None:
        if self._zeroconf is None:
            return
        zeroconf, self._zeroconf = self._zeroconf, None
        try:
            await zeroconf.async_unregister_all_services()
            for info in self._infos:
                logger.info('withdrew "%s"', info.name.removesuffix(f".{info.type}"))
        finally:
            self._infos = []
            await zeroconf.async_close()
