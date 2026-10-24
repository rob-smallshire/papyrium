"""Dot fonts: character glyphs as dot matrices, kept as swappable data.

A dot font is a text file::

    # Comments start with a hash.
    rows 9
    columns 11

    U+0041 LATIN CAPITAL LETTER A
    .....#.....
    ...

Each glyph starts with its Unicode code point (anything after it on the line
is a comment) and continues with exactly ``rows`` lines of ``columns``
characters, ``#`` for a dot and ``.`` for none. Row 0 is the top pin.
Comment and blank lines may appear between glyphs, not within one.

A variant of a character is named by a sequence of code points, the
character and a combining mark: ``U+0030 U+0338`` is a slashed zero.
"""

from __future__ import annotations

import importlib.resources
import re
from abc import abstractmethod
from dataclasses import dataclass, field

from papyrium.exception import DataError
from papyrium.extension import Extension

_CODE_POINTS_PATTERN = re.compile(r"^U\+[0-9A-Fa-f]{4,6}(?:\s+U\+[0-9A-Fa-f]{4,6})*\b")


def code_points(character: str) -> str:
    """*character*, which may be a sequence, in U+ notation."""
    return " ".join(f"U+{ord(c):04X}" for c in character)


@dataclass(frozen=True)
class Glyph:
    """A character's dots as (column, row) pairs."""

    dots: frozenset[tuple[int, int]]

    @property
    def leftmost(self) -> int | None:
        return min((column for column, _ in self.dots), default=None)

    @property
    def rightmost(self) -> int | None:
        return max((column for column, _ in self.dots), default=None)

    @property
    def has_adjacent_dots(self) -> bool:
        """True if any two dots in a row are in neighbouring columns.

        A 9-pin head cannot strike the same pin in successive columns, so its
        fonts never have them.
        """
        return any((column + 1, row) in self.dots for column, row in self.dots)


@dataclass(frozen=True)
class DotFontData:
    """A parsed dot font."""

    rows: int
    columns: int
    glyphs: dict[str, Glyph] = field(default_factory=dict)


def parse_dot_font(text: str) -> DotFontData:
    """Parse the dot font text format.

    Raises:
        DataError: The text is not a well-formed dot font.
    """
    settings: dict[str, int] = {}
    glyphs: dict[str, Glyph] = {}
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        number, line = index + 1, lines[index].rstrip()
        index += 1
        if not line or line.startswith("#"):
            continue
        words = line.split()
        if words[0] in ("rows", "columns") and len(words) == 2 and words[1].isdigit():
            settings[words[0]] = int(words[1])
            continue
        match = _CODE_POINTS_PATTERN.match(line)
        if match is None:
            raise DataError(f"line {number}: expected a setting or a code point, got {line!r}")
        if "rows" not in settings or "columns" not in settings:
            raise DataError(f"line {number}: rows and columns must be set before any glyph")
        character = "".join(chr(int(word[2:], 16)) for word in match.group().split())
        if character in glyphs:
            raise DataError(f"line {number}: {code_points(character)} is defined twice")
        rows, columns = settings["rows"], settings["columns"]
        bitmap = [line.rstrip() for line in lines[index : index + rows]]
        if len(bitmap) != rows:
            raise DataError(f"line {number}: {code_points(character)} needs {rows} rows")
        dots = set()
        for row, bitmap_line in enumerate(bitmap):
            bitmap_number = index + row + 1
            if len(bitmap_line) != columns:
                raise DataError(f"line {bitmap_number}: expected {columns} columns")
            for column, cell in enumerate(bitmap_line):
                if cell == "#":
                    dots.add((column, row))
                elif cell != ".":
                    raise DataError(f"line {bitmap_number}: unexpected {cell!r}")
        index += rows
        glyphs[character] = Glyph(frozenset(dots))
    if "rows" not in settings or "columns" not in settings:
        raise DataError("a dot font must set rows and columns")
    return DotFontData(rows=settings["rows"], columns=settings["columns"], glyphs=glyphs)


class DotFont(Extension):
    """A character set's glyphs as dot matrices, for a dot-matrix printer model.

    Concrete fonts plug in on the ``papyrium.font`` extension axis, so a
    model's character ROM can be swapped for another design.
    """

    @classmethod
    def _kind(cls) -> str:
        return "font"

    @property
    @abstractmethod
    def rows(self) -> int:
        """Dot rows per glyph, row 0 at the top."""

    @property
    @abstractmethod
    def columns(self) -> int:
        """Dot columns per glyph."""

    @abstractmethod
    def glyph(self, character: str) -> Glyph | None:
        """The glyph for *character*, or None if the font has none.

        *character* may be a sequence naming a variant, such as a slashed zero.
        """

    @abstractmethod
    def characters(self) -> frozenset[str]:
        """Every character the font has a glyph for."""


class DataDotFont(DotFont):
    """A dot font read from a text file shipped in its package.

    Subclasses set :attr:`font_filename`, the file's name within the
    subclass's package.
    """

    font_filename: str = "glyphs.txt"

    def __init__(self, name: str, **kwargs) -> None:
        super().__init__(name=name, **kwargs)
        package = type(self).__module__
        text = importlib.resources.files(package).joinpath(self.font_filename).read_text("ascii")
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
