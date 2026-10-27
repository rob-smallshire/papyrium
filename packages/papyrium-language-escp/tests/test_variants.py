"""Mechanism settings for ESC/P printers that differ from the FX-80."""

import logging

from helpers import ESC, LEFT, LINE, dots, run

from papyrium.language.escp import CharacterSet
from papyrium.language.escp.charsets import (
    LX800_CHARACTER_SETS,
    M1109_CHARACTER_SETS,
    character_for,
)
from papyrium.language.escp.generator import CharacterGenerator

M1109_CONTROLS = frozenset({8, 9, 10, 11, 12, 13, 14, 15, 18, 19, 20, 27})


def text(data, **options):
    (page,) = run(data, **options)
    return "".join(mark.character for mark in page.text)


def test_norway_denmark_ii_and_england_ii():
    assert character_for(0x24, CharacterSet.NORWAY) == chr(0xA4)
    assert character_for(0x24, CharacterSet.DENMARK_II) == "$"
    assert character_for(0x40, CharacterSet.DENMARK_II) == chr(0xC9)
    assert character_for(0x60, CharacterSet.UK_II) == chr(0xA3)
    assert character_for(0x23, CharacterSet.UK_II) == "#"


def test_the_fx80_ignores_the_extra_national_sets():
    assert text(ESC + b"R\x0b`") == "`"


def test_a_printer_with_twelve_sets_selects_them():
    assert text(ESC + b"R\x0b`", character_sets=M1109_CHARACTER_SETS) == chr(0xA3)


def test_spain_ii_and_latin_america():
    assert character_for(0x40, CharacterSet.SPAIN_II) == "á"
    assert character_for(0x5C, CharacterSet.SPAIN_II) == "Ñ"
    assert character_for(0x7B, CharacterSet.SPAIN_II) == "í"
    assert character_for(0x60, CharacterSet.SPAIN_II) == "`"
    assert character_for(0x60, CharacterSet.LATIN_AMERICA) == "ü"
    assert character_for(0x7E, CharacterSet.LATIN_AMERICA) == "ú"


def test_set_numbers_are_the_printers_own():
    # ESC R 11 is England II on the M-1109 and Spain II on the LX-800.
    assert text(ESC + b"R\x0b@`", character_sets=M1109_CHARACTER_SETS) == "@" + chr(0xA3)
    assert text(ESC + b"R\x0b@`", character_sets=LX800_CHARACTER_SETS) == "á`"
    assert text(ESC + b"R\x0c`", character_sets=LX800_CHARACTER_SETS) == "ü"


def test_characters_beyond_the_international_ones_print_upright():
    # The test font has no á: it prints nothing, upright, and is recorded as text.
    marks = run(ESC + b"R\x0b@A", character_sets=LX800_CHARACTER_SETS)[0].text
    assert [mark.character for mark in marks] == ["á", "A"]


def test_low_codes_that_stay_controls_are_the_mechanisms():
    # Code 24 is CAN on the FX-80 even with ESC I 1; on the M-1109 it prints.
    assert text(ESC + b"I\x01A\x18B") == "B"
    assert text(ESC + b"I\x01A\x18B", controls=M1109_CONTROLS) == "A" + chr(0xD6) + "B"


def test_without_default_vertical_tabs_vt_is_a_line_feed():
    assert dots(b"\x0bA", default_vertical_tabs=False) == [(LEFT + 36, LINE)]


def test_form_length_can_clear_the_vertical_tabs():
    data = ESC + b"B\x05\x00" + ESC + b"C\x42\x0bA"
    assert dots(data) == [(LEFT + 36, 5 * LINE)]
    assert dots(data, form_length_clears_vertical_tabs=True) == [(LEFT + 36, LINE)]


def test_cancel_can_end_one_line_enlarged():
    # Double width strikes each dot twice, a half column apart.
    assert len(dots(b"\x0e\x18A")) == 2
    assert len(dots(b"\x0e\x18A", cancel_ends_one_line_enlarged=True)) == 1


def test_condensed_elite_is_twenty_characters_an_inch():
    data = ESC + b"M\x0fAA"
    assert [x for x, _ in dots(data)] == [LEFT + 30, LEFT + 30 + 360]
    assert [x for x, _ in dots(data, condensed_elite=True)] == [LEFT + 18, LEFT + 18 + 216]


def test_bit_image_mode_7_is_144_dots_an_inch_without_adjacent_dots():
    data = ESC + b"*\x07\x03\x00\x80\x80\x80"
    assert run(data) == []
    assert dots(data, graphics_modes=frozenset(range(8))) == [(LEFT, 0), (LEFT + 60, 0)]


def test_nlq_prints_draft_double_struck_when_the_printer_has_it():
    # Without NLQ, ESC x is an unknown command and the 1 that follows prints.
    assert len(run(ESC + b"x1A")[0].text) == 2
    assert dots(ESC + b"x\x01A", nlq=True) == [(LEFT + 36, 0), (LEFT + 36, 20)]
    assert dots(ESC + b"x\x01" + ESC + b"x\x00A", nlq=True) == [(LEFT + 36, 0)]


