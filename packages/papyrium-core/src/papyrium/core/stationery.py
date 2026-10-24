"""Stationery: what the paper bears before the printer touches it.

Continuous fanfold paper has a half-inch tear-off strip down each side,
punched with feed holes every half inch and perforated where it tears off,
and a perforation across the top of each sheet. Listing paper is also
printed: green-bar and blue-bar paper tint alternate half-inch bands, three
lines at six lines per inch, and music-ruled paper rules alternate bands
between their lines.

A stationery's features are plain shapes, rectangles and circles, so every
output can draw them under the dots without knowing what they mean.
Positions are page units from the sheet's top-left corner.
"""

from __future__ import annotations

from dataclasses import dataclass

from papyrium.core.page import inches

Colour = tuple[int, int, int]

#: The tear-off strip down each side of fanfold paper.
STRIP_WIDTH = inches(1) // 2
#: Feed hole spacing, and diameter (5/32 inch).
HOLE_PITCH = inches(1) // 2
HOLE_DIAMETER = inches(5) // 32
#: The height of each band of listing paper: three lines at six per inch.
BAND_HEIGHT = inches(1) // 2
#: Ruled lines on music-ruled paper: one per line, 1/144 inch thick, each
#: 1/36 inch above a line printed from the band's top, so in the gap
#: between the descenders of one line and the capitals of the next.
RULE_PITCH = inches(1) // 6
RULE_THICKNESS = inches(1) // 144
RULE_RAISE = inches(1) // 36
#: The paper between the strips, or a whole cut sheet: 8.5 inches.
PAPER_WIDTH = inches(17) // 2
#: Perforations: short cuts with ties between.
PERFORATION_CUT = inches(1) // 16
PERFORATION_TIE = inches(1) // 32
PERFORATION_THICKNESS = inches(1) // 144

#: The platen seen through a feed hole.
HOLE_COLOUR: Colour = (110, 110, 110)
PERFORATION_COLOUR: Colour = (200, 200, 200)
GREEN_BAND: Colour = (214, 234, 210)
BLUE_BAND: Colour = (212, 225, 242)
GREEN_RULE: Colour = (120, 180, 130)


@dataclass(frozen=True)
class Rectangle:
    """A filled rectangle; *x* and *y* are its top-left corner."""

    x: int
    y: int
    width: int
    height: int
    colour: Colour


@dataclass(frozen=True)
class Circle:
    """A filled circle about its centre."""

    x: int
    y: int
    diameter: int
    colour: Colour


Feature = Rectangle | Circle


@dataclass(frozen=True)
class Stationery:
    """A kind of paper: its tear-off strips and what is printed between them.

    *band_colour* tints alternate bands, starting with the second; with
    *ruled*, those bands are ruled a line at a time instead of tinted.
    """

    name: str
    description: str
    strips: bool = False
    band_colour: Colour | None = None
    ruled: bool = False

    @property
    def paper_width(self) -> int:
        """The usual width of this stationery: 8.5 inches, plus any strips."""
        return PAPER_WIDTH + (2 * STRIP_WIDTH if self.strips else 0)

    def features(self, width: int, height: int) -> tuple[Feature, ...]:
        """The shapes on a sheet *width* by *height* units, back to front."""
        features: list[Feature] = []
        left, right = (STRIP_WIDTH, width - STRIP_WIDTH) if self.strips else (0, width)
        if self.band_colour is not None:
            for top in range(BAND_HEIGHT, height, 2 * BAND_HEIGHT):
                bottom = min(top + BAND_HEIGHT, height)
                if self.ruled:
                    features.extend(
                        Rectangle(left, y, right - left, RULE_THICKNESS, self.band_colour)
                        for y in range(top - RULE_RAISE, bottom - RULE_RAISE + 1, RULE_PITCH)
                        if y + RULE_THICKNESS <= height
                    )
                else:
                    features.append(
                        Rectangle(left, top, right - left, bottom - top, self.band_colour)
                    )
        if self.strips:
            features.extend(_perforation_across(0, width))
            for x in (STRIP_WIDTH, width - STRIP_WIDTH):
                features.extend(_perforation_down(x, height))
            for y in range(HOLE_PITCH // 2, height, HOLE_PITCH):
                for x in (STRIP_WIDTH // 2, width - STRIP_WIDTH // 2):
                    features.append(Circle(x, y, HOLE_DIAMETER, HOLE_COLOUR))
        return tuple(features)


def _perforation_across(y: int, width: int) -> list[Rectangle]:
    step = PERFORATION_CUT + PERFORATION_TIE
    return [
        Rectangle(x, y, min(PERFORATION_CUT, width - x), PERFORATION_THICKNESS, PERFORATION_COLOUR)
        for x in range(0, width, step)
    ]


def _perforation_down(x: int, height: int) -> list[Rectangle]:
    step = PERFORATION_CUT + PERFORATION_TIE
    return [
        Rectangle(x, y, PERFORATION_THICKNESS, min(PERFORATION_CUT, height - y), PERFORATION_COLOUR)
        for y in range(0, height, step)
    ]


#: Every kind of stationery, by name.
STATIONERY = {
    stationery.name: stationery
    for stationery in (
        Stationery("sheet", "Plain paper with no tear-off strips"),
        Stationery("fanfold", "Plain continuous paper with tear-off strips", strips=True),
        Stationery(
            "green-bar", "Listing paper with pale green bands", strips=True, band_colour=GREEN_BAND
        ),
        Stationery(
            "blue-bar", "Listing paper with pale blue bands", strips=True, band_colour=BLUE_BAND
        ),
        Stationery(
            "music-ruled",
            "Listing paper with alternate bands ruled in green between the lines",
            strips=True,
            band_colour=GREEN_RULE,
            ruled=True,
        ),
    )
}


def stationery_named(name: str) -> Stationery:
    """The stationery called *name*.

    Raises:
        KeyError: There is no such stationery.
    """
    return STATIONERY[name]
