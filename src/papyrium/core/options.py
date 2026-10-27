"""Building an extension from string-valued options, as given on a command line."""

from __future__ import annotations

import inspect
from collections.abc import Mapping
from typing import Any

from papyrium.exception import ConfigurationError

_TRUE_WORDS = frozenset({"1", "true", "yes", "on"})
_FALSE_WORDS = frozenset({"0", "false", "no", "off"})


def _parse_flag(text: str) -> bool:
    word = text.strip().lower()
    if word in _TRUE_WORDS:
        return True
    if word in _FALSE_WORDS:
        return False
    raise ValueError(f"expected one of {', '.join(sorted(_TRUE_WORDS | _FALSE_WORDS))}")


def _convert(value: Any, default: Any) -> Any:
    """Convert a string *value* to the type of *default*; pass other values through."""
    if not isinstance(value, str) or default is inspect.Parameter.empty or default is None:
        return value
    if isinstance(default, bool):
        return _parse_flag(value)
    if isinstance(default, (int, float)):
        return type(default)(value)
    return value


def construct(cls: type, *, name: str, config: Mapping[str, Any]) -> Any:
    """Instantiate *cls* with keyword options taken from *config*.

    Keys may be hyphenated (``read-size``) and map to the keyword parameter
    with underscores. A string value is converted to the type of the
    parameter's default, so ``"9100"`` becomes 9100 for a parameter whose
    default is an int, and ``"yes"`` becomes True for a bool.

    Raises:
        ConfigurationError: An option is unknown or its value cannot be
            converted.
    """
    parameters = inspect.signature(cls).parameters
    kwargs: dict[str, Any] = {}
    for key, value in config.items():
        keyword = key.replace("-", "_")
        parameter = parameters.get(keyword)
        if parameter is None or keyword == "name" or parameter.kind is not parameter.KEYWORD_ONLY:
            known = sorted(
                p.replace("_", "-")
                for p, spec in parameters.items()
                if spec.kind is spec.KEYWORD_ONLY
            )
            raise ConfigurationError(
                f"{name!r} has no option {key!r}; options are: {', '.join(known) or 'none'}"
            )
        try:
            kwargs[keyword] = _convert(value, parameter.default)
        except ValueError as error:
            raise ConfigurationError(f"{name!r} option {key!r}: bad value {value!r}") from error
    return cls(name=name, **kwargs)
