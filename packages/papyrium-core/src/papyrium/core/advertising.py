"""Advertising a printer on the network, so that senders can find it.

A printer is described in Papyrium's own terms, an :class:`Advertisement`
built from its name and UUID, its model's identity, the identities of the
languages it accepts and the endpoints its transport listens on. An
:class:`Advertiser` plug-in announces that by some discovery protocol, such
as multicast DNS, and knows that protocol's records; nothing else does.
"""

from __future__ import annotations

import logging
import uuid
from abc import abstractmethod
from collections.abc import Callable
from dataclasses import dataclass

from papyrium.core.language import LanguageIdentity
from papyrium.core.model import ModelIdentity, PrinterModel
from papyrium.core.transport import Endpoint
from papyrium.extension import Extension, create_extension, namespace_for

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Advertisement:
    """A printer, as announced to the network.

    *endpoints* are those the network can reach; there is at least one.
    *model* is None, and *languages* empty, for a printer capturing jobs
    with no printer model.
    """

    name: str
    printer_uuid: uuid.UUID
    model: ModelIdentity | None
    languages: tuple[LanguageIdentity, ...]
    endpoints: tuple[Endpoint, ...]

    def __post_init__(self) -> None:
        if not self.endpoints:
            raise ValueError("an advertisement needs an endpoint the network can reach")


class Advertiser(Extension):
    """Announces printers by a discovery protocol, such as multicast DNS.

    Concrete advertisers plug in on the ``papyrium.advertiser`` extension
    axis. An advertiser announces what its protocol can describe, logs
    what it announced, and leaves out, with a message, an endpoint whose
    protocol it cannot describe.
    """

    @classmethod
    def _kind(cls) -> str:
        return "advertiser"

    @abstractmethod
    async def start(self, advertisement: Advertisement) -> None:
        """Announce *advertisement* until :meth:`stop`."""

    @abstractmethod
    async def stop(self) -> None:
        """Withdraw what was announced; stopping before starting does nothing."""


def _installed_language_identity(name: str) -> LanguageIdentity:
    return create_extension("language", namespace_for("language"), name).identity()


class Advertising:
    """One printer's advertisement, made by *advertiser* while the printer runs.

    Advertising is best effort: a printer the network cannot reach is not
    announced, and a failure to announce is logged while the printer
    carries on printing.
    """

    def __init__(
        self,
        advertiser: Advertiser,
        *,
        name: str,
        printer_uuid: uuid.UUID,
        model: PrinterModel | None,
        language_identity: Callable[[str], LanguageIdentity] = _installed_language_identity,
    ) -> None:
        self._advertiser = advertiser
        self._name = name
        self._printer_uuid = printer_uuid
        self._model = model
        self._language_identity = language_identity
        self._started = False

    async def start(self, endpoints: tuple[Endpoint, ...]) -> None:
        """Announce the printer at those of *endpoints* the network can reach."""
        reachable = []
        for endpoint in endpoints:
            if endpoint.local_only:
                logger.warning(
                    "not advertising port %d: only this machine can reach it (%s)",
                    endpoint.port,
                    ", ".join(endpoint.addresses),
                )
            else:
                reachable.append(endpoint)
        if not reachable:
            logger.warning("not advertising %r: the network cannot reach it", self._name)
            return
        try:
            advertisement = Advertisement(
                name=self._name,
                printer_uuid=self._printer_uuid,
                model=None if self._model is None else self._model.identity(),
                languages=()
                if self._model is None
                else tuple(self._language_identity(n) for n in self._model.languages()),
                endpoints=tuple(reachable),
            )
            await self._advertiser.start(advertisement)
        except Exception as error:
            logger.warning("advertising failed: %s; the printer carries on", error)
            return
        self._started = True

    async def stop(self) -> None:
        """Withdraw the announcement, if there is one."""
        if not self._started:
            return
        self._started = False
        try:
            await self._advertiser.stop()
        except Exception as error:
            logger.warning("withdrawing the advertisement failed: %s", error)
