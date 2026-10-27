"""The Star LC-10's draft and near letter quality fonts, from its firmware."""

from __future__ import annotations

from papyrium.core.dotfont import DataDotFont

__version__ = "0.1.0"

__all__ = [
    "LC10DraftFont",
    "LC10NlqCourierEliteFont",
    "LC10NlqCourierFont",
    "LC10NlqOratorEliteFont",
    "LC10NlqOratorFont",
    "LC10NlqOratorSmallCapitalsEliteFont",
    "LC10NlqOratorSmallCapitalsFont",
    "LC10NlqSanserifEliteFont",
    "LC10NlqSanserifFont",
]


class LC10DraftFont(DataDotFont):
    """The Star LC-10's draft font, extracted from its firmware ROM.

    9 rows by 11 columns 1/120 inch apart, the last two left for spacing;
    a character with a descender sits a pin lower, on the ninth pin.
    Successive columns may both hold a dot, as in the ROM. Covers ASCII,
    the national characters, the slashed zero, the IBM PC's low symbols
    and the upper half of its character set less the block and box
    drawing characters and the integral halves.
    """

    font_filename = "draft.txt"


class _LC10NlqFont(DataDotFont):
    """An LC-10 NLQ typeface, extracted from its firmware ROM.

    18 rows: the pins of the first pass on even rows and of the second on
    odd rows, half a dot lower; a character with a descender sits a pin
    (two rows) lower. Columns are 1/240 inch apart, 24 to the pica cell
    and 20 to the elite one, the character placed in its cell as the
    printer places it. Covers the same characters as the draft font.
    """


class LC10NlqCourierFont(_LC10NlqFont):
    """The Star LC-10's NLQ Courier in pica, extracted from its firmware ROM."""

    font_filename = "nlq-courier.txt"


class LC10NlqSanserifFont(_LC10NlqFont):
    """The Star LC-10's NLQ Sanserif in pica, extracted from its firmware ROM."""

    font_filename = "nlq-sanserif.txt"


class LC10NlqOratorFont(_LC10NlqFont):
    """The Star LC-10's NLQ Orator with lower case in pica, from its firmware ROM."""

    font_filename = "nlq-orator.txt"


class LC10NlqOratorSmallCapitalsFont(_LC10NlqFont):
    """The Star LC-10's NLQ Orator with small capitals in pica, from its firmware ROM."""

    font_filename = "nlq-orator-small-capitals.txt"


class LC10NlqCourierEliteFont(_LC10NlqFont):
    """The Star LC-10's NLQ Courier in elite, extracted from its firmware ROM."""

    font_filename = "nlq-courier-elite.txt"


class LC10NlqSanserifEliteFont(_LC10NlqFont):
    """The Star LC-10's NLQ Sanserif in elite, extracted from its firmware ROM."""

    font_filename = "nlq-sanserif-elite.txt"


class LC10NlqOratorEliteFont(_LC10NlqFont):
    """The Star LC-10's NLQ Orator with lower case in elite, from its firmware ROM."""

    font_filename = "nlq-orator-elite.txt"


class LC10NlqOratorSmallCapitalsEliteFont(_LC10NlqFont):
    """The Star LC-10's NLQ Orator with small capitals in elite, from its firmware ROM."""

    font_filename = "nlq-orator-small-capitals-elite.txt"
