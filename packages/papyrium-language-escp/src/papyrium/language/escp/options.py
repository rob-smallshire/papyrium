"""Parsing the options ESC/P printer models share: paper, character set and font."""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path
from typing import Any

from papyrium.core.dotfont import DotFont, FileDotFont
from papyrium.core.page import inches
from papyrium.core.stationery import STATIONERY
from papyrium.exception import ConfigurationError, DataError
from papyrium.extension import create_extension, namespace_for
from papyrium.language.escp.charsets import CharacterSet, parse_character_set

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


def nine_row_font(name: str) -> DotFont:
    """The installed dot font called *name*, or the dot font file at the path
    *name*, which must be nine rows high."""
    if name.endswith(".txt") or "/" in name or "\\" in name:
        try:
            font = FileDotFont(name=Path(name).stem, filepath=Path(name))
        except (OSError, DataError) as error:
            raise ConfigurationError(f"cannot read the font file {name}: {error}") from error
    else:
        font = create_extension("font", namespace_for("font"), name)
    if not isinstance(font, DotFont) or font.rows != 9:
        raise ConfigurationError(f"font {name!r} is not a 9-row dot font")
    return font


def paper_options(
    *, paper_width: str, form_length: str, top_offset: str, stationery: str
) -> dict[str, Any]:
    """EscpMechanism settings for the paper, with the 8-inch line centred across it."""
    width = inches_option("paper-width", paper_width)
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
    return {
        "paper_width": width,
        "sheet_length": length,
        "left_offset": max(0, (width - LINE_LENGTH) // 2),
        "top_offset": top,
        "stationery": STATIONERY[stationery],
    }
