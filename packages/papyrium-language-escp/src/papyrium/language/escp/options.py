"""Parsing the options ESC/P printer models share: paper, character set and font."""

from __future__ import annotations

import logging
from fractions import Fraction
from pathlib import Path
from typing import Any

from papyrium.core.dotfont import DotFont, FileDotFont
from papyrium.core.page import inches
from papyrium.core.stationery import STATIONERY, STRIP_WIDTH
from papyrium.exception import ConfigurationError, DataError
from papyrium.extension import create_extension, namespace_for
from papyrium.language.escp.charsets import CharacterSet, parse_character_set

logger = logging.getLogger(__name__)

#: The head's reach on an 80-column printer: 8 inches.
LINE_LENGTH = inches(8)


def inches_option(option: str, value: str) -> int:
    """*value*, a length in inches such as ``8.5`` or ``1/6``, in page units.

    Raises:
        ConfigurationError: *value* is not an exact length in inches.
    """
    try:
        return inches(Fraction(str(value)))
    except (ValueError, ZeroDivisionError) as error:
        raise ConfigurationError(f"{option} must be a length in inches, not {value!r}") from error


def character_set_option(value: str) -> CharacterSet:
    """The international character set named or numbered by *value*."""
    try:
        return parse_character_set(value)
    except (KeyError, ValueError) as error:
        raise ConfigurationError(f"unknown character set {value!r}") from error


def _dot_font(name: str) -> DotFont:
    """The installed dot font called *name*, or the dot font file at the path *name*."""
    if name.endswith(".txt") or "/" in name or "\\" in name:
        try:
            return FileDotFont(name=Path(name).stem, filepath=Path(name))
        except (OSError, DataError) as error:
            raise ConfigurationError(f"cannot read the font file {name}: {error}") from error
    font = create_extension("font", namespace_for("font"), name)
    if not isinstance(font, DotFont):
        raise ConfigurationError(f"{name!r} is not a dot font")
    return font


def nine_row_font(name: str) -> DotFont:
    """The dot font *name* (see :func:`_dot_font`), which must be nine rows high."""
    font = _dot_font(name)
    if font.rows != 9:
        raise ConfigurationError(f"font {name!r} is not a 9-row dot font")
    return font


def nlq_font(name: str) -> DotFont:
    """The near letter quality font *name*: 18 rows (two passes) by 24 columns."""
    font = _dot_font(name)
    if (font.rows, font.columns) != (18, 24):
        raise ConfigurationError(f"font {name!r} is not an 18 x 24 NLQ font")
    return font


def paper_options(
    *, paper_width: str | None, form_length: str, top_offset: str, stationery: str
) -> dict[str, Any]:
    """EscpMechanism settings for the paper, with the 8-inch line centred across it.

    Without a *paper_width*, the paper is as wide as the stationery usually
    is: 8.5 inches, and 9.5 with tear-off strips.
    """
    length = inches_option("form-length", form_length)
    top = inches_option("top-offset", top_offset)
    if not 0 <= top < length:
        raise ConfigurationError(
            f"top-offset must be at least 0 and less than the form length, not {top_offset!r}"
        )
    if stationery not in STATIONERY:
        raise ConfigurationError(
            f"unknown stationery {stationery!r}; choose from {', '.join(STATIONERY)}"
        )
    kind = STATIONERY[stationery]
    width = kind.paper_width if paper_width is None else inches_option("paper-width", paper_width)
    left_offset = max(0, (width - LINE_LENGTH) // 2)
    if kind.strips and left_offset < STRIP_WIDTH:
        logger.warning(
            "the line runs onto the tear-off strips of %s paper %s inches wide",
            stationery,
            paper_width,
        )
    return {
        "paper_width": width,
        "sheet_length": length,
        "left_offset": left_offset,
        "top_offset": top,
        "stationery": kind,
    }
