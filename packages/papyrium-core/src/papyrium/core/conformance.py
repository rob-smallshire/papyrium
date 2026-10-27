"""Reusable conformance suites, one for each extension axis.

Subclass the suite for an axis in a plug-in package's test suite, for
example :class:`TransportConformance`, implement its ``make_...`` methods
(and :meth:`~TransportConformance.connect` for a transport), and pytest runs
the inherited contract checks against your plug-in.

This module deliberately imports no test framework, so it is safe to import
anywhere; the concrete subclass lives in a test module that pytest collects.
"""

from __future__ import annotations

import asyncio
from typing import Protocol

from papyrium.core.transport import Transport

#: How long a check waits for bytes before deciding they are not coming.
TIMEOUT_SECONDS = 2.0

#: How long a check waits to be confident that nothing more is coming.
QUIET_SECONDS = 0.1


class Connection(Protocol):
    """One connection from a sender to the transport under test."""

    async def send(self, data: bytes) -> None:
        """Send *data* to the transport."""

    async def disconnect(self) -> None:
        """End this connection."""


async def receive(transport: Transport, count: int) -> bytes:
    """Pull chunks from *transport* until *count* bytes have arrived."""
    received = bytearray()
    iterator = aiter(transport)
    while len(received) < count:
        received += await asyncio.wait_for(anext(iterator), TIMEOUT_SECONDS)
    return bytes(received)


class TransportConformance:
    """The contract every :class:`Transport` implementation must satisfy."""

    def make_transport(self) -> Transport:
        """Return a fresh, unopened transport to exercise. Override this."""
        raise NotImplementedError

    async def connect(self, transport: Transport) -> Connection:
        """Open a new connection to the opened *transport*. Override this."""
        raise NotImplementedError

    def test_kind_is_transport(self):
        assert type(self.make_transport()).kind() == "transport"

    async def test_context_manager_yields_self(self):
        transport = self.make_transport()
        async with transport as entered:
            assert entered is transport

    async def test_bytes_arrive_in_order(self):
        data = bytes(range(256)) * 4
        async with self.make_transport() as transport:
            connection = await self.connect(transport)
            await connection.send(data[:300])
            await connection.send(data[300:])
            assert await receive(transport, len(data)) == data
            await connection.disconnect()

    async def test_chunks_are_non_empty_bytes(self):
        async with self.make_transport() as transport:
            connection = await self.connect(transport)
            await connection.send(b"HELLO")
            chunk = await asyncio.wait_for(anext(aiter(transport)), TIMEOUT_SECONDS)
            assert isinstance(chunk, bytes)
            assert chunk
            await connection.disconnect()

    async def test_disconnect_does_not_end_the_stream(self):
        async with self.make_transport() as transport:
            first = await self.connect(transport)
            await first.send(b"ONE")
            await first.disconnect()
            assert await receive(transport, 3) == b"ONE"
            second = await self.connect(transport)
            await second.send(b"TWO")
            await second.disconnect()
            assert await receive(transport, 3) == b"TWO"

    async def test_iteration_waits_for_bytes_after_disconnect(self):
        async with self.make_transport() as transport:
            connection = await self.connect(transport)
            await connection.send(b"X")
            await connection.disconnect()
            assert await receive(transport, 1) == b"X"
            try:
                await asyncio.wait_for(anext(aiter(transport)), QUIET_SECONDS)
            except TimeoutError:
                pass
            else:
                raise AssertionError("iteration produced data or ended after a disconnect")

    async def test_endpoints_are_where_it_listens_once_open(self):
        from papyrium.core.transport import Endpoint

        async with self.make_transport() as transport:
            endpoints = transport.endpoints()
            assert isinstance(endpoints, tuple)
            assert all(isinstance(endpoint, Endpoint) for endpoint in endpoints)

    async def test_iteration_ends_after_close(self):
        transport = self.make_transport()
        async with transport:
            pass
        received = [chunk async for chunk in transport]
        assert received == []


def _sample_pages():
    from papyrium.core.page import Page

    return [
        Page(number=1, width=4320, height=4320, dot_diameter=60, dots=((300, 300), (420, 300))),
        Page(number=2, width=4320, height=4320, dot_diameter=60, dots=((2160, 2160),)),
    ]


class OutputConformance:
    """The contract every :class:`~papyrium.core.output.Output` must satisfy.

    The checks take a pytest ``tmp_path`` argument, so subclasses must be
    collected by pytest.
    """

    def make_output(self):
        """Return a fresh output to exercise. Override this."""
        raise NotImplementedError

    def _render(self, dirpath, pages):
        dirpath.mkdir(parents=True, exist_ok=True)
        document = self.make_output().open_document(dirpath)
        for page in pages:
            document.add_page(page)
        return document.close()

    def test_kind_is_output(self):
        assert type(self.make_output()).kind() == "output"

    def test_writes_files_inside_the_job_directory(self, tmp_path):
        filepaths = self._render(tmp_path, _sample_pages())
        assert filepaths
        for filepath in filepaths:
            assert filepath.parent == tmp_path
            assert filepath.is_file()
            assert filepath.stat().st_size > 0

    def test_no_pages_writes_no_files(self, tmp_path):
        assert self._render(tmp_path, []) == []
        assert list(tmp_path.iterdir()) == []

    def test_same_pages_give_identical_files(self, tmp_path):
        first = self._render(tmp_path / "first", _sample_pages())
        second = self._render(tmp_path / "second", _sample_pages())
        assert [path.name for path in first] == [path.name for path in second]
        for first_filepath, second_filepath in zip(first, second):
            assert first_filepath.read_bytes() == second_filepath.read_bytes()


