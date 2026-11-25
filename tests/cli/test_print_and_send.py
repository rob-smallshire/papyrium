"""The one-shot commands: print a file as a job, or send it to a running printer."""

import json
import socket
import threading

import pytest
from click.testing import CliRunner
from exit_codes import ExitCode

from papyrium.cli import cli
from papyrium.core.jobs import CAPTURE_FILENAME, JOB_RECORD_FILENAME, JobEndReason, JobStore

_JOB = b"HELLO FROM B2\r\n\x0cPAGE TWO\r\n"


@pytest.fixture
def run():
    def _run(*args, input=None):
        return CliRunner().invoke(cli, list(args), input=input, catch_exceptions=False)

    return _run


def _job_record(dirpath):
    return json.loads((dirpath / JOB_RECORD_FILENAME).read_text())


def test_print_makes_a_job_as_serve_would(run, tmp_path):
    saved_filepath = tmp_path / "b2-printer.dat"
    saved_filepath.write_bytes(_JOB)
    jobs_dirpath = tmp_path / "jobs"
    result = run("print", str(saved_filepath), "--output-dir", str(jobs_dirpath))
    assert result.exit_code == 0, result.output
    job_dirpath = jobs_dirpath / "job-0001"
    assert (job_dirpath / CAPTURE_FILENAME).read_bytes() == _JOB
    assert sorted(path.name for path in job_dirpath.iterdir()) == [
        CAPTURE_FILENAME,
        "job.json",
        "job.pdf",
        "page-0001.png",
        "page-0002.png",
    ]
    record = _job_record(job_dirpath)
    assert record["transport"] == "print"
    assert record["end_reason"] == "end-of-input"
    assert record["printer"]["model"] == "epson-fx80"
    assert record["printer"]["uuid"] == str(JobStore(jobs_dirpath).printer_uuid())
    assert record["printer"]["name"] == "Epson FX-80 (Papyrium)"


def test_print_numbers_its_job_after_those_already_there(run, tmp_path):
    jobs_dirpath = tmp_path / "jobs"
    earlier = JobStore(jobs_dirpath).create_job(transport_name="raw-tcp")
    earlier.append(b"EARLIER")
    earlier.close(JobEndReason.IDLE)
    saved_filepath = tmp_path / "saved.dat"
    saved_filepath.write_bytes(_JOB)
    result = run("print", str(saved_filepath), "--output-dir", str(jobs_dirpath))
    assert result.exit_code == 0, result.output
    assert (jobs_dirpath / "job-0002" / CAPTURE_FILENAME).read_bytes() == _JOB


def test_print_reads_standard_input_given_a_dash(run, tmp_path):
    jobs_dirpath = tmp_path / "jobs"
    result = run("print", "-", "--output-dir", str(jobs_dirpath), input=_JOB)
    assert result.exit_code == 0, result.output
    assert (jobs_dirpath / "job-0001" / CAPTURE_FILENAME).read_bytes() == _JOB


def test_print_records_the_model_and_its_options(run, tmp_path):
    saved_filepath = tmp_path / "saved.dat"
    saved_filepath.write_bytes(b"A\rB\r")
    jobs_dirpath = tmp_path / "jobs"
    result = run(
        "print",
        str(saved_filepath),
        "-m",
        "epson-fx80",
        "-M",
        "auto-line-feed=yes",
        "-o",
        "png",
        "--name",
        "Desk printer",
        "--output-dir",
        str(jobs_dirpath),
    )
    assert result.exit_code == 0, result.output
    record = _job_record(jobs_dirpath / "job-0001")
    assert record["printer"]["options"] == {"auto-line-feed": "yes"}
    assert record["printer"]["name"] == "Desk printer"
    replay = run("render", str(jobs_dirpath / "job-0001"), "-o", "png", "--as", "json")
    assert replay.exit_code == 0, replay.output


def test_print_reports_the_job_and_its_files(run, tmp_path):
    saved_filepath = tmp_path / "saved.dat"
    saved_filepath.write_bytes(_JOB)
    jobs_dirpath = tmp_path / "jobs"
    result = run("print", str(saved_filepath), "--output-dir", str(jobs_dirpath), "--as", "json")
    assert result.exit_code == 0, result.output
    assert "job-0001" in result.output
    assert "page-0002.png" in result.output


def test_print_of_nothing_makes_no_job(tmp_path):
    jobs_dirpath = tmp_path / "jobs"
    result = CliRunner().invoke(cli, ["print", "-", "--output-dir", str(jobs_dirpath)], input=b"")
    assert result.exit_code == ExitCode.DATA_ERR
    assert "no bytes" in result.output
    assert not list(jobs_dirpath.glob("job-*"))


class _Listener:
    """A raw TCP printer port that keeps whatever each connection sends."""

    def __init__(self):
        self._socket = socket.create_server(("127.0.0.1", 0))
        self.port = self._socket.getsockname()[1]
        self.received = []
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()

    def _serve(self):
        connection, _ = self._socket.accept()
        data = bytearray()
        with connection:
            while chunk := connection.recv(4096):
                data += chunk
        self.received.append(bytes(data))

    def join(self):
        self._thread.join(timeout=5)
        self._socket.close()


def test_send_delivers_a_file_to_a_printer_port(run, tmp_path):
    saved_filepath = tmp_path / "b2-printer.dat"
    saved_filepath.write_bytes(_JOB)
    listener = _Listener()
    result = run("send", str(saved_filepath), "--host", "127.0.0.1", "--port", str(listener.port))
    listener.join()
    assert result.exit_code == 0, result.output
    assert listener.received == [_JOB]


def test_send_delivers_standard_input_given_a_dash(run):
    listener = _Listener()
    result = run("send", "-", "--host", "127.0.0.1", "--port", str(listener.port), input=_JOB)
    listener.join()
    assert result.exit_code == 0, result.output
    assert listener.received == [_JOB]


def test_send_to_a_port_nobody_listens_on_says_so(tmp_path):
    saved_filepath = tmp_path / "saved.dat"
    saved_filepath.write_bytes(_JOB)
    with socket.create_server(("127.0.0.1", 0)) as unused:
        port = unused.getsockname()[1]
    result = CliRunner().invoke(
        cli, ["send", str(saved_filepath), "--host", "127.0.0.1", "--port", str(port)]
    )
    assert result.exit_code == ExitCode.UNAVAILABLE
    assert f"127.0.0.1:{port}" in result.output