def test_a_printer_can_power_on_in_nlq():
    assert dots(b"A", nlq=True, near_letter_quality=True) == [(LEFT + 36, 0), (LEFT + 36, 20)]


def _nlq_font(column=0):
    from papyrium.core.testing import MemoryDotFont

    # A: one column of the first pass's top pin, and the next of the second pass's.
    rows = ["." * 24 for _ in range(18)]
    rows[0] = "." * column + "#" + rows[0][column + 1 :]
    rows[1] = "." * (column + 1) + "#" + rows[1][column + 2 :]
    text = "rows 18\ncolumns 24\nU+0041\n" + "\n".join(rows) + "\n"
    return MemoryDotFont(name=f"nlq-{column}", text=text)


TWO_TYPEFACES = {"nlq": True, "nlq_fonts": (_nlq_font(0), _nlq_font(4))}


def test_esc_k_chooses_the_nlq_typeface():
    assert dots(ESC + b"x\x01" + ESC + b"k\x01A", **TWO_TYPEFACES) == [
        (LEFT + 72, 0),
        (LEFT + 90, 20),
    ]
    assert dots(ESC + b"x\x01" + ESC + b"k\x01" + ESC + b"k\x00A", **TWO_TYPEFACES) == [
        (LEFT, 0),
        (LEFT + 18, 20),
    ]


def test_esc_k_in_draft_takes_effect_with_nlq():
    assert dots(ESC + b"k\x01" + ESC + b"x\x01A", **TWO_TYPEFACES)[0] == (LEFT + 72, 0)


def test_a_typeface_the_printer_has_no_font_for_prints_in_the_first(caplog):
    options = {"nlq": True, "nlq_fonts": (_nlq_font(0), None)}
    with caplog.at_level(logging.WARNING):
        assert dots(ESC + b"x\x01" + ESC + b"k\x01AA", **options)[:2] == [
            (LEFT, 0),
            (LEFT + 18, 20),
        ]
    assert caplog.text.count("typeface 1") == 1


def test_a_printer_without_nlq_ignores_esc_k():
    assert dots(ESC + b"k\x01A") == dots(b"A")


def test_an_nlq_font_gives_two_passes_on_a_240th_inch_grid():
    assert dots(ESC + b"x\x01A", nlq=True, nlq_fonts=(_nlq_font(),)) == [(LEFT, 0), (LEFT + 18, 20)]


def test_characters_the_nlq_font_lacks_print_draft_double_struck():
    assert dots(ESC + b"x\x01B", nlq=True, nlq_fonts=(_nlq_font(),)) == [
        (LEFT + 36, 0),
        (LEFT + 36, 20),
        (LEFT + 108, 360),
        (LEFT + 108, 380),
    ]


def test_nlq_is_always_ten_characters_an_inch():
    data = ESC + b"M" + ESC + b"x\x01AA"
    assert [x for x, _ in dots(data, nlq=True, nlq_fonts=(_nlq_font(),))][::2] == [LEFT, LEFT + 432]


def test_enlarged_nlq_doubles_the_grid_and_strikes_each_dot_twice():
    assert dots(ESC + b"x\x01" + ESC + b"W\x01A", nlq=True, nlq_fonts=(_nlq_font(),)) == [
        (LEFT, 0),
        (LEFT + 18, 0),
        (LEFT + 36, 20),
        (LEFT + 54, 20),
    ]


def _bar_font():
    from papyrium.core.testing import MemoryDotFont

    # A: a bar across columns 0-4 of the top row.
    rows = ["#####......"] + ["..........."] * 8
    text = "rows 9\ncolumns 11\nU+0020\n" + "\n".join(["..........."] * 9) + "\n\nU+0041\n"
    return MemoryDotFont(name="bar", text=text + "\n".join(rows) + "\n")


def test_dots_in_successive_columns_can_print_once():
    font = _bar_font()
    assert [x for x, _ in dots(b"A", font=font)] == [LEFT + 36 * c for c in range(5)]
    generator = CharacterGenerator(prints_adjacent_dots_once=True)
    printed = dots(b"A", font=font, generator=generator)
    assert [x for x, _ in printed] == [LEFT, LEFT + 72, LEFT + 144]


def _font_with_a_at(column, *, rows, columns):
    from papyrium.core.testing import MemoryDotFont

    lines = ["." * columns for _ in range(rows)]
    lines[0] = "." * column + "#" + lines[0][column + 1 :]
    text = f"rows {rows}\ncolumns {columns}\nU+0041\n" + "\n".join(lines) + "\n"
    return MemoryDotFont(name=f"a-at-{column}-{columns}", text=text)


ELITE_DRAFT = {"elite_font": _font_with_a_at(5, rows=9, columns=11)}


def test_a_printer_may_have_its_own_draft_font_for_elite():
    # Elite columns are 30 units apart.
    assert dots(ESC + b"MA", **ELITE_DRAFT) == [(LEFT + 5 * 30, 0)]


def test_the_elite_draft_font_is_only_for_elite():
    assert dots(b"A", **ELITE_DRAFT) == [(LEFT + 36, 0)]


