"""Advertising a printer: what is announced, when, and what happens when it can't be."""

import asyncio
import logging
import uuid

import pytest

from papyrium.core.advertising import Advertisement, Advertising
from papyrium.core.conformance import AdvertiserConformance
from papyrium.core.instance import PrinterInstance
from papyrium.core.jobs import JobStore
from papyrium.core.language import LanguageIdentity
from papyrium.core.model import ModelIdentity
from papyrium.core.spooler import Spooler
from papyrium.core.testing import ByteDotModel, MemoryAdvertiser, MemoryTransport
from papyrium.core.transport import Endpoint

PRINTER_UUID = uuid.UUID("12345678-1234-4234-8234-123456789abc")
NETWORK = Endpoint(protocol="appsocket", port=9100, addresses=("0.0.0.0",))
LOOPBACK = Endpoint(protocol="appsocket", port=9101, addresses=("127.0.0.1",))


class TestMemoryAdvertiserConformance(AdvertiserConformance):
    def make_advertiser(self):
        return MemoryAdvertiser(name="memory")


TOY = LanguageIdentity(name="Toy", command_set="TOY")


class _SpeakingModel(ByteDotModel):
    def languages(self):
        return ("toy",)


def _advertising(advertiser):
    return Advertising(
        advertiser,
        name="Desk Printer",
        printer_uuid=PRINTER_UUID,
        model=_SpeakingModel(name="m"),
        language_identity={"toy": TOY}.__getitem__,
    )


async def test_announces_the_printer_and_its_network_endpoints():
    advertiser = MemoryAdvertiser(name="memory")
    await _advertising(advertiser).start((NETWORK,))
    (advertisement,) = advertiser.advertisements
    assert advertisement == Advertisement(
        name="Desk Printer",
        printer_uuid=PRINTER_UUID,
        model=ModelIdentity(manufacturer="Papyrium", model="Byte Dot"),
        languages=(TOY,),
        endpoints=(NETWORK,),
    )


async def test_leaves_out_endpoints_only_this_machine_can_reach(caplog):
    advertiser = MemoryAdvertiser(name="memory")
    with caplog.at_level(logging.INFO):
        await _advertising(advertiser).start((NETWORK, LOOPBACK))
    assert advertiser.advertisements[0].endpoints == (NETWORK,)
    assert "port 9101" in caplog.text and "only this machine" in caplog.text


async def test_announces_nothing_when_only_this_machine_can_reach_it(caplog):
    advertiser = MemoryAdvertiser(name="memory")
    with caplog.at_level(logging.INFO):
        await _advertising(advertiser).start((LOOPBACK,))
    assert advertiser.advertisements == []
    assert "not advertising" in caplog.text


async def test_a_failure_to_advertise_is_logged_not_raised(caplog):
    advertiser = MemoryAdvertiser(name="memory", fail=True)
    advertising = _advertising(advertiser)
    with caplog.at_level(logging.WARNING):
        await advertising.start((NETWORK,))
        await advertising.stop()
    assert "advertising failed" in caplog.text


async def test_stop_withdraws_what_was_announced():
    advertiser = MemoryAdvertiser(name="memory")
    advertising = _advertising(advertiser)
    await advertising.start((NETWORK,))
    await advertising.stop()
    assert advertiser.stopped


class _RecordingTransport(MemoryTransport):
    def __init__(self, name, events):
        super().__init__(name=name)
        self._events = events

    def endpoints(self):
        return (NETWORK,)

    async def open(self):
        self._events.append("transport opened")

    async def close(self):
        self._events.append("transport closed")
        await super().close()


class _RecordingAdvertiser(MemoryAdvertiser):
    def __init__(self, name, events):
        super().__init__(name=name)
        self._events = events

    async def start(self, advertisement):
        self._events.append("advertised")
        await super().start(advertisement)

    async def stop(self):
        self._events.append("withdrawn")
        await super().stop()


async def test_a_printer_advertises_once_listening_and_withdraws_before_it_stops(tmp_path):
    events = []
    transport = _RecordingTransport("memory", events)
    spooler = Spooler(transport, JobStore(tmp_path), idle_timeout_seconds=0)
    advertising = _advertising(_RecordingAdvertiser("memory", events))
    instance = PrinterInstance(transport, spooler, advertising=advertising)
    stop = asyncio.Event()
    run = asyncio.create_task(instance.run(stop))
    for _ in range(20):
        await asyncio.sleep(0)
    stop.set()
    await asyncio.wait_for(run, 5.0)
    assert events == ["transport opened", "advertised", "withdrawn", "transport closed"]


def test_an_advertisement_needs_an_endpoint():
    with pytest.raises(ValueError, match="endpoint"):
        Advertisement(
            name="Desk Printer",
            printer_uuid=PRINTER_UUID,
            model=ModelIdentity(manufacturer="Papyrium", model="Byte Dot"),
            languages=(),
            endpoints=(),
        )
