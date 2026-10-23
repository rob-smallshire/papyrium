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
    assert job.closed


def test_closing_twice_keeps_the_first_reason(tmp_path):
    job = JobStore(tmp_path).create_job(transport_name="memory")
    job.close(JobEndReason.IDLE)
    job.close(JobEndReason.SHUTDOWN)
    assert _record(job)["end_reason"] == "idle"


def test_records_lists_jobs_in_number_order(tmp_path):
    clock = _Clock()
    store = JobStore(tmp_path, clock=clock)
    for _ in range(2):
        job = store.create_job(transport_name="raw-tcp")
        job.append(b"AB")
        job.close(JobEndReason.REQUESTED)
    open_job = store.create_job(transport_name="raw-tcp")
    records = store.records()
    assert [record.number for record in records] == [1, 2, 3]
    assert records[0].byte_count == 2
    assert records[0].end_reason is JobEndReason.REQUESTED
    assert records[0].started_at == clock.now
    assert records[2].end_reason is None
    assert records[2].ended_at is None
    assert records[2].dirpath == open_job.dirpath


def test_record_of_an_open_job_counts_the_bytes_captured_so_far(tmp_path):
    store = JobStore(tmp_path)
    job = store.create_job(transport_name="raw-tcp")
    job.append(b"HELLO")
    assert store.records()[0].byte_count == 5


def test_records_of_a_missing_directory_is_empty(tmp_path):
    assert JobStore(tmp_path / "absent").records() == []


def test_an_unreadable_record_is_skipped_with_a_warning(tmp_path, caplog):
    store = JobStore(tmp_path)
    store.create_job(transport_name="memory").close(JobEndReason.REQUESTED)
    (tmp_path / "job-0002").mkdir()
    (tmp_path / "job-0002" / JOB_RECORD_FILENAME).write_text("{not json")
    assert [record.number for record in store.records()] == [1]
    assert "job-0002" in caplog.text
