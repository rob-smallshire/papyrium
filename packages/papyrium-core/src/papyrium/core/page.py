"""The page model: what a printer put on each sheet, independent of any output.

Positions and sizes are whole numbers of *units*, 1/4320 inch, measured from
the page's top-left corner with y increasing down the page. The unit divides
exactly into every step the impact printers Papyrium models can make: FX-80
graphics densities (1/60 to 1/240 inch), line feeds in 1/72 and 1/216 inch,
condensed columns (7/1440 inch) and Diablo 630 steps (1/120 and 1/48 inch).
So the same bytes always give the same marks, with no rounding.

A page holds *dots*, each a single strike of one pin, all of one diameter,
and *text*: which character was printed in which cell, so outputs can make
the page searchable and tests can compare content. Glyph and path marks,
for daisywheels and plotters, join the model when those printers do.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

#: Page units per inch.
UNITS_PER_INCH = 4320

Dot = tuple[int, int]


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
    dots struck, in the order they were struck, each *dot_diameter* units
    across. *text* records the characters printed, in printing order.
    """

    number: int
    width: int
    height: int
    dot_diameter: int
    dots: tuple[Dot, ...] = ()
    text: tuple[TextMark, ...] = ()

    @property
    def width_inches(self) -> Fraction:
        return Fraction(self.width, UNITS_PER_INCH)

    @property
    def height_inches(self) -> Fraction:
        return Fraction(self.height, UNITS_PER_INCH)

    @property
    def is_blank(self) -> bool:
        return not self.dots
