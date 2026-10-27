"""Download characters: ESC = and ESC I 4-7."""

from proprinter_helpers import ESC, LEFT, NLQ_STEP, PICA, PIN, STEP, dots


def download(start, *characters):
    """ESC = defining *characters*, each two attribute bytes and eleven
    columns, from code *start*."""
    data = b"".join(bytes(character) for character in characters)
    count = len(data) + 2
    return ESC + b"=" + bytes([count % 256, count // 256, 20, start]) + data


def character(kind=0, spacing=0, columns=(0x80,)):
    return [kind, spacing, *columns, *[0] * (11 - len(columns))]


def test_download_characters_print_once_esc_i_4_selects_them():
    data = download(ord("A"), character())
    assert dots(data + b"A") == [(LEFT + STEP, 0)]
    assert dots(data + ESC + b"I\x04A") == [(LEFT, 0)]


def test_the_download_area_starts_as_a_copy_of_the_resident_characters():
    assert dots(download(ord("A"), character()) + ESC + b"I\x04B") == [
        (LEFT + STEP, 0),
        (LEFT + STEP, PIN),
    ]


def test_esc_equals_0_0_copies_the_resident_characters_again():
    data = download(ord("A"), character()) + ESC + b"=\x00\x00" + ESC + b"I\x04A"
    assert dots(data) == [(LEFT + STEP, 0)]


def test_bit_7_of_the_first_attribute_makes_a_descender():
    assert dots(download(ord("A"), character(kind=0x80)) + ESC + b"I\x04A") == [(LEFT, PIN)]


def test_line_drawing_carries_row_8_down_to_row_12():
    data = download(ord("A"), character(kind=0x81, columns=(0x01,)))
    assert dots(data + ESC + b"I\x04A") == [(LEFT, row * PIN) for row in range(7, 12)]


def test_shading_repeats_rows_1_to_4_as_rows_9_to_12():
    data = download(ord("A"), character(kind=0x02, columns=(0x90,)))
    rows = [0, 3, 8, 11]
    assert dots(data + ESC + b"I\x04A") == [(LEFT, row * PIN) for row in rows]


def test_the_second_attribute_gives_the_proportional_columns():
    # Skip column 0, print columns 1 and 2, then one blank column.
    data = download(ord("A"), character(spacing=0x12, columns=(0x00, 0x80)))
    assert dots(data + ESC + b"I\x04" + ESC + b"P\x01AA") == [(LEFT, 0), (LEFT + 3 * STEP, 0)]


def test_downloaded_characters_print_in_nlq_with_esc_i_6():
    # Two dots side by side: draft prints the first, NLQ both.
    data = download(ord("A"), character(columns=(0x80, 0x80)))
    assert dots(data + ESC + b"I\x04A") == [(LEFT, 0)]
    assert dots(data + ESC + b"I\x06A") == [(LEFT, 0), (LEFT + 2 * NLQ_STEP, 0)]


def test_nlq_prints_downloaded_shading_as_draft():
    data = download(ord("A"), character(kind=0x02, columns=(0xC0,)))
    rows = [0, 1, 8, 9]
    assert dots(data + ESC + b"I\x06A") == [(LEFT, row * PIN) for row in rows]


def test_a_download_for_another_printer_id_is_skipped():
    data = ESC + b"=\x04\x00\x15A\x00\x00"
    assert dots(data + ESC + b"I\x04AA") == [(LEFT + STEP, 0), (LEFT + PICA + STEP, 0)]


def test_bytes_short_of_a_whole_character_are_skipped():
    count = 13 + 2 + 3
    data = ESC + b"=" + bytes([count, 0, 20, ord("A")]) + bytes(character()) + b"\x80\x80\x80"
    assert dots(data + ESC + b"I\x04AA") == [(LEFT, 0), (LEFT + PICA, 0)]
