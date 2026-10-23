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
def start_papyrium(tmp_path):
    """Start papyrium serve with extra arguments; returns (port, output_dirpath)."""
    processes = []

    def start(*extra_args):
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
                *extra_args,
            ],
            stderr=subprocess.PIPE,
            text=True,
        )
        processes.append(process)
        pattern = re.compile(r"listening for raw TCP on 127\.0\.0\.1:(\d+)")
        for line in process.stderr:
            if match := pattern.search(line):
                return int(match.group(1)), tmp_path
        raise AssertionError("papyrium serve did not report its port")

    yield start
    for process in processes:
        process.send_signal(signal.SIGINT)
        process.wait(timeout=10)


@pytest.fixture
def papyrium(start_papyrium):
    """papyrium serve with no idle timeout; yields (port, output_dirpath)."""
    return start_papyrium("--idle-timeout", "0")


def _bbc_printing_to(launch_bbc, port, *, line_feeds=True):
    """A Model B at the BASIC prompt, its parallel printer connected to *port*.

    With *line_feeds* the MOS sends LF to the printer (*FX6,0); otherwise it
    keeps its default and sends CR alone.
    """
    bbc = launch_bbc(extra_args=["--tcp-printer", f"host=127.0.0.1:port={port}"])
    bbc.wait_until_ready()
    printer = bbc.extensions[TcpPrinter]
    _wait_until(lambda: printer.get_status().connected, "the printer to connect")
    _wait_until(lambda: ">" in _screen(bbc), "the BASIC prompt")
    if line_feeds:
        _type_line(bbc, "*FX6,0")
    _type_line(bbc, "*FX5,1")
    return bbc


def _pdf_text(output_dirpath):
    from pypdf import PdfReader

    pdf_filepath = output_dirpath / "job-0001" / "job.pdf"
    _wait_until(pdf_filepath.exists, "the job's PDF")
    return [page.extract_text() for page in PdfReader(pdf_filepath).pages]


def _wait_for_capture(output_dirpath, length):
    capture_filepath = output_dirpath / "job-0001" / "capture.prn"
    _wait_until(
        lambda: capture_filepath.exists() and len(capture_filepath.read_bytes()) >= length,
        f"{length} bytes in the capture",
    )
    return capture_filepath.read_bytes()


def _fx80_page_images(data):
    from papyrium.model.epson_fx80 import EpsonFx80
    from papyrium.output.png import PngOutput

    interpreter = EpsonFx80(name="epson-fx80").create_interpreter()
    pages = interpreter.feed(data) + interpreter.finish()
    return [PngOutput(name="png").render(page).tobytes() for page in pages]


def test_bbc_print_with_fx6_0_is_captured_as_hello_lf_cr(launch_bbc, papyrium):
    port, output_dirpath = papyrium
    bbc = _bbc_printing_to(launch_bbc, port)
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


def test_bbc_text_styles_print_as_an_fx80_page(launch_bbc, start_papyrium):
    """Escape sequences sent with VDU 1 drive the FX-80 emulation to a page and a PDF."""
    port, output_dirpath = start_papyrium("--idle-timeout", "1")
    bbc = _bbc_printing_to(launch_bbc, port)
    _type_line(
        bbc,
        'VDU 2,1,27,1,69:PRINT "PAPYRIUM ON A BBC MICRO":VDU 1,27,1,70,1,27,1,52'
        f':PRINT "ITALIC FROM BBC BASIC":VDU 1,27,1,53,1,12,3:PRINT {MARKER_EXPR}',
    )
    _wait_until(lambda: MARKER in _screen(bbc), "the print to finish")
    expected = b"\x1bEPAPYRIUM ON A BBC MICRO\n\r\x1bF\x1b4ITALIC FROM BBC BASIC\n\r\x1b5\x0c"
    assert _wait_for_capture(output_dirpath, len(expected)) == expected

    page_filepath = output_dirpath / "job-0001" / "page-0001.png"
    _wait_until(page_filepath.exists, "the page to be ejected")
    from PIL import Image

    with Image.open(page_filepath) as image:
        assert [image.tobytes()] == _fx80_page_images(expected)

    (text,) = _pdf_text(output_dirpath)
    assert "PAPYRIUM ON A BBC MICRO" in text
    assert "ITALIC FROM BBC BASIC" in text


