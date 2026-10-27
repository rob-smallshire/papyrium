"""Download characters: ESC = and ESC I 4-7."""

from proprinter_helpers import ESC, HALF_ROW, LEFT, NLQ_STEP, PICA, PIN, STEP, dots, faces


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


# NLQ II download characters: ESC = with printer ID 21 (TR 4-19 to 4-23).


def nlq_ii_download(start, *characters):
    """ESC = defining NLQ II *characters*, each two attribute bytes and 23
    columns of a first-pass and a second-pass byte, from code *start*."""
    data = b"".join(bytes(character) for character in characters)
    count = len(data) + 2
    return ESC + b"=" + bytes([count % 256, count // 256, 21, start]) + data


def nlq_ii_character(kind=0, columns=((0x80, 0x80),)):
    data = [byte for column in columns for byte in column]
    return [kind, 0, *data, *[0] * (46 - len(data))]


def test_esc_i_7_prints_downloaded_nlq_ii_characters():
    data = nlq_ii_download(ord("A"), nlq_ii_character())
    resident = [(LEFT + 2 * NLQ_STEP, 0)]
    assert dots(data + ESC + b"I\x03A", **faces()) == resident
    assert dots(data + ESC + b"I\x07A", **faces()) == [(LEFT, 0), (LEFT, HALF_ROW)]


def test_esc_i_7_prints_resident_nlq_ii_for_codes_not_downloaded():
    data = nlq_ii_download(ord("B"), nlq_ii_character())
    assert dots(data + ESC + b"I\x07A", **faces()) == [(LEFT + 2 * NLQ_STEP, 0)]


def test_a_descending_nlq_ii_character_starts_two_rows_lower():
    data = nlq_ii_download(ord("A"), nlq_ii_character(kind=0x80))
    assert dots(data + ESC + b"I\x07A", **faces()) == [(LEFT, PIN), (LEFT, PIN + HALF_ROW)]


def test_line_drawing_carries_rows_15_and_16_down_to_row_24():
    data = nlq_ii_download(ord("A"), nlq_ii_character(kind=0x01, columns=((0x01, 0x01),)))
    rows = range(14, 24)
    expected = sorted((LEFT, (row // 2) * PIN + (row % 2) * HALF_ROW) for row in rows)
    assert dots(data + ESC + b"I\x07A", **faces()) == expected


def test_esc_equals_1_0_21_restores_the_resident_nlq_ii_characters():
    data = nlq_ii_download(ord("A"), nlq_ii_character()) + ESC + b"=\x01\x00\x15"
    assert dots(data + ESC + b"I\x07A", **faces()) == [(LEFT + 2 * NLQ_STEP, 0)]


def test_nlq_ii_drops_a_dot_after_one_in_its_row_unless_emphasized():
    two = nlq_ii_character(columns=((0x80, 0), (0x80, 0)))
    data = nlq_ii_download(ord("A"), two) + ESC + b"I\x07"
    assert dots(data + b"A", **faces()) == [(LEFT, 0)]
    assert dots(data + ESC + b"EA", **faces()) == [(LEFT, 0), (LEFT + NLQ_STEP, 0)]
