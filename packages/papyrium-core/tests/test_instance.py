"""PrinterInstance: a transport, spooler and renderer run together until stopped."""

import asyncio
import json

from papyrium.core.instance import PrinterInstance
from papyrium.core.jobs import JobStore
from papyrium.core.rendering import JobRenderer
from papyrium.core.spooler import Spooler
from papyrium.core.testing import ByteDotModel, JsonOutput, MemoryTransport


def _instance(tmp_path, *, render=True):
    transport = MemoryTransport(name="memory")
    renderer = JobRenderer(ByteDotModel(name="m"), [JsonOutput(name="json")]) if render else None
    spooler = Spooler(transport, JobStore(tmp_path), idle_timeout_seconds=0, listener=renderer)
    return PrinterInstance(transport, spooler, renderer), transport


async def _settle():
    for _ in range(20):
        await asyncio.sleep(0)


async def test_runs_until_stopped_and_ends_the_job_on_shutdown(tmp_path):
    instance, transport = _instance(tmp_path)
    stop = asyncio.Event()
    run = asyncio.create_task(instance.run(stop))
    await _settle()
    await transport.feed(b"AB\x0cC")
    await _settle()
    stop.set()
    await asyncio.wait_for(run, 5.0)
    record = json.loads((tmp_path / "job-0001" / "job.json").read_text())
    assert record["end_reason"] == "shutdown"
    pages = json.loads((tmp_path / "job-0001" / "pages.json").read_text())
    assert [page["number"] for page in pages] == [1, 2]


async def test_captures_without_a_renderer(tmp_path):
    instance, transport = _instance(tmp_path, render=False)
    stop = asyncio.Event()
    run = asyncio.create_task(instance.run(stop))
    await _settle()
    await transport.feed(b"AB")
    await _settle()
    stop.set()
    await asyncio.wait_for(run, 5.0)
    assert (tmp_path / "job-0001" / "capture.prn").read_bytes() == b"AB"
    assert not (tmp_path / "job-0001" / "pages.json").exists()
