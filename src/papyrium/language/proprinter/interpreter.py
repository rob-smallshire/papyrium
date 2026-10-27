"""ProprinterInterpreter: an incremental interpreter for the 9-wire IBM Proprinters.

Written from IBM's Proprinter manuals (``docs/ibm-proprinter-ii.md``).
The Proprinter's commands are close kin to Epson's, and much of the
machinery is the same: the line buffer, paper motion, forms, tabs,
bit-image graphics and the character generator are the ESC/P
interpreter's. What is the Proprinter's own is here: its command table,
in which many letters mean something else; its character sets 1 and 2
of the IBM PC characters; its print faces chosen by ``ESC I``, NLQ among
them made from the draft characters; its download characters; and the
way its print modes mask one another.
"""

from __future__ import annotations

import logging
from collections.abc import Callable

from papyrium.core.dotfont import DotFont, Glyph
from papyrium.core.page import inches
from papyrium.language.escp.charsets import ADDITIONAL_LOCATION, IBM_LOCATION, rom_location
from papyrium.language.escp.interpreter import (
    DC2,
    DC3,
    DEL,
    ELITE_WIDTH,
    FEED_STEP,
    SI,
    ArgumentReader,
    EscpInterpreter,
    UserCharacter,
)
from papyrium.language.proprinter.mechanism import ProprinterMechanism
from papyrium.language.proprinter.nlq import NLQ_SCALE, nlq_from_draft

logger = logging.getLogger(__name__)

#: The print faces ESC I chooses, in its low two bits; bit 2 takes the
#: characters from the download area.
DRAFT, FASTFONT, NLQ, NLQ_II = 0, 1, 2, 3
DOWNLOAD = 4

#: The low codes character set 2 prints: the card suits and the section sign.
SET_2_LOW_CODES = frozenset({3, 4, 5, 6, 21})

#: The block graphics, never underscored or overscored: line drawing and
#: shading at 176-223, and 244.
BLOCK_GRAPHICS = frozenset(range(176, 224)) | {244}

#: The shading characters, which NLQ prints as they are in draft.
SHADING = frozenset({176, 177, 178})

#: The printer ID of a download font derived from the draft font, and of
#: an NLQ II download font.
DRAFT_DOWNLOAD_ID = 20
NLQ_II_DOWNLOAD_ID = 21

#: Bytes for each draft download character: two attribute bytes and eleven
#: column bytes.
DOWNLOAD_CHARACTER_BYTES = 13

#: The kinds of download character, in attribute byte 1's low two bits.
ORDINARY, LINE_DRAWING, SHADING_KIND = 0, 1, 2

#: The most horizontal and vertical tab stops.
HORIZONTAL_TAB_STOPS = 28
VERTICAL_TAB_STOPS = 64


