"""The text layer: which character was printed in which cell."""

from helpers import ESC, LEFT, LINE, PICA, run

from papyrium.core.page import TextMark


def _text(data, **options):
    pages = run(data, **options)
    return [[(mark.x, mark.y, mark.character) for mark in page.text] for page in pages]


def test_each_character_is_recorded_in_its_cell():
    (page,) = run(b"AB")
    assert page.text == (
        TextMark(LEFT, 0, PICA, 540, "A"),
        TextMark(LEFT + PICA, 0, PICA, 540, "B"),
    )


def test_text_follows_lines_and_pages():
    assert _text(b"A\nB\x0cA") == [[(LEFT, 0, "A"), (LEFT, LINE, "B")], [(LEFT, 0, "A")]]


def test_national_characters_are_recorded_as_printed():
    assert _text(ESC + b"R\x03#") == [[(LEFT, 0, chr(0x00A3))]]


def test_deleted_and_cancelled_characters_leave_no_text():
    assert _text(b"AB\x7f") == [[(LEFT, 0, "A")]]
    assert _text(b"AB\x18A") == [[(LEFT, 0, "A")]]


def test_script_cells_are_half_height():
    (page,) = run(ESC + b"S\x01A")
    assert (page.text[0].y, page.text[0].height) == (240, 270)


def test_a_page_of_spaces_alone_is_not_printed():
    assert run(b"   ") == []
