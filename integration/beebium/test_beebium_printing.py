"""A BBC Micro emulated by Beebium prints to papyrium serve over raw TCP.

Not part of the default suite: it needs a Beebium build and its Python
client. Run from the repository root with::

    BEEBIUM_SERVER=/Users/rjs/Code/beebium/build/src/server/beebium-model-b \\
    BEEBIUM_ROM_DIR=/Users/rjs/Code/beebium/roms \\
        uv run --with /Users/rjs/Code/beebium/clients/beebium-python-client \\
        pytest integration/beebium

The Beebium client registers the ``launch_bbc`` fixture as a pytest plugin.
Every wait polls the guest or the capture, never the wall clock alone.
"""

from __future__ import annotations

import json
import re
import signal
import subprocess
import sys
import time

import pytest

beebium_client = pytest.importorskip("beebium.client")
from beebium.ext.peripheral.tcp_printer import TcpPrinter  # noqa: E402

TIMEOUT = 20.0

# Assembled at run time so it reaches the screen only after the print has
# executed, not as part of the echoed command line.
MARKER_EXPR = '"DO"+"NE"'
MARKER = "DONE"


def _wait_until(condition, description, timeout=TIMEOUT):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if condition():
            return
        time.sleep(0.05)
    pytest.fail(f"timed out waiting for {description}")


def _screen(bbc):
    text = bbc.video.screen_text().text
    return "\n".join(text) if isinstance(text, list) else text


def _type_line(bbc, line):
    bbc.keyboard.type(line + "\r")
    bbc.keyboard.wait_until_typing_complete()


@pytest.fixture
def papyrium(tmp_path):
    """A papyrium serve process on a free loopback port; yields (port, output_dirpath)."""
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
        ],
        stderr=subprocess.PIPE,
        text=True,
    )
    pattern = re.compile(r"listening for raw TCP on 127\.0\.0\.1:(\d+)")
    port = None
    for line in process.stderr:
        if match := pattern.search(line):
            port = int(match.group(1))
            break
    assert port is not None, "papyrium serve did not report its port"
    try:
        yield port, tmp_path
    finally:
        process.send_signal(signal.SIGINT)
        process.wait(timeout=10)


def test_bbc_print_with_fx6_0_is_captured_as_hello_lf_cr(launch_bbc, papyrium):
    port, output_dirpath = papyrium
    bbc = launch_bbc(extra_args=["--tcp-printer", f"host=127.0.0.1:port={port}"])
    bbc.wait_until_ready()
    printer = bbc.extensions[TcpPrinter]
    _wait_until(lambda: printer.get_status().connected, "the printer to connect")
    _wait_until(lambda: ">" in _screen(bbc), "the BASIC prompt")

    _type_line(bbc, "*FX6,0")
    _type_line(bbc, "*FX5,1")
    _type_line(bbc, f'VDU 2:PRINT "HELLO":VDU 1,12:VDU 3:PRINT {MARKER_EXPR}')
    _wait_until(lambda: MARKER in _screen(bbc), "the print to finish")

    capture_filepath = output_dirpath / "job-0001" / "capture.prn"
    expected = b"HELLO\n\r\x0c"
    _wait_until(
        lambda: capture_filepath.exists() and len(capture_filepath.read_bytes()) >= len(expected),
        "the bytes to reach the capture",
    )
    assert capture_filepath.read_bytes() == expected
    record = json.loads((output_dirpath / "job-0001" / "job.json").read_text())
    assert record["transport"] == "raw-tcp"
    assert record["end_reason"] is None
