"""JobStore and JobCapture: numbered job directories holding raw captures."""

import json
from datetime import UTC, datetime, timedelta

from papyrium.core.jobs import CAPTURE_FILENAME, JOB_RECORD_FILENAME, JobEndReason, JobStore


class _Clock:
    def __init__(self):
        self.now = datetime(2026, 10, 23, 12, 0, 0, tzinfo=UTC)

    def __call__(self):
        return self.now


def _record(job):
    return json.loads((job.dirpath / JOB_RECORD_FILENAME).read_text())


def test_jobs_are_numbered_from_one(tmp_path):
    store = JobStore(tmp_path)
    first = store.create_job(transport_name="memory")
    first.close(JobEndReason.REQUESTED)
    second = store.create_job(transport_name="memory")
    assert (first.number, second.number) == (1, 2)
    assert first.dirpath == tmp_path / "job-0001"
    assert second.dirpath == tmp_path / "job-0002"


def test_numbering_continues_after_existing_jobs(tmp_path):
    (tmp_path / "job-0007").mkdir()
    (tmp_path / "unrelated").mkdir()
    assert JobStore(tmp_path).create_job(transport_name="memory").number == 8


def test_output_directory_is_created(tmp_path):
    output_dirpath = tmp_path / "spool" / "out"
    JobStore(output_dirpath).create_job(transport_name="memory")
    assert (output_dirpath / "job-0001").is_dir()


def test_appended_bytes_are_in_the_capture_immediately(tmp_path):
    job = JobStore(tmp_path).create_job(transport_name="memory")
    job.append(b"HELLO")
    job.append(b"\n\r")
    assert (job.dirpath / CAPTURE_FILENAME).read_bytes() == b"HELLO\n\r"
    assert job.byte_count == 7


def test_record_describes_an_open_job(tmp_path):
    clock = _Clock()
    job = JobStore(tmp_path, clock=clock).create_job(transport_name="raw-tcp")
    assert _record(job) == {
        "number": 1,
        "transport": "raw-tcp",
        "started_at": "2026-10-23T12:00:00+00:00",
        "ended_at": None,
        "end_reason": None,
        "byte_count": 0,
    }


def test_record_describes_a_closed_job(tmp_path):
    clock = _Clock()
    job = JobStore(tmp_path, clock=clock).create_job(transport_name="raw-tcp")
    job.append(b"ABC")
    clock.now += timedelta(seconds=5)
    job.close(JobEndReason.IDLE)
    record = _record(job)
    assert record["ended_at"] == "2026-10-23T12:00:05+00:00"
    assert record["end_reason"] == "idle"
    assert record["byte_count"] == 3
    assert job.closed


def test_closing_twice_keeps_the_first_reason(tmp_path):
    job = JobStore(tmp_path).create_job(transport_name="memory")
    job.close(JobEndReason.IDLE)
    job.close(JobEndReason.SHUTDOWN)
    assert _record(job)["end_reason"] == "idle"
