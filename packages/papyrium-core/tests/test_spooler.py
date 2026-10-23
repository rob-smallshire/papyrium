"""The Spooler: every byte captured, jobs ended by idle timeout or request."""

import asyncio

import pytest
from papyrium.core.jobs import CAPTURE_FILENAME, JobEndReason, JobStore
from papyrium.core.spooler import Spooler
from papyrium.core.testing import MemoryTransport

QUIET = 0.2


async def _settle():
    """Let the spooler pull whatever has been sent."""
    for _ in range(10):
        await asyncio.sleep(0)


@pytest.fixture
async def rig(tmp_path):
    transport = MemoryTransport(name="memory")
    spooler = Spooler(transport, JobStore(tmp_path), idle_timeout_seconds=0)
    await transport.open()
    task = asyncio.create_task(spooler.run())
    yield transport, spooler, tmp_path
    await transport.close()
    await asyncio.wait_for(task, 1.0)


def _captures(dirpath):
    return {
        job_dirpath.name: (job_dirpath / CAPTURE_FILENAME).read_bytes()
        for job_dirpath in sorted(dirpath.glob("job-*"))
    }


async def test_no_job_until_bytes_arrive(rig):
    transport, spooler, dirpath = rig
    await _settle()
    assert spooler.current_job is None
    assert _captures(dirpath) == {}


async def test_bytes_are_captured_into_a_job(rig):
    transport, spooler, dirpath = rig
    await transport.feed(b"HELLO\n\r")
    await _settle()
    assert _captures(dirpath) == {"job-0001": b"HELLO\n\r"}


async def test_a_disconnect_does_not_end_the_job(rig):
    transport, spooler, dirpath = rig
    await transport.feed(b"ONE")
    await transport.feed(b"TWO")
    await _settle()
    assert _captures(dirpath) == {"job-0001": b"ONETWO"}


async def test_requested_end_starts_a_new_job_with_the_next_byte(rig):
    transport, spooler, dirpath = rig
    await transport.feed(b"ONE")
    await _settle()
    ended = spooler.end_job()
    assert ended.end_reason is JobEndReason.REQUESTED
    assert spooler.current_job is None
    await transport.feed(b"TWO")
    await _settle()
    assert _captures(dirpath) == {"job-0001": b"ONE", "job-0002": b"TWO"}


async def test_requested_end_with_no_job_is_a_no_op(rig):
    transport, spooler, dirpath = rig
    assert spooler.end_job() is None


async def test_shutdown_ends_the_current_job(tmp_path):
    transport = MemoryTransport(name="memory")
    spooler = Spooler(transport, JobStore(tmp_path), idle_timeout_seconds=0)
    async with transport:
        task = asyncio.create_task(spooler.run())
        await transport.feed(b"ABC")
        await _settle()
        job = spooler.current_job
    await asyncio.wait_for(task, 1.0)
    assert job.end_reason is JobEndReason.SHUTDOWN


async def test_idle_timeout_ends_the_job(tmp_path):
    transport = MemoryTransport(name="memory")
    spooler = Spooler(transport, JobStore(tmp_path), idle_timeout_seconds=0.05)
    async with transport:
        task = asyncio.create_task(spooler.run())
        await transport.feed(b"ONE")
        await _settle()
        job = spooler.current_job
        await asyncio.sleep(QUIET)
        assert job.end_reason is JobEndReason.IDLE
        assert spooler.current_job is None
        await transport.feed(b"TWO")
        await _settle()
    await asyncio.wait_for(task, 1.0)
    assert _captures(tmp_path) == {"job-0001": b"ONE", "job-0002": b"TWO"}


async def test_bytes_keep_an_idle_job_open(tmp_path):
    transport = MemoryTransport(name="memory")
    spooler = Spooler(transport, JobStore(tmp_path), idle_timeout_seconds=0.1)
    async with transport:
        task = asyncio.create_task(spooler.run())
        for _ in range(5):
            await transport.feed(b"X")
            await asyncio.sleep(0.04)
        assert spooler.current_job is not None
        assert spooler.current_job.byte_count == 5
    await asyncio.wait_for(task, 1.0)


async def test_zero_idle_timeout_never_ends_a_job(tmp_path):
    transport = MemoryTransport(name="memory")
    spooler = Spooler(transport, JobStore(tmp_path), idle_timeout_seconds=0)
    async with transport:
        task = asyncio.create_task(spooler.run())
        await transport.feed(b"X")
        await asyncio.sleep(QUIET)
        assert spooler.current_job is not None
    await asyncio.wait_for(task, 1.0)
