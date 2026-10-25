"""Jobs: numbered directories each holding a raw capture and a job record."""

from __future__ import annotations

import enum
import json
import logging
import re
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from papyrium.exception import DataError

logger = logging.getLogger(__name__)

#: The raw bytes of a job, exactly as received, before any interpretation.
CAPTURE_FILENAME = "capture.prn"

#: The job's metadata as JSON.
JOB_RECORD_FILENAME = "job.json"

#: The printer's own record, beside its jobs: its UUID.
PRINTER_RECORD_FILENAME = "printer.json"

_JOB_DIRNAME_PATTERN = re.compile(r"^job-(\d+)$")

Clock = Callable[[], datetime]


def _utc_now() -> datetime:
    return datetime.now(UTC)


def job_dirname(number: int) -> str:
    return f"job-{number:04d}"


class JobEndReason(enum.Enum):
    """Why a job ended."""

    #: No bytes arrived for the idle timeout.
    IDLE = "idle"
    #: An end was requested through the CLI or API.
    REQUESTED = "requested"
    #: The printer instance shut down.
    SHUTDOWN = "shutdown"


@dataclass(frozen=True)
class JobRecord:
    """A job as described by its record file and its capture.

    The byte count is the size of the capture, which is complete up to the
    last byte received even while the job is open.
    """

    number: int
    dirpath: Path
    transport_name: str
    started_at: datetime
    ended_at: datetime | None
    end_reason: JobEndReason | None
    byte_count: int
    #: How the printer was set up for the job, for replay; None if not recorded.
    printer_setup: dict[str, Any] | None = None

    @classmethod
    def read(cls, dirpath: Path) -> JobRecord:
        """Read the record in the job directory *dirpath*."""
        record = json.loads((dirpath / JOB_RECORD_FILENAME).read_text())
        ended_at = record["ended_at"]
        end_reason = record["end_reason"]
        return cls(
            number=record["number"],
            dirpath=dirpath,
            transport_name=record["transport"],
            started_at=datetime.fromisoformat(record["started_at"]),
            ended_at=None if ended_at is None else datetime.fromisoformat(ended_at),
            end_reason=None if end_reason is None else JobEndReason(end_reason),
            byte_count=(dirpath / CAPTURE_FILENAME).stat().st_size,
            printer_setup=record.get("printer"),
        )


class JobCapture:
    """One job: its raw capture, written as bytes arrive, and its record.

    Every appended chunk is flushed to the capture file at once, so a
    capture is complete up to the last byte received even if the process
    dies.
    """

    def __init__(
        self,
        number: int,
        dirpath: Path,
        *,
        transport_name: str,
        printer_setup: Mapping[str, Any] | None,
        clock: Clock,
    ) -> None:
        self._number = number
        self._dirpath = dirpath
        self._transport_name = transport_name
        self._printer_setup = None if printer_setup is None else dict(printer_setup)
        self._clock = clock
        self._started_at = clock()
        self._ended_at: datetime | None = None
        self._end_reason: JobEndReason | None = None
        self._byte_count = 0
        dirpath.mkdir(parents=True)
        self._capture = open(dirpath / CAPTURE_FILENAME, "wb")
        self._write_record()

    @property
    def number(self) -> int:
        return self._number

    @property
    def dirpath(self) -> Path:
        return self._dirpath

    @property
    def byte_count(self) -> int:
        return self._byte_count

    @property
    def closed(self) -> bool:
        return self._end_reason is not None

    @property
    def end_reason(self) -> JobEndReason | None:
        return self._end_reason

    def append(self, chunk: bytes) -> None:
        """Append *chunk* to the capture and flush it to disc."""
        self._capture.write(chunk)
        self._capture.flush()
        self._byte_count += len(chunk)

    def close(self, reason: JobEndReason) -> None:
        """End the job for *reason*; closing an ended job does nothing."""
        if self.closed:
            return
        self._capture.close()
        self._ended_at = self._clock()
        self._end_reason = reason
        self._write_record()
        logger.info("job %d ended (%s), %d bytes", self._number, reason.value, self._byte_count)

    def _write_record(self) -> None:
        record = {
            "number": self._number,
            "transport": self._transport_name,
            "printer": self._printer_setup,
            "started_at": self._started_at.isoformat(),
            "ended_at": None if self._ended_at is None else self._ended_at.isoformat(),
            "end_reason": None if self._end_reason is None else self._end_reason.value,
        }
        record_filepath = self._dirpath / JOB_RECORD_FILENAME
        temporary_filepath = record_filepath.with_suffix(".tmp")
        temporary_filepath.write_text(json.dumps(record, indent=2) + "\n")
        temporary_filepath.replace(record_filepath)


class JobStore:
    """Allocates numbered job directories under an output directory.

    Numbering continues from the highest job already present, so restarting
    a printer instance never overwrites earlier jobs.
    """

    def __init__(self, output_dirpath: Path, *, clock: Clock = _utc_now) -> None:
        self._output_dirpath = Path(output_dirpath)
        self._clock = clock

    @property
    def output_dirpath(self) -> Path:
        return self._output_dirpath

    def create_job(
        self, *, transport_name: str, printer_setup: Mapping[str, Any] | None = None
    ) -> JobCapture:
        """Start the next job.

        *printer_setup* records how the printer was configured (its model
        and options), so the capture can be replayed to the same pages.
        """
        number = self._last_number() + 1
        job = JobCapture(
            number,
            self._output_dirpath / job_dirname(number),
            transport_name=transport_name,
            printer_setup=printer_setup,
            clock=self._clock,
        )
        logger.info("job %d started in %s", number, job.dirpath)
        return job

    def printer_uuid(self) -> uuid.UUID:
        """The UUID of the printer whose jobs these are, created on first use.

        One output directory holds one printer's jobs, so the UUID is kept
        beside them and stays the same across restarts and renames.

        Raises:
            DataError: The printer record exists but cannot be read.
        """
        record_filepath = self._output_dirpath / PRINTER_RECORD_FILENAME
        if record_filepath.exists():
            try:
                return uuid.UUID(json.loads(record_filepath.read_text())["uuid"])
            except (OSError, ValueError, KeyError, TypeError) as error:
                raise DataError(f"cannot read the printer record {record_filepath}") from error
        printer_uuid = uuid.uuid4()
        self._output_dirpath.mkdir(parents=True, exist_ok=True)
        temporary_filepath = record_filepath.with_suffix(".tmp")
        temporary_filepath.write_text(json.dumps({"uuid": str(printer_uuid)}, indent=2) + "\n")
        temporary_filepath.replace(record_filepath)
        logger.info("new printer %s", printer_uuid)
        return printer_uuid

    def records(self) -> list[JobRecord]:
        """The records of every job in the store, in job number order.

        A job whose record cannot be read is left out, with a warning
        saying why.
        """
        records = []
        for _, dirpath in self._job_dirpaths():
            try:
                records.append(JobRecord.read(dirpath))
            except (OSError, ValueError, KeyError) as error:
                logger.warning("skipping %s: unreadable job record: %s", dirpath, error)
        return records

    def _job_dirpaths(self) -> list[tuple[int, Path]]:
        if not self._output_dirpath.is_dir():
            return []
        return sorted(
            (int(match.group(1)), child)
            for child in self._output_dirpath.iterdir()
            if (match := _JOB_DIRNAME_PATTERN.match(child.name)) and child.is_dir()
        )

    def _last_number(self) -> int:
        return max((number for number, _ in self._job_dirpaths()), default=0)
