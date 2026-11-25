"""FileFollowTransport, following real files that a sender appends to."""

import asyncio
import os

import pytest

from papyrium.core.conformance import QUIET_SECONDS, TransportConformance, receive
from papyrium.exception import ConfigurationError
from papyrium.extension import create_extension, namespace_for
from papyrium.transport.file_follow import FileFollowTransport

_POLL_SECONDS = 0.01


class _Appender:
    """A sender that appends to the followed file, as BeebEm and B-em do."""

    def __init__(self, filepath):
        self._file = open(filepath, "ab")

    async def send(self, data):
        self._file.write(data)
        self._file.flush()

    async def disconnect(self):
        self._file.close()


async def _append(filepath, data):
    appender = _Appender(filepath)
    await appender.send(data)
    await appender.disconnect()


def _make_transport(filepath, **options):
    options = {"poll_interval": _POLL_SECONDS, **options}
    return FileFollowTransport(name="file-follow", filepath=str(filepath), **options)


async def _assert_nothing_arrives(transport):
    try:
        chunk = await asyncio.wait_for(anext(aiter(transport)), QUIET_SECONDS)
    except TimeoutError:
        return
    raise AssertionError(f"expected no bytes, received {chunk!r}")


class TestFileFollowConformance(TransportConformance):
    @pytest.fixture(autouse=True)
    def _followed_filepath(self, tmp_path):
        self._filepath = tmp_path / "printer.prn"

    def make_transport(self):
        return _make_transport(self._filepath)

    async def connect(self, transport):
        return _Appender(self._filepath)


def test_is_registered_on_the_transport_axis(tmp_path):
    transport = create_extension(
        "transport", namespace_for("transport"), "file-follow", filepath=str(tmp_path / "p.prn")
    )
    assert isinstance(transport, FileFollowTransport)


def test_needs_a_file_to_follow():
    with pytest.raises(ConfigurationError, match="filepath"):
        FileFollowTransport.from_config(name="file-follow", config={})


def test_takes_its_options_as_strings(tmp_path):
    transport = FileFollowTransport.from_config(
        name="file-follow",
        config={"filepath": str(tmp_path / "p.prn"), "from-start": "yes", "poll-interval": "0.5"},
    )
    assert transport.filepath == tmp_path / "p.prn"
    assert transport.from_start
    assert transport.poll_interval == 0.5


def test_rejects_a_poll_interval_that_is_not_positive(tmp_path):
    with pytest.raises(ConfigurationError, match="poll-interval"):
        FileFollowTransport(name="file-follow", filepath=str(tmp_path / "p.prn"), poll_interval=0)


async def test_skips_what_the_file_held_before_it_opened(tmp_path):
    filepath = tmp_path / "printer.prn"
    filepath.write_bytes(b"EARLIER SESSION")
    async with _make_transport(filepath) as transport:
        await _assert_nothing_arrives(transport)
        await _append(filepath, b"NEW")
        assert await receive(transport, 3) == b"NEW"


async def test_reads_what_the_file_held_from_the_start_when_asked(tmp_path):
    filepath = tmp_path / "printer.prn"
    filepath.write_bytes(b"EARLIER")
    async with _make_transport(filepath, from_start=True) as transport:
        assert await receive(transport, 7) == b"EARLIER"


async def test_waits_for_the_file_to_appear_and_reads_it_all(tmp_path):
    filepath = tmp_path / "printer.prn"
    async with _make_transport(filepath) as transport:
        await _assert_nothing_arrives(transport)
        filepath.write_bytes(b"FIRST BYTES")
        assert await receive(transport, 11) == b"FIRST BYTES"


async def test_reads_a_truncated_file_from_the_start(tmp_path):
    filepath = tmp_path / "printer.prn"
    async with _make_transport(filepath) as transport:
        await _append(filepath, b"A LONG FIRST RUN")
        assert await receive(transport, 16) == b"A LONG FIRST RUN"
        with open(filepath, "r+b") as rewriter:
            rewriter.truncate(0)
            rewriter.write(b"SHORT")
        assert await receive(transport, 5) == b"SHORT"


async def test_reads_a_file_rewritten_in_place_from_the_start(tmp_path):
    # As beebjit does: truncated and written again, beyond the old length,
    # between two looks at the file.
    filepath = tmp_path / "printer.prn"
    async with _make_transport(filepath, poll_interval=0.2) as transport:
        await _append(filepath, b"RUN ONE")
        assert await receive(transport, 7) == b"RUN ONE"
        with open(filepath, "wb") as rewriter:
            rewriter.write(b"SECOND RUN, LONGER")
        assert await receive(transport, 18) == b"SECOND RUN, LONGER"


async def test_reads_a_replaced_file_from_the_start(tmp_path):
    filepath = tmp_path / "printer.prn"
    async with _make_transport(filepath) as transport:
        await _append(filepath, b"OLD")
        assert await receive(transport, 3) == b"OLD"
        replacement = tmp_path / "replacement.prn"
        replacement.write_bytes(b"OLDER THAN IT LOOKS")
        os.replace(replacement, filepath)
        assert await receive(transport, 19) == b"OLDER THAN IT LOOKS"


async def test_waits_after_the_file_is_deleted(tmp_path):
    filepath = tmp_path / "printer.prn"
    async with _make_transport(filepath) as transport:
        await _append(filepath, b"GONE")
        assert await receive(transport, 4) == b"GONE"
        filepath.unlink()
        await _assert_nothing_arrives(transport)
        filepath.write_bytes(b"BACK")
        assert await receive(transport, 4) == b"BACK"


async def test_delivers_a_large_burst_whole(tmp_path):
    filepath = tmp_path / "printer.prn"
    data = bytes(range(256)) * 1024
    async with _make_transport(filepath) as transport:
        await _append(filepath, data)
        assert await receive(transport, len(data)) == data


def test_has_no_endpoints(tmp_path):
    assert _make_transport(tmp_path / "p.prn").endpoints() == ()


def test_expands_a_home_directory_in_its_filepath(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    transport = FileFollowTransport(name="file-follow", filepath="~/printer.prn")
    assert transport.filepath == tmp_path / "printer.prn"
