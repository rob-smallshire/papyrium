"""A printer announced by MdnsAdvertiser is found by a later DNS-SD browse.

Not part of the default suite: multicast is unreliable on CI runners. It
runs a real responder and browser on the loopback interface only, so
nothing is announced to the network. Run from the repository root with::

    uv run pytest integration/mdns
"""

from __future__ import annotations

import asyncio

from zeroconf import IPVersion
from zeroconf.asyncio import AsyncServiceBrowser, AsyncServiceInfo, AsyncZeroconf

from papyrium.advertiser.mdns import MdnsAdvertiser
from papyrium.core.conformance import sample_advertisement

PRINTER_TYPE = "_pdl-datastream._tcp.local."
#: Announced in the records only; a browser on loopback need not reach it.
ANNOUNCED_ADDRESS = "192.0.2.10"


def _loopback_zeroconf():
    return AsyncZeroconf(interfaces=["127.0.0.1"], ip_version=IPVersion.V4Only)


async def _browse(service_type, seconds=3.0):
    """The instance names a browser started now finds for *service_type*."""
    client = _loopback_zeroconf()
    found = []

    def handler(zeroconf, service_type, name, state_change):
        found.append(name)

    browser = AsyncServiceBrowser(client.zeroconf, service_type, handlers=[handler])
    await asyncio.sleep(seconds)
    await browser.async_cancel()
    infos = []
    for name in dict.fromkeys(found):
        info = AsyncServiceInfo(service_type, name)
        if await info.async_request(client.zeroconf, 3000):
            infos.append(info)
    await client.async_close()
    return infos


async def test_a_printer_dialog_browsing_later_finds_the_printer_and_its_txt():
    advertiser = MdnsAdvertiser(
        name="mdns",
        zeroconf_factory=_loopback_zeroconf,
        interface_addresses=lambda: [ANNOUNCED_ADDRESS],
    )
    await advertiser.start(sample_advertisement())
    try:
        # Long enough for the announcements to end, so the browser must query.
        await asyncio.sleep(3)
        (info,) = await _browse(PRINTER_TYPE)
        assert info.name == "Conformance Printer (Papyrium)." + PRINTER_TYPE
        assert info.port == 9100
        assert info.parsed_addresses() == [ANNOUNCED_ADDRESS]
        assert info.decoded_properties["ty"] == "Epson FX-80 (Papyrium)"
        assert info.decoded_properties["note"] == "Papyrium virtual printer"
    finally:
        await advertiser.stop()


async def test_a_withdrawn_printer_is_no_longer_found():
    advertiser = MdnsAdvertiser(
        name="mdns",
        zeroconf_factory=_loopback_zeroconf,
        interface_addresses=lambda: [ANNOUNCED_ADDRESS],
    )
    await advertiser.start(sample_advertisement())
    await advertiser.stop()
    assert await _browse(PRINTER_TYPE) == []