LISTING_PROGRAM = [
    '10 PRINT "HELLO"',
    "20 GOTO 10",
]


def test_bbc_listing_with_cr_only_needs_auto_line_feed(launch_bbc, start_papyrium):
    """At *FX6,10 the BBC sends CR alone; the FX-80's auto line feed switch copes."""
    port, output_dirpath = start_papyrium("-M", "auto-line-feed=yes", "--idle-timeout", "1")
    bbc = _bbc_printing_to(launch_bbc, port, line_feeds=False)
    for line in LISTING_PROGRAM:
        _type_line(bbc, line)
    _type_line(bbc, "VDU 2")
    _type_line(bbc, "LIST")  # LIST must begin its line.
    _type_line(bbc, f"VDU 3:PRINT {MARKER_EXPR}")
    _wait_until(lambda: MARKER in _screen(bbc), "the listing to finish")

    capture_filepath = output_dirpath / "job-0001" / "capture.prn"
    _wait_until(capture_filepath.exists, "the capture")
    (text,) = _pdf_text(output_dirpath)
    data = capture_filepath.read_bytes()
    assert b"\n" not in data
    assert b'   10 PRINT "HELLO"\r   20 GOTO 10\r' in data
    lines = [line.strip() for line in text.splitlines()]
    assert '10 PRINT "HELLO"' in lines
    assert "20 GOTO 10" in lines
    record = json.loads((output_dirpath / "job-0001" / "job.json").read_text())
    assert record["printer"] == {"model": "epson-fx80", "options": {"auto-line-feed": "yes"}}


SCREEN_DUMP_PROGRAM = [
    "10 MODE 4",
    "20 MOVE 0,1020:DRAW 508,1020:DRAW 508,768:DRAW 0,768:DRAW 0,1020:DRAW 508,768",
    "30 MOVE 256,1000:FOR A=0 TO 6.4 STEP .4:DRAW 256+100*SIN A,894+100*COS A:NEXT",
    "40 VDU 2,1,27,1,65,1,8",
    "50 FOR Y=1020 TO 768 STEP -32",
    "60 VDU 1,27,1,75,1,128,1,0",
    "70 FOR X=0 TO 508 STEP 4",
    "80 B=0:FOR P=0 TO 7:IF POINT(X,Y-P*4) B=B+2^(7-P)",
    "90 NEXT:VDU 1,B:NEXT",
    "100 VDU 1,13,1,10:NEXT",
    "110 VDU 1,27,1,64,1,12,3",
    f"120 PRINT {MARKER_EXPR}",
]


def test_bbc_basic_screen_dump_prints_as_fx80_bit_image(launch_bbc, papyrium):
    """A BASIC program reads the screen with POINT and prints it with ESC K."""
    port, output_dirpath = papyrium
    bbc = _bbc_printing_to(launch_bbc, port)
    for line in SCREEN_DUMP_PROGRAM:
        _type_line(bbc, line)
    bbc.system.set_speed_multiplier(0.0)
    _type_line(bbc, "RUN")
    _wait_until(lambda: MARKER in _screen(bbc), "the screen dump to finish", timeout=120.0)

    strip = 4 + 128 + 2
    data = _wait_for_capture(output_dirpath, 3 + 8 * strip + 3)
    assert data.startswith(b"\x1bA\x08")
    assert data.endswith(b"\x1b@\x0c")
    assert data.count(b"\x1bK\x80\x00") == 8
    assert len(data) == 3 + 8 * strip + 3
    # The box's top edge is solid along the first strip's top pin.
    first_strip = data[7 : 7 + 128]
    assert all(column & 0x80 for column in first_strip)

    page_filepath = output_dirpath / "job-0001" / "page-0001.png"
    _wait_until(page_filepath.exists, "the page to be ejected")
    from PIL import Image

    with Image.open(page_filepath) as image:
        assert [image.tobytes()] == _fx80_page_images(data)
