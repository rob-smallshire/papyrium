"""MdnsAdvertiser: a printer announced as DNS-SD records, with zeroconf faked."""

import asyncio
import dataclasses
import logging
import uuid

from papyrium.advertiser.mdns import MdnsAdvertiser, service_infos
from papyrium.core.conformance import AdvertiserConformance, sample_advertisement
from papyrium.core.transport import Endpoint
from papyrium.extension import create_extension, namespace_for

INTERFACE_ADDRESSES = ("192.168.1.20", "fe80::1", "127.0.0.1", "::1")


def _interface_addresses():
    return INTERFACE_ADDRESSES


class _FakeZeroconf:
    """Records registrations; renames the first one, as after a name clash."""

    def __init__(self, *, rename_to=None):
        self.registered = []
        self.unregistered = []
        self.closed = False
        self._rename_to = rename_to

    async def async_register_service(self, info, allow_name_change=False):
        if self._rename_to and allow_name_change:
            info.name = self._rename_to
        self.registered.append(info)
        done = asyncio.get_running_loop().create_future()
        done.set_result(None)
        return done

    async def async_unregister_all_services(self):
        self.unregistered.extend(self.registered)

    async def async_close(self):
        self.closed = True


def _advertiser(zeroconf=None):
    zeroconf = zeroconf or _FakeZeroconf()
    advertiser = MdnsAdvertiser(
        name="mdns", zeroconf_factory=lambda: zeroconf, interface_addresses=_interface_addresses
    )
    return advertiser, zeroconf


class TestMdnsAdvertiserConformance(AdvertiserConformance):
    def make_advertiser(self):
        return _advertiser()[0]


def test_is_registered_on_the_advertiser_axis():
    advertiser = create_extension("advertiser", namespace_for("advertiser"), "mdns")
    assert isinstance(advertiser, MdnsAdvertiser)


def test_a_raw_tcp_printer_is_a_pdl_datastream_service():
    (info,) = service_infos(sample_advertisement(), _interface_addresses)
    assert info.type == "_pdl-datastream._tcp.local."
    assert info.name == "Conformance Printer (Papyrium)._pdl-datastream._tcp.local."
    assert info.port == 9100


def test_txt_record_follows_the_bonjour_printing_keys_and_names_papyrium():
    (info,) = service_infos(sample_advertisement(), _interface_addresses)
    assert info.decoded_properties == {
        "txtvers": "1",
        "qtotal": "1",
        "ty": "Epson FX-80 (Papyrium)",
        "product": "(Epson FX-80)",
        "note": "Papyrium virtual printer",
        "usb_MFG": "Epson",
        "usb_MDL": "FX-80",
        "usb_CMD": "ESCP9",
        "uuid": "00000000-0000-4000-8000-000000000001",
    }


def test_an_unspecified_address_stands_for_every_address_of_its_family_but_loopback():
    (info,) = service_infos(sample_advertisement(), _interface_addresses)
    assert info.parsed_addresses() == ["192.168.1.20"]
    dual_stack = dataclasses.replace(
        sample_advertisement(),
        endpoints=(Endpoint(protocol="appsocket", port=9100, addresses=("0.0.0.0", "::")),),
    )
    (info,) = service_infos(dual_stack, _interface_addresses)
    assert sorted(info.parsed_addresses()) == ["192.168.1.20", "fe80::1"]


def test_a_specific_address_is_announced_as_bound():
    advertisement = dataclasses.replace(
        sample_advertisement(),
        endpoints=(Endpoint(protocol="appsocket", port=9100, addresses=("192.168.1.20",)),),
    )
    (info,) = service_infos(advertisement, _interface_addresses)
    assert info.parsed_addresses() == ["192.168.1.20"]


def test_the_host_is_named_for_the_printer_so_it_never_claims_the_machines_name():
    (info,) = service_infos(sample_advertisement(), _interface_addresses)
    assert info.server == "papyrium-00000000.local."


def test_an_endpoint_of_an_unknown_protocol_is_left_out_and_said_so(caplog):
    advertisement = dataclasses.replace(
        sample_advertisement(),
        endpoints=(Endpoint(protocol="rfc2217", port=2217, addresses=("0.0.0.0",)),),
    )
    with caplog.at_level(logging.WARNING):
        assert service_infos(advertisement, _interface_addresses) == []
    assert "rfc2217" in caplog.text


async def test_start_registers_and_reports_the_name_actually_registered(caplog):
    taken = "Conformance Printer (Papyrium) (2)._pdl-datastream._tcp.local."
    advertiser, zeroconf = _advertiser(_FakeZeroconf(rename_to=taken))
    with caplog.at_level(logging.INFO):
        await advertiser.start(sample_advertisement())
    assert len(zeroconf.registered) == 1
    assert (
        'advertising "Conformance Printer (Papyrium) (2)" as _pdl-datastream._tcp on port 9100'
        in (caplog.text)
    )


async def test_stop_withdraws_and_closes(caplog):
    advertiser, zeroconf = _advertiser()
    await advertiser.start(sample_advertisement())
    with caplog.at_level(logging.INFO):
        await advertiser.stop()
    assert zeroconf.unregistered == zeroconf.registered
    assert zeroconf.closed
    assert "withdrew" in caplog.text


async def test_nothing_to_announce_opens_no_responder():
    created = []
    advertiser = MdnsAdvertiser(
        name="mdns",
        zeroconf_factory=lambda: created.append(1) or _FakeZeroconf(),
        interface_addresses=_interface_addresses,
    )
    advertisement = dataclasses.replace(
        sample_advertisement(),
        endpoints=(Endpoint(protocol="rfc2217", port=2217, addresses=("0.0.0.0",)),),
        printer_uuid=uuid.uuid4(),
    )
    await advertiser.start(advertisement)
    await advertiser.stop()
    assert created == []


def test_a_printer_without_a_model_says_only_that_it_is_papyrium():
    advertisement = dataclasses.replace(sample_advertisement(), model=None, languages=())
    (info,) = service_infos(advertisement, _interface_addresses)
    assert info.decoded_properties == {
        "txtvers": "1",
        "qtotal": "1",
        "ty": "Papyrium",
        "note": "Papyrium virtual printer",
        "uuid": "00000000-0000-4000-8000-000000000001",
    }
