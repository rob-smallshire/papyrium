"""The page model: what a printer put on each sheet, independent of any output.

Positions and sizes are whole numbers of *units*, 1/4320 inch, measured from
the page's top-left corner with y increasing down the page. The unit divides
exactly into every step the impact printers Papyrium models can make: FX-80
graphics densities (1/60 to 1/240 inch), line feeds in 1/72 and 1/216 inch,
condensed columns (7/1440 inch) and Diablo 630 steps (1/120 and 1/48 inch).
So the same bytes always give the same marks, with no rounding.

A page holds *dots*, each a single strike of one pin, all of one diameter,
in black, and, from a colour ribbon, *ink dots*, struck through a band of
cyan, magenta or yellow ink; a mixed colour is the same dot struck through
two bands. It also holds *text*: which character was printed in which cell, so outputs can make
the page searchable and tests can compare content. Glyph and path marks,
for daisywheels and plotters, join the model when those printers do.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from fractions import Fraction
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from papyrium.core.stationery import Stationery

#: Page units per inch.
UNITS_PER_INCH = 4320

Dot = tuple[int, int]


class Ink(enum.Enum):
    """A coloured band of a ribbon, through which a pin strikes a dot."""

    CYAN = "cyan"
    MAGENTA = "magenta"
    YELLOW = "yellow"


#: The colour of each ink on white paper, as RGB, for outputs to draw with.
INK_COLOURS: dict[Ink, tuple[int, int, int]] = {
    Ink.CYAN: (0, 160, 228),
    Ink.MAGENTA: (228, 0, 124),
    Ink.YELLOW: (255, 232, 0),
}


@dataclass(frozen=True)
class InkDots:
    """The dots struck through one band of ink, in the order they were struck."""

    ink: Ink
    dots: tuple[Dot, ...]


@dataclass(frozen=True)
class TextMark:
    """A character printed in a cell: the cell's top-left corner and size.

    Text marks describe content; the dots are what is visible.
    """

    x: int
    y: int
    width: int
    height: int
    character: str


def units_from_fraction(length_inches: Fraction | int) -> int:
    """Convert an exact length in inches to units.

    Raises:
        ValueError: The length is not a whole number of units.
    """
    units = Fraction(length_inches) * UNITS_PER_INCH
    if units.denominator != 1:
        raise ValueError(f"{length_inches} inch is not a whole number of page units")
    return int(units)


def inches(length_inches: Fraction | int) -> int:
    """Units in *length_inches*, which must be exact; see :func:`units_from_fraction`."""
    return units_from_fraction(length_inches)


@dataclass(frozen=True)
class Page:
    """One sheet of output: its size and the marks printed on it.

    *number* counts pages within a job from 1. *dots* are the centres of the
    black dots struck, in the order they were struck, each *dot_diameter*
    units across, and *ink_dots* those struck through coloured bands.
    *text* records the characters printed, in printing order.
    *stationery* is the kind of paper, which outputs draw under the marks;
    None for a blank sheet.
    """

    number: int
    width: int
    height: int
    dot_diameter: int
    dots: tuple[Dot, ...] = ()
    ink_dots: tuple[InkDots, ...] = ()
    text: tuple[TextMark, ...] = ()
    stationery: Stationery | None = None

    @property
    def width_inches(self) -> Fraction:
        return Fraction(self.width, UNITS_PER_INCH)

    @property
    def height_inches(self) -> Fraction:
        return Fraction(self.height, UNITS_PER_INCH)

    @property
    def is_blank(self) -> bool:
        return not self.dots and not any(inked.dots for inked in self.ink_dots)

    def all_dots(self) -> tuple[Dot, ...]:
        """Every dot struck, black or inked."""
        return self.dots + tuple(dot for inked in self.ink_dots for dot in inked.dots)
