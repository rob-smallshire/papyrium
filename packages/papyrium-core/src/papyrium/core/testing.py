"""In-process doubles for each extension axis, for testing without real plug-ins."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from pathlib import Path

from papyrium.core.channel import ChunkChannel
from papyrium.core.dotfont import DotFont, Glyph, parse_dot_font
from papyrium.core.model import Interpreter, PrinterModel
from papyrium.core.output import Document, Output
from papyrium.core.page import Page
from papyrium.core.transport import Transport


class MemoryConnection:
    """One connection into a :class:`MemoryTransport`."""

    def __init__(self, channel: ChunkChannel) -> None:
        self._channel = channel

    async def send(self, data: bytes) -> None:
        await self._channel.send(data)

    async def disconnect(self) -> None:
        """End this connection; the transport's stream carries on."""


class MemoryTransport(Transport):
    """An in-process transport for testing readers without sockets.

    Open connections with :meth:`connect` and send bytes through them, or
    :meth:`feed` bytes as a single short-lived connection.
    """

    def __init__(self, name: str, *, capacity: int = 16, **kwargs) -> None:
        super().__init__(name=name, **kwargs)
        self._channel = ChunkChannel(capacity)

    async def open(self) -> None:
        pass

    async def close(self) -> None:
        self._channel.close()

    def connect(self) -> MemoryConnection:
        """Open a new connection to this transport."""
        return MemoryConnection(self._channel)

    async def feed(self, data: bytes) -> None:
        """Send *data* over a new connection, then disconnect it."""
        connection = self.connect()
        await connection.send(data)
        await connection.disconnect()

    def __aiter__(self) -> AsyncIterator[bytes]:
        return self._channel


class _ByteDotInterpreter(Interpreter):
    def __init__(self, width: int, height: int) -> None:
        self._width = width
        self._height = height
        self._dots: list[tuple[int, int]] = []
        self._page_number = 0

    def feed(self, data: bytes) -> list[Page]:
        pages = []
        for byte in data:
            if byte == 0x0C:
                pages.append(self._eject())
            else:
                self._dots.append((byte % self._width, len(self._dots) % self._height))
        return pages

    def finish(self) -> list[Page]:
        return [self._eject()] if self._dots else []

    def _eject(self) -> Page:
        self._page_number += 1
        page = Page(
            number=self._page_number,
            width=self._width,
            height=self._height,
            dot_diameter=1,
            dots=tuple(self._dots),
        )
        self._dots = []
        return page


class ByteDotModel(PrinterModel):
    """A toy printer: one dot per byte, and a form feed ends the page."""

    def __init__(self, name: str, *, width: int = 256, height: int = 64, **kwargs) -> None:
        super().__init__(name=name, **kwargs)
        self._width = width
        self._height = height

    def create_interpreter(self) -> Interpreter:
        return _ByteDotInterpreter(self._width, self._height)


class _JsonDocument(Document):
    def __init__(self, dirpath: Path, filename: str, documents: list) -> None:
        self._filepath = dirpath / filename
        self._pages: list[Page] = []
        documents.append(self._pages)

    def add_page(self, page: Page) -> None:
        self._pages.append(page)

    def close(self) -> list[Path]:
        if not self._pages:
            return []
        description = [
            {
                "number": page.number,
                "width": page.width,
                "height": page.height,
                "dots": [list(dot) for dot in page.dots],
            }
            for page in self._pages
        ]
        self._filepath.write_text(json.dumps(description, sort_keys=True) + "\n")
        return [self._filepath]


class JsonOutput(Output):
    """Writes a job's pages as JSON, and keeps them in :attr:`documents` for inspection."""

    def __init__(self, name: str, *, filename: str = "pages.json", **kwargs) -> None:
        super().__init__(name=name, **kwargs)
        self._filename = filename
        self.documents: list[list[Page]] = []

    def open_document(self, dirpath: Path) -> Document:
        return _JsonDocument(dirpath, self._filename, self.documents)


class MemoryDotFont(DotFont):
    """A dot font built from text in the dot font format, for exact tests."""

    def __init__(self, name: str, *, text: str, **kwargs) -> None:
        super().__init__(name=name, **kwargs)
        self._data = parse_dot_font(text)

    @property
    def rows(self) -> int:
        return self._data.rows

    @property
    def columns(self) -> int:
        return self._data.columns

    def glyph(self, character: str) -> Glyph | None:
        return self._data.glyphs.get(character)

    def characters(self) -> frozenset[str]:
        return frozenset(self._data.glyphs)
