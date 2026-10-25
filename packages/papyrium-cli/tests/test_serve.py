"""papyrium serve as a real process: bytes over TCP land in a job capture."""

import json
import re
import signal
import socket
import subprocess
import sys
import time

import pytest

pytestmark = pytest.mark.skipif(sys.platform == "win32", reason="uses SIGINT")


def _wait_for_port(process):
    deadline = time.monotonic() + 10
    pattern = re.compile(r"listening for raw TCP on 127\.0\.0\.1:(\d+)")
    for line in process.stderr:
        if match := pattern.search(line):
            return int(match.group(1))
        if time.monotonic() > deadline:
            break
    raise AssertionError("server did not report its port")


def test_serve_captures_a_job_and_closes_it_on_shutdown(tmp_path):
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "papyrium.cli",
            "serve",
            "--output-dir",
            str(tmp_path),
            "-T",
            "host=127.0.0.1",
            "-T",
            "port=0",
            "--idle-timeout",
            "0",
            "--name",
            "Test Printer",
        ],
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        port = _wait_for_port(process)
        with socket.create_connection(("127.0.0.1", port)) as connection:
            connection.sendall(b"HELLO\n\r")
        with socket.create_connection(("127.0.0.1", port)) as connection:
            connection.sendall(b"\x0c")
        capture_filepath = tmp_path / "job-0001" / "capture.prn"
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            if capture_filepath.exists() and capture_filepath.read_bytes() == b"HELLO\n\r\x0c":
                break
            time.sleep(0.05)
        assert capture_filepath.read_bytes() == b"HELLO\n\r\x0c"
    finally:
        process.send_signal(signal.SIGINT)
        process.wait(timeout=10)
    assert process.returncode == 0
    record = json.loads((tmp_path / "job-0001" / "job.json").read_text())
    assert record["end_reason"] == "shutdown"
    printer_uuid = json.loads((tmp_path / "printer.json").read_text())["uuid"]
    assert record["printer"] == {
        "model": "epson-fx80",
        "options": {},
        "name": "Test Printer",
        "uuid": printer_uuid,
    }
    assert not (tmp_path / "job-0002").exists()
    # The form feed ejected page 1; nothing followed it, so there is no page 2.
    job_dirpath = tmp_path / "job-0001"
    assert (job_dirpath / "page-0001.png").is_file()
    assert not (job_dirpath / "page-0002.png").exists()
    assert (job_dirpath / "job.pdf").is_file()


def test_advertising_a_printer_only_this_machine_can_reach_says_so_and_prints_on(tmp_path):
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "papyrium.cli",
            "serve",
            "--output-dir",
            str(tmp_path),
            "-T",
            "host=127.0.0.1",
            "-T",
            "port=0",
            "--advertise",
            "--capture-only",
        ],
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        port = _wait_for_port(process)
        warning = next(line for line in process.stderr if "not advertising" in line)
        with socket.create_connection(("127.0.0.1", port)) as connection:
            connection.sendall(b"HELLO")
        capture_filepath = tmp_path / "job-0001" / "capture.prn"
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            if capture_filepath.exists() and capture_filepath.read_bytes() == b"HELLO":
                break
            time.sleep(0.05)
    finally:
        process.send_signal(signal.SIGINT)
        process.wait(timeout=10)
    assert process.returncode == 0
    assert "only this machine" in warning
    assert capture_filepath.read_bytes() == b"HELLO"