class PrinterModelConformance:
    """The contract every :class:`~papyrium.core.model.PrinterModel` must satisfy."""

    def make_model(self):
        """Return a model to exercise. Override this."""
        raise NotImplementedError

    def sample_job(self) -> bytes:
        """Return bytes that print at least two pages. Override this."""
        raise NotImplementedError

    def _pages(self, chunks):
        interpreter = self.make_model().create_interpreter()
        pages = []
        for chunk in chunks:
            pages.extend(interpreter.feed(chunk))
        pages.extend(interpreter.finish())
        return pages

    def test_kind_is_model(self):
        assert type(self.make_model()).kind() == "model"

    def test_sample_job_prints_pages(self):
        pages = self._pages([self.sample_job()])
        assert len(pages) >= 2
        assert any(not page.is_blank for page in pages)

    def test_pages_are_numbered_from_one(self):
        pages = self._pages([self.sample_job()])
        assert [page.number for page in pages] == list(range(1, len(pages) + 1))

    def test_pages_do_not_depend_on_chunking(self):
        data = self.sample_job()
        whole = self._pages([data])
        bytewise = self._pages([data[i : i + 1] for i in range(len(data))])
        assert whole == bytewise

    def test_interpreters_start_afresh(self):
        assert self._pages([self.sample_job()]) == self._pages([self.sample_job()])

    def test_no_bytes_print_no_pages(self):
        assert self._pages([]) == []

    def test_has_an_identity(self):
        from papyrium.core.model import ModelIdentity

        assert isinstance(self.make_model().identity(), ModelIdentity)

    def test_names_only_installed_languages(self):
        from papyrium.extension import list_extensions, namespace_for

        installed = set(list_extensions(namespace_for("language")))
        languages = self.make_model().languages()
        assert isinstance(languages, tuple)
        assert set(languages) <= installed, sorted(set(languages) - installed)

    def test_demo_prints_a_page_without_warnings(self, caplog):
        import logging

        demo = self.make_model().demo()
        assert isinstance(demo, bytes) and demo
        with caplog.at_level(logging.WARNING):
            pages = self._pages([demo])
        assert pages and any(not page.is_blank for page in pages)
        assert not [record for record in caplog.records if record.levelno >= logging.WARNING]

    def test_dots_lie_on_the_page(self):
        for page in self._pages([self.sample_job()]):
            for x, y in page.all_dots():
                assert 0 <= x < page.width and 0 <= y < page.height, (page.number, x, y)


class LanguageConformance:
    """The contract every :class:`~papyrium.core.language.Language` must satisfy."""

    def make_language(self):
        """Return the language to exercise. Override this."""
        raise NotImplementedError

    def test_kind_is_language(self):
        assert type(self.make_language()).kind() == "language"

    def test_has_an_identity(self):
        from papyrium.core.language import LanguageIdentity

        assert isinstance(self.make_language().identity(), LanguageIdentity)


def sample_advertisement():
    """An advertisement for a printer on port 9100 of every interface."""
    import uuid

    from papyrium.core.advertising import Advertisement
    from papyrium.core.language import LanguageIdentity
    from papyrium.core.model import ModelIdentity
    from papyrium.core.transport import Endpoint

    return Advertisement(
        name="Conformance Printer (Papyrium)",
        printer_uuid=uuid.UUID("00000000-0000-4000-8000-000000000001"),
        model=ModelIdentity(manufacturer="Epson", model="FX-80"),
        languages=(LanguageIdentity(name="ESC/P", command_set="ESCP9"),),
        endpoints=(Endpoint(protocol="appsocket", port=9100, addresses=("0.0.0.0",)),),
    )


class AdvertiserConformance:
    """The contract every :class:`~papyrium.core.advertising.Advertiser` must satisfy."""

    def make_advertiser(self):
        """Return a fresh advertiser to exercise. Override this."""
        raise NotImplementedError

    def test_kind_is_advertiser(self):
        assert type(self.make_advertiser()).kind() == "advertiser"

    async def test_starts_and_stops(self):
        advertiser = self.make_advertiser()
        await advertiser.start(sample_advertisement())
        await advertiser.stop()

    async def test_stop_before_start_does_nothing(self):
        await self.make_advertiser().stop()


#: The printable ASCII characters every dot font must cover.
PRINTABLE_ASCII = frozenset(chr(code) for code in range(0x20, 0x7F))


class DotFontConformance:
    """The contract every :class:`~papyrium.core.dotfont.DotFont` must satisfy.

    Set :attr:`allows_adjacent_dots` to True in a subclass for a font made
    for a head that can strike a pin in successive columns.
    """

    allows_adjacent_dots = False

    def make_font(self):
        """Return the font to exercise. Override this."""
        raise NotImplementedError

    def test_kind_is_font(self):
        assert type(self.make_font()).kind() == "font"

    def test_covers_printable_ascii(self):
        missing = PRINTABLE_ASCII - self.make_font().characters()
        assert not missing, sorted(missing)

    def test_dots_lie_within_the_matrix(self):
        font = self.make_font()
        for character in font.characters():
            for column, row in font.glyph(character).dots:
                assert 0 <= column < font.columns and 0 <= row < font.rows, character

    def test_no_horizontally_adjacent_dots(self):
        if self.allows_adjacent_dots:
            return
        font = self.make_font()
        offenders = [c for c in font.characters() if font.glyph(c).has_adjacent_dots]
        assert not offenders, sorted(offenders)

    def test_space_is_blank(self):
        assert not self.make_font().glyph(" ").dots
