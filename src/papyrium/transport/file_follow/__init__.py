"""File-follow transport: the bytes an emulator appends to a printer file."""

from __future__ import annotations

import asyncio
import contextlib
import logging
import os
from collections.abc import AsyncIterator
from pathlib import Path

from papyrium.core.channel import ChunkChannel
from papyrium.core.transport import Transport
from papyrium.exception import ConfigurationError

__all__ = ["FileFollowTransport", "DEFAULT_POLL_INTERVAL"]

logger = logging.getLogger(__name__)

#: Seconds between looks at the file.
DEFAULT_POLL_INTERVAL = 0.1

_READ_SIZE = 4096

#: How much of the file's start is kept, to notice the file written afresh in place.
_HEAD_SIZE = 64


class FileFollowTransport(Transport):
    """Follows a file as a sender writes to it, as ``tail -f`` does.

    Stands in for a printer cable where an emulator prints to a file: it
    looks at the file every ``poll-interval`` seconds and delivers the
    bytes added since it last looked. Nothing is written to the file.

    By default it starts at the file's end, because such a file usually
    holds earlier sessions' printing; ``from-start`` reads what the file
    already holds first. A file that does not exist yet is waited for, and
    read from its start when it appears.

    A file that is truncated, replaced (deleted and created again, or
    renamed over), or written afresh in place (its first bytes change) is
    read again from its start. A file written afresh with the same first
    bytes and grown beyond its old length between two looks cannot be told
    from one appended to.

    The file gives no backpressure: a sender writing to it never waits.

    Options: ``filepath`` (required), ``from-start`` (default no),
    ``poll-interval`` (seconds, default 0.1).
    """

    def __init__(
        self,
        name: str,
        *,
        filepath: str = "",
        from_start: bool = False,
        poll_interval: float = DEFAULT_POLL_INTERVAL,
        capacity: int = 16,
        **kwargs,
    ) -> None:
        super().__init__(name=name, **kwargs)
        if not filepath:
            raise ConfigurationError(f"{name!r} needs a file to follow: give its filepath option")
        if poll_interval <= 0:
            raise ConfigurationError(
                f"{name!r} option 'poll-interval' must be positive, not {poll_interval}"
            )
        self._filepath = Path(filepath).expanduser()
        self._from_start = from_start
        self._poll_interval = poll_interval
        self._channel = ChunkChannel(capacity)
        self._follower: asyncio.Task | None = None
        self._identity: tuple[int, int] | None = None
        self._offset = 0
        self._head = b""
        self._failure: str | None = None

    @property
    def filepath(self) -> Path:
        return self._filepath

    @property
    def from_start(self) -> bool:
        return self._from_start

    @property
    def poll_interval(self) -> float:
        return self._poll_interval

    async def open(self) -> None:
        self._begin()
        self._follower = asyncio.create_task(self._follow())

    async def close(self) -> None:
        if self._follower is not None:
            self._follower.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._follower
            self._follower = None
        self._channel.close()

    def __aiter__(self) -> AsyncIterator[bytes]:
        return self._channel

    def _begin(self) -> None:
        """Take the file as it stands: skip what it holds, unless reading from the start."""
        try:
            status = os.stat(self._filepath)
        except FileNotFoundError:
            logger.info("waiting for %s to appear", self._filepath)
            return
        self._identity = _identity(status)
        if self._from_start:
            logger.info("following %s from its start", self._filepath)
            return
        with open(self._filepath, "rb") as file:
            self._head = file.read(_HEAD_SIZE)
        self._offset = status.st_size
        logger.info("following %s from its end, at byte %d", self._filepath, self._offset)

    async def _follow(self) -> None:
        while True:
            try:
                await self._look()
            except OSError as error:
                self._report_failure(f"cannot read {self._filepath}: {error}")
            else:
                self._failure = None
            await asyncio.sleep(self._poll_interval)

    async def _look(self) -> None:
        """Deliver whatever the file has gained since the last look."""
        try:
            status = os.stat(self._filepath)
        except FileNotFoundError:
            if self._identity is not None:
                logger.info("%s has gone; waiting for it to appear again", self._filepath)
                self._identity = None
                self._restart()
            return
        identity = _identity(status)
        if self._identity is not None and identity != self._identity:
            logger.info("%s was replaced; reading it from its start", self._filepath)
            self._restart()
        elif status.st_size < self._offset:
            logger.info("%s was truncated; reading it from its start", self._filepath)
            self._restart()
        self._identity = identity
        if status.st_size == self._offset:
            return
        with open(self._filepath, "rb") as file:
            if self._head and file.read(len(self._head)) != self._head:
                logger.info("%s was written afresh; reading it from its start", self._filepath)
                self._restart()
            file.seek(self._offset)
            while chunk := file.read(_READ_SIZE):
                self._remember_head(chunk)
                self._offset += len(chunk)
                await self._channel.send(chunk)

    def _restart(self) -> None:
        self._offset = 0
        self._head = b""

    def _remember_head(self, chunk: bytes) -> None:
        # The head is the file's first bytes, so it grows only while the
        # offset is still within it.
        if self._offset == len(self._head) < _HEAD_SIZE:
            self._head += chunk[: _HEAD_SIZE - len(self._head)]

    def _report_failure(self, message: str) -> None:
        # Logged once each time the failure changes, not at every look.
        if message != self._failure:
            logger.warning("%s; trying again", message)
            self._failure = message


def _identity(status: os.stat_result) -> tuple[int, int]:
    return (status.st_dev, status.st_ino)
