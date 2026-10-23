"""Plug-in axes as the CLI sees them: discovery, construction and options."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import click

from papyrium.exception import ConfigurationError
from papyrium.extension import extension, list_extensions, namespace_for


@dataclass(frozen=True)
class Axis:
    """An extension axis, with the words the CLI uses for it."""

    kind: str
    singular: str
    plural: str
    summary: str

    @property
    def namespace(self) -> str:
        return namespace_for(self.kind)

    def names(self) -> list[str]:
        return sorted(list_extensions(self.namespace))

    def create(self, name: str, options: Mapping[str, Any]):
        """Build the plug-in *name* from KEY=VALUE *options*."""
        if name not in self.names():
            raise ConfigurationError(
                f"no {self.singular} named {name!r}; installed {self.plural}: "
                f"{', '.join(self.names()) or 'none'}"
            )
        plugin_class = extension(self.kind, self.namespace, name)
        if hasattr(plugin_class, "from_config"):
            return plugin_class.from_config(name=name, config=options)
        if options:
            raise ConfigurationError(f"{self.singular} {name!r} takes no options")
        return plugin_class(name=name)


TRANSPORTS = Axis("transport", "transport", "transports", "Installed transport plug-ins.")
LANGUAGES = Axis("language", "language", "languages", "Installed printer languages.")
MODELS = Axis("model", "model", "models", "Installed printer models.")
FONTS = Axis("font", "font", "fonts", "Installed dot fonts.")
OUTPUTS = Axis("output", "output", "outputs", "Installed output plug-ins.")

AXES = (TRANSPORTS, LANGUAGES, MODELS, FONTS, OUTPUTS)


def parse_options(_ctx, _param, values: tuple[str, ...]) -> dict[str, str]:
    """A Click callback turning repeated KEY=VALUE options into a dict."""
    options = {}
    for value in values:
        key, separator, setting = value.partition("=")
        if not separator or not key.strip():
            raise click.BadParameter(f"expected KEY=VALUE, got {value!r}")
        options[key.strip()] = setting.strip()
    return options


def parse_output_options(_ctx, _param, values: tuple[str, ...]) -> dict[str, dict[str, str]]:
    """A Click callback turning repeated OUTPUT.KEY=VALUE options into dicts per output."""
    options: dict[str, dict[str, str]] = {}
    for value in values:
        target, separator, setting = value.partition("=")
        output_name, dot, key = target.partition(".")
        if not separator or not dot or not output_name.strip() or not key.strip():
            raise click.BadParameter(f"expected OUTPUT.KEY=VALUE, got {value!r}")
        options.setdefault(output_name.strip(), {})[key.strip()] = setting.strip()
    return options


def create_outputs(names: tuple[str, ...], options: dict[str, dict[str, str]]) -> list:
    """Build the named outputs, each with its own options."""
    unused = set(options) - set(names)
    if unused:
        raise ConfigurationError(
            f"options given for outputs not selected: {', '.join(sorted(unused))}"
        )
    return [OUTPUTS.create(name, options.get(name, {})) for name in names]