class ProprinterInterpreter(EscpInterpreter):
    """Interprets the IBM Proprinter's language for a printer described by
    a :class:`ProprinterMechanism`."""

    _mechanism: ProprinterMechanism

    def _initialise(self) -> None:
        super()._initialise()
        # ESC I: the face, and whether it comes from the download area.
        self._face = DRAFT
        self._stored_line_spacing: int | None = None
        # The draft download area holds a copy of the resident characters
        # until characters are downloaded into it.
        self._ram_holds_rom = True
        self._shading_downloads: set[int] = set()

    # -- Character sets -----------------------------------------------------

    def _is_printable(self, byte: int) -> bool:
        """Character set 1 obeys codes 128-159 as controls; set 2 prints them,
        and the card suits and section sign among the low codes."""
        if byte & 0x80:
            return self._ibm_set == 2 or byte >= 0xA0
        if byte in SET_2_LOW_CODES:
            return self._ibm_set == 2
        return 0x20 <= byte < DEL

    def _location(self, byte: int) -> int:
        if byte & 0x80:
            return IBM_LOCATION + (byte & 0x7F)
        if byte < 0x20:
            return ADDITIONAL_LOCATION + byte
        return rom_location(byte, self._character_set, self._mechanism.national_differences)

    def _control(self, code: int) -> ArgumentReader:
        if code == SI:
            self._print_line()
            self._condensed = True
        elif code == DC2:
            # Back to 10 cpi from condensed and 12 cpi, keeping double width.
            self._condensed = self._elite = False
        elif code in (DC3, DEL):
            pass
        else:
            yield from super()._control(code)

    # -- Print faces --------------------------------------------------------

    def _print_face(self) -> int:
        """The face characters print in, once the modes have masked one another.

        Double strike prints NLQ. Condensed (unless 12 cpi masks it), super-
        and subscript mask both NLQ faces, and emphasized masks NLQ.
        """
        face = self._face
        if face == DRAFT and self._double_strike:
            face = NLQ
        if face == NLQ_II and self._mechanism.nlq_ii_font is None:
            face = NLQ
        if face == FASTFONT and self._mechanism.fastfont is None:
            face = DRAFT
        condensed = self._condensed and not self._elite
        if face in (NLQ, NLQ_II) and (condensed or self._script is not None):
            return DRAFT
        if face == NLQ and self._emphasized:
            return DRAFT
        return face

    def _print_location(self, location: int) -> None:
        face = self._print_face()
        if face == NLQ_II:
            glyph = self._nlq_ii_glyph(location)
            if glyph is not None:
                self._nlq_character(location, glyph, False, self._mechanism.nlq_ii_font.columns)
                return
        elif face == NLQ and not self._is_shading(location):
            glyph = nlq_from_draft(self._glyph(location))
            self._nlq_character(location, glyph, False, self._nlq_columns())
            return
        super()._print_location(location)

    def _nlq_ii_glyph(self, location: int) -> Glyph | None:
        """The resident NLQ II character for *location*, or None to print draft."""
        if self._face & DOWNLOAD:
            logger.debug("NLQ II download characters are not modelled; printing resident ones")
        character = self._rom_character(location)
        glyph = self._mechanism.nlq_ii_font.glyph(character)
        if glyph is None:
            self._report_missing(character, "printing draft")
        return glyph

    def _is_shading(self, location: int) -> bool:
        if location in self._shading_downloads and self._glyph_source(location)[0] == "ram":
            return True
        return location - IBM_LOCATION + 0x80 in SHADING

    def _nlq_columns(self) -> int:
        """NLQ's grid has twice the draft cell's columns."""
        return NLQ_SCALE * super()._cell_columns(self._column_width())

    def _nlq_font(self) -> DotFont | None:
        # Only the faces chosen here print NLQ; the ESC/P interpreter's NLQ
        # and enlarged characters, which would look for an NLQ font, do not.
        return None

    def _draft_font(self) -> DotFont:
        if self._print_face() == FASTFONT:
            return self._mechanism.fastfont
        return self._mechanism.font

    def _column_width(self) -> int:
        """Fastfont is 12 cpi; 12 cpi masks condensed, and emphasized masks
        condensed too."""
        if self._print_face() == FASTFONT:
            return ELITE_WIDTH
        return super()._column_width()

    def _cell_columns(self, pitch: int) -> int:
        if self._print_face() == FASTFONT:
            return self._mechanism.fastfont.columns
        return super()._cell_columns(pitch)

    def _is_emphasized(self) -> bool:
        """Emphasized prints at any pitch; condensed, not emphasized, gives way."""
        return self._emphasized

    def _is_lined(self, location: int) -> bool:
        return location - IBM_LOCATION + 0x80 not in BLOCK_GRAPHICS

    # -- Paper motion -------------------------------------------------------

    def _form_feed(self) -> None:
        if self._mechanism.form_feed_at_top_ignored and self._at_top_of_blank_form():
            logger.debug("ignoring a form feed at the top of a blank form")
            return
        super()._form_feed()

    def _at_top_of_blank_form(self) -> bool:
        if self._y != self._form_top + self._top_margin or self._line:
            return False
        return not any(y >= self._form_top for dots in self._paper_dots.values() for _, y in dots)

    def _vertical_tab(self) -> None:
        """Feed to the next stop on the form, or a line where there is none."""
        position = self._y - self._form_top
        last = self._form_length - self._skip_perforation
        below = [tab for tab in self._vertical_tabs if position < tab < last]
        if not below:
            self._line_feed()
            return
        self._end_line()
        if self._mechanism.line_feed_returns:
            self._x = self._left_margin
        self._one_line_double_width = False
        self._advance(below[0] - position)

    # -- Escape commands ----------------------------------------------------

    #: The commands whose ESC/P handlers do what the Proprinter's do.
    _SHARED_COMMANDS = "-013CEFGHKLNOSTUXYZ[_"

    def _escape_table(self) -> dict[str, Callable[[], ArgumentReader | None]]:
        escp = super()._escape_table()
        table = {letter: escp[letter] for letter in self._SHARED_COMMANDS}

        def setter(attribute: str, value) -> Callable[[], None]:
            return lambda: setattr(self, attribute, value)

        table.update(
            {
                "2": self._esc_stored_line_spacing,
                "4": self._set_top_of_form,
                "5": self._esc_auto_line_feed,
                "6": setter("_ibm_set", 2),
                "7": setter("_ibm_set", 1),
                ":": setter("_elite", True),
                "=": self._esc_download,
                "A": self._esc_store_line_spacing,
                "B": self._esc_vertical_tab_lines,
                "D": self._esc_horizontal_tab_columns,
                "I": self._esc_print_mode,
                "J": self._esc_feed,
                "P": self._esc_proportional,
                "Q": self._esc_deselect,
                "R": self._esc_reset_tabs,
                "W": self._esc_continuous_double_width,
                "\\": self._esc_print_codes,
                "^": self._esc_print_code,
            }
        )
        return table

    def _fs_table(self) -> dict[str, Callable[[], ArgumentReader | None]]:
        """Star's commands after FS in the LC-10's IBM mode: the ESC/P
        commands whose letters the Proprinter's commands took."""
        return {
            "4": self._esc_italic,
            "5": lambda: setattr(self, "_italic", False),
            ":": self._esc_copy_rom,
            "=": lambda: setattr(self, "_msb", 0),
            "Q": self._esc_right_margin,
            "R": self._esc_character_set,
            "\\": self._esc_relative_position,
        }

    def _esc_store_line_spacing(self) -> ArgumentReader:
        """Keep n/72 inch, 1-85, for ESC 2 to bring into force; 0 keeps the last."""
        n = yield
        if 0 < n <= 85:
            self._stored_line_spacing = n * self._mechanism.pin_pitch
        else:
            logger.debug("keeping the stored line spacing, not %d/72 inch", n)

    def _esc_stored_line_spacing(self) -> None:
        """The spacing ESC A kept, or 1/6 inch if none."""
        self._line_spacing = self._stored_line_spacing or inches(1) // 6

    def _esc_auto_line_feed(self) -> ArgumentReader:
        """Carriage return also feeds a line (1) or not (0)."""
        self._auto_line_feed = self._flag((yield))

    def _esc_print_mode(self) -> ArgumentReader:
        """0 draft, 1 Fastfont, 2 NLQ, 3 NLQ II; 4-7 the same from the download area."""
        n = yield
        if n > 7:
            logger.debug("ignoring print mode %d", n)
            return
        self._print_line()
        self._face = n & ~DOWNLOAD
        self._user_set_selected = bool(n & DOWNLOAD)

    def _esc_feed(self) -> ArgumentReader:
        """Feed n/216 inch once, returning the carriage where a line feed does."""
        n = yield
        self._print_line()
        if self._mechanism.line_feed_returns:
            self._x = self._left_margin
        self._advance(n * FEED_STEP)

    def _esc_deselect(self) -> ArgumentReader:
        """ESC Q 3: deselected until DC1."""
        if (yield) == 3:
            self._print_line()
            self._selected = False

    def _esc_reset_tabs(self) -> None:
        """The power-on horizontal tabs again, and no vertical tabs."""
        self._tabs = self._default_tabs()
        self._vertical_tab_channels[self._vertical_tab_channel] = []
        self._vertical_tabs = self._vertical_tab_channels[self._vertical_tab_channel]

    def _esc_vertical_tab_lines(self) -> ArgumentReader:
        """Up to 64 vertical stops, by line number, line 1 the top of form."""
        lines = yield from self._read_stops(VERTICAL_TAB_STOPS)
        stops = [(line - 1) * self._line_spacing for line in lines]
        stops = [stop for stop in stops if stop < self._form_length]
        self._vertical_tab_channels[self._vertical_tab_channel] = stops
        self._vertical_tabs = stops

    def _esc_horizontal_tab_columns(self) -> ArgumentReader:
        """Up to 28 horizontal stops, by column, column 1 at the left margin."""
        columns = yield from self._read_stops(HORIZONTAL_TAB_STOPS)
        width = self._tab_unit()
        self._tabs = [(column - 1) * width for column in columns]

    def _esc_continuous_double_width(self) -> ArgumentReader:
        """Double width on (1) or off (0), either way ending SO's."""
        self._double_width = self._flag((yield))
        self._one_line_double_width = False

    def _esc_print_codes(self) -> ArgumentReader:
        """Print the next n1 + 256 n2 bytes from the All Characters Chart."""
        low = yield
        high = yield
        for _ in range(low + 256 * high):
            yield from self._print_any_code()

    def _esc_print_code(self) -> ArgumentReader:
        """Print the next byte from the All Characters Chart."""
        yield from self._print_any_code()

    def _print_any_code(self) -> ArgumentReader:
        byte = yield
        if byte == 0:
            location = 0x20  # The chart leaves code 0 blank.
        elif byte < 0x20:
            location = ADDITIONAL_LOCATION + byte
        else:
            location = self._location(byte)
        self._print_location(location)

    # -- Download characters ------------------------------------------------

    def _esc_download(self) -> ArgumentReader:
        """ESC = n1 n2 ID start, then for each character two attribute bytes
        and eleven column bytes, n1 + 256 n2 counting the bytes after it.

        A count of 0, or of 1 with the draft ID, copies the resident
        characters into the draft download area again.
        """
        low = yield
        high = yield
        count = low + 256 * high
        if count == 0:
            self._reset_download_area()
            return
        printer_id = yield
        if count == 1:
            if printer_id == DRAFT_DOWNLOAD_ID:
                self._reset_download_area()
            else:
                logger.debug("ignoring initialisation of download area %d", printer_id)
            return
        start = yield
        remaining = count - 2
        if printer_id != DRAFT_DOWNLOAD_ID:
            logger.debug("ignoring %d bytes of download font %d", remaining, printer_id)
            for _ in range(remaining):
                yield
            return
        characters, leftover = divmod(remaining, DOWNLOAD_CHARACTER_BYTES)
        for index in range(characters):
            data = []
            for _ in range(DOWNLOAD_CHARACTER_BYTES):
                data.append((yield))
            code = start + index
            if code > 0xFF:
                logger.debug("ignoring a download character beyond code 255")
                continue
            self._define_download_character(self._location(code), data[0], data[1], data[2:])
        for _ in range(leftover):
            yield

    def _reset_download_area(self) -> None:
        self._ram.clear()
        self._shading_downloads.clear()
        self._ram_holds_rom = True

    def _define_download_character(
        self, location: int, kind_attribute: int, spacing_attribute: int, columns: list[int]
    ) -> None:
        """A draft download character, every dot it gives kept: draft drops
        those that follow a printed one, but NLQ prints them all."""
        kind = kind_attribute & 0x03
        # Bit 7 makes an ordinary character a descender, on the bottom eight wires.
        top_row = 1 if kind == ORDINARY and kind_attribute & 0x80 else 0
        dots = {
            (column, top_row + bit)
            for column, pattern in enumerate(columns)
            for bit in range(8)
            if pattern & (0x80 >> bit)
        }
        if kind == LINE_DRAWING:
            # Row 8 carries on down through rows 9 to 12.
            dots |= {(column, row) for column, top in dots if top == 7 for row in range(8, 12)}
        elif kind == SHADING_KIND:
            # Rows 1 to 4 repeat as rows 9 to 12.
            dots |= {(column, row + 8) for column, row in dots if row < 4}
        if kind == SHADING_KIND:
            self._shading_downloads.add(location)
        else:
            self._shading_downloads.discard(location)
        skip, printed = (spacing_attribute >> 4) & 0x07, spacing_attribute & 0x0F
        if spacing_attribute == 0:
            printed = 11
        printed = min(printed, 11)
        # Each proportional character is followed by one blank column.
        self._ram[location] = UserCharacter(
            Glyph(frozenset(dots)), first_column=skip, last_column=skip + printed
        )
