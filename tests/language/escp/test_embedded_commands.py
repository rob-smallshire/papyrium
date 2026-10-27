"""Embedded commands, as the Star LC-10 Colour has them: a capital letter in
doubled parentheses and a digit, sent as ordinary text."""

from helpers import ESC, LEFT, LINE, PICA, dots, run
from test_variants import _nlq_font

from papyrium.core.page import Ink

EMBEDDED = {"embedded_commands": frozenset("FSCBI04RT"), "colour_ribbon": True}


def test_a_colour_command_takes_no_room_on_the_line():
    (page,) = run(b"((C))2A", **EMBEDDED)
    assert page.ink_dots[0].ink == Ink.CYAN
    assert page.ink_dots[0].dots == ((LEFT + 36, 0),)


def test_text_that_is_not_a_command_prints():
    # '(' prints in the test font as nothing, but takes a column.
    assert dots(b"((Q))1A", **EMBEDDED) == [(LEFT + 6 * PICA + 36, 0)]
    assert dots(b"(A", **EMBEDDED) == [(LEFT + PICA + 36, 0)]


def test_a_command_with_a_digit_out_of_range_prints():
    # The test font's C has a dot in column 1.
    assert dots(b"((C))9A", **EMBEDDED) == [(LEFT + 2 * PICA + 36, 0), (LEFT + 6 * PICA + 36, 0)]


def test_a_control_code_breaking_off_a_command_is_obeyed():
    assert dots(b"((\nA", **EMBEDDED) == [(LEFT + 36, LINE)]


def test_without_embedded_commands_they_are_text():
    assert dots(b"((C))2A") == [(LEFT + 2 * PICA + 36, 0), (LEFT + 6 * PICA + 36, 0)]


def test_bold_and_italic():
    assert len(dots(b"((B))1A", **EMBEDDED)) == 2
    assert dots(b"((I))1A((I))0", **EMBEDDED) == [(LEFT + 36 + 108, 0)]


def test_type_style_selects_nlq_and_draft():
    options = {**EMBEDDED, "nlq": True, "nlq_fonts": (_nlq_font(0), _nlq_font(4))}
    assert dots(b"((F))1A((F))9A", **options) == [
        (LEFT + 72, 0),
        (LEFT + 90, 20),
        (LEFT + PICA + 36, 0),
    ]


def test_size_doubles_width_and_height_on_the_base_line():
    options = {**EMBEDDED, "nlq": True, "nlq_fonts": (_nlq_font(0),)}
    printed = sorted(dots(b"\n\n((S))3A", **options))
    assert printed[0] == (LEFT, 2 * LINE - 8 * 60)
    assert (LEFT + 36, 2 * LINE - 8 * 60) in printed


def test_sheet_feeder_commands_are_taken_and_ignored():
    assert dots(b"((0))((4))((R))((T))2A", **EMBEDDED) == [(LEFT + 36, 0)]


def test_a_line_of_commands_alone_prints_blank():
    assert dots(b"((C))1\r\nA", **EMBEDDED) == []
    (page,) = run(b"((C))1\r\nA", **EMBEDDED)
    assert page.ink_dots[0].dots == ((LEFT + 36, LINE),)


def test_escape_sequences_still_work_beside_them():
    assert dots(ESC + b"M((C))0A", **EMBEDDED) == [(LEFT + 30, 0)]


def test_a_command_after_a_stray_parenthesis_is_still_a_command():
    (page,) = run(b"(((C))2A", **EMBEDDED)
    assert page.ink_dots[0].ink == Ink.CYAN
    assert page.ink_dots[0].dots == ((LEFT + PICA + 36, 0),)