def test_nlq_masks_elite_unless_the_printer_prints_nlq_elite():
    data = ESC + b"x\x01" + ESC + b"MAA"
    options = {"nlq": True, "nlq_fonts": (_nlq_font(0),)}
    assert [x for x, _ in dots(data, **options)][::2] == [LEFT, LEFT + 432]
    assert [x for x, _ in dots(data, nlq_elite=True, **options)][::2] == [LEFT, LEFT + 360]


def test_nlq_elite_prints_from_the_typefaces_elite_font():
    options = {
        "nlq": True,
        "nlq_elite": True,
        "nlq_fonts": (_nlq_font(0),),
        "nlq_elite_fonts": (_font_with_a_at(2, rows=18, columns=20),),
    }
    # The elite font's 20 columns span the 1/12 inch cell: 18 units apart.
    assert dots(ESC + b"x\x01" + ESC + b"MA", **options) == [(LEFT + 36, 0)]


def _block_font():
    from papyrium.core.testing import MemoryDotFont

    rows = ["..........." for _ in range(12)]
    rows[11] = "#.........."
    return MemoryDotFont(
        name="blocks", text="rows 12\ncolumns 11\nU+2500\n" + "\n".join(rows) + "\n"
    )


def test_block_graphics_may_come_from_a_font_of_their_own():
    # IBM code 0xC4 is a horizontal line; this font's has one dot on row 11.
    data = ESC + b"t\x01\xc4"
    assert dots(data, block_graphics_font=_block_font()) == [(LEFT, 11 * 60)]


def test_the_draft_fonts_glyph_comes_before_the_block_graphics_font():
    from papyrium.core.testing import MemoryDotFont

    text = "rows 9\ncolumns 11\nU+2500\n#..........\n" + "\n".join(["..........."] * 8) + "\n"
    font = MemoryDotFont(name="with-line", text=text)
    data = ESC + b"t\x01\xc4"
    assert dots(data, font=font, block_graphics_font=_block_font()) == [(LEFT, 0)]


class _ProportionalNlq(CharacterGenerator):
    def nlq_proportional_cell(self, glyph):
        return 5, -glyph.extent[0]


def test_nlq_is_fixed_pitch_unless_the_generator_spaces_it_proportionally():
    options = {"nlq": True, "nlq_fonts": (_nlq_font(3),)}
    data = ESC + b"x\x01" + ESC + b"p\x01AA"
    assert [x for x, _ in dots(data, **options)][::2] == [LEFT + 54, LEFT + 432 + 54]
    proportional = dots(data, generator=_ProportionalNlq(), **options)
    # A's dots begin at column 3; flush left, in a cell of five 1/240 inch columns.
    assert [x for x, _ in proportional][::2] == [LEFT, LEFT + 5 * 18]


def test_a_printer_may_differ_from_a_national_set():
    from papyrium.language.escp.charsets import LC10_NATIONAL_DIFFERENCES

    assert character_for(0x60, CharacterSet.SPAIN) == "`"
    assert character_for(0x60, CharacterSet.SPAIN, LC10_NATIONAL_DIFFERENCES) == "´"
    assert character_for(0x60, CharacterSet.SPAIN_II, LC10_NATIONAL_DIFFERENCES) == "´"
    assert character_for(0x60, CharacterSet.LATIN_AMERICA, LC10_NATIONAL_DIFFERENCES) == "ü"
    assert character_for(0x7B, CharacterSet.SPAIN, LC10_NATIONAL_DIFFERENCES) == "¨"


def test_a_printer_may_space_elite_proportionally():
    data = ESC + b"M" + ESC + b"p\x01AA"
    # Elite masks proportional on the FX-80: elite columns, 30 units apart.
    assert [x for x, _ in dots(data)] == [LEFT + 30, LEFT + 360 + 30]
    spaced = dots(data, proportional_elite=True, proportional_emphasized=False)
    # A's dot in column 1: one column wide and two of spacing, 1/120 inch.
    assert [x for x, _ in spaced] == [LEFT + 36, LEFT + 3 * 36 + 36]


def test_proportional_elite_draft_keeps_the_pica_draft_font():
    options = {**ELITE_DRAFT, "proportional_elite": True, "proportional_emphasized": False}
    assert dots(ESC + b"M" + ESC + b"p\x01A", **options) == [(LEFT + 36, 0)]


def test_proportional_need_not_print_emphasized():
    assert len(dots(ESC + b"p\x01A")) == 2
    assert len(dots(ESC + b"p\x01A", proportional_emphasized=False)) == 1


def test_proportional_elite_nlq_prints_from_the_elite_font():
    class Proportional(CharacterGenerator):
        def nlq_proportional_cell(self, glyph):
            return 5, -glyph.extent[0]

    options = {
        "nlq": True,
        "nlq_elite": True,
        "proportional_elite": True,
        "nlq_fonts": (_nlq_font(0),),
        "nlq_elite_fonts": (_font_with_a_at(2, rows=18, columns=20),),
        "generator": Proportional(),
    }
    data = ESC + b"x\x01" + ESC + b"M" + ESC + b"p\x01AA"
    assert dots(data, **options) == [(LEFT, 0), (LEFT + 5 * 18, 0)]
