"""JobRendering and JobRenderer: bytes through a model into outputs."""

import asyncio
import json

from papyrium.core.jobs import JobStore
from papyrium.core.rendering import JobRenderer, JobRendering
from papyrium.core.spooler import Spooler
from papyrium.core.testing import ByteDotModel, JsonOutput, MemoryTransport


def test_pages_reach_every_output_as_they_complete(tmp_path):
    first, second = JsonOutput(name="a", filename="a.json"), JsonOutput(name="b", filename="b.json")
    rendering = JobRendering(ByteDotModel(name="m"), [first, second], tmp_path)
    rendering.feed(b"AB\x0cC")
    assert rendering.page_count == 1
    assert len(first.documents[0]) == len(second.documents[0]) == 1
    filepaths = rendering.finish()
    assert rendering.page_count == 2
    assert sorted(path.name for path in filepaths) == ["a.json", "b.json"]


def test_finish_twice_writes_once(tmp_path):
    rendering = JobRendering(ByteDotModel(name="m"), [JsonOutput(name="j")], tmp_path)
    rendering.feed(b"A")
    assert len(rendering.finish()) == 1
    assert rendering.finish() == []


async def _serve(tmp_path, model, feeds):
    transport = MemoryTransport(name="memory")
    renderer = JobRenderer(model, [JsonOutput(name="json")])
    spooler = Spooler(transport, JobStore(tmp_path), idle_timeout_seconds=0, listener=renderer)
    render_task = asyncio.create_task(renderer.run())
    async with transport:
        spool_task = asyncio.create_task(spooler.run())
        for feed in feeds:
            if feed is None:
                for _ in range(10):
                    await asyncio.sleep(0)
                spooler.end_job()
            else:
                await transport.feed(feed)
    await spool_task
    renderer.close()
    await asyncio.wait_for(render_task, 5.0)


async def test_renderer_writes_each_jobs_pages_into_its_directory(tmp_path):
    await _serve(tmp_path, ByteDotModel(name="m"), [b"AB\x0cC", None, b"D"])
    first = json.loads((tmp_path / "job-0001" / "pages.json").read_text())
    second = json.loads((tmp_path / "job-0002" / "pages.json").read_text())
    assert [page["number"] for page in first] == [1, 2]
    assert [page["number"] for page in second] == [1]


class _FailingModel(ByteDotModel):
    def create_interpreter(self):
        raise RuntimeError("broken printer")


async def test_a_rendering_failure_is_logged_and_the_capture_kept(tmp_path, caplog):
    await _serve(tmp_path, _FailingModel(name="m"), [b"AB"])
    assert (tmp_path / "job-0001" / "capture.prn").read_bytes() == b"AB"
    assert not (tmp_path / "job-0001" / "pages.json").exists()
    assert "rendering job 1 failed" in caplog.text
