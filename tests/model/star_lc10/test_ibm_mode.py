"""The LC-10's IBM mode: the Proprinter II's commands and character sets on
the LC-10's own typefaces (switch 1-6 off)."""

from papyrium.model.star_lc10 import StarLC10, StarLC10Colour

ESC, FS = b"\x1b", b"\x1c"


def _pages(data, *, ibm_mode, model=StarLC10, **options):
    interpreter = model(name="star-lc10", ibm_mode=ibm_mode, **options).create_interpreter()
    return interpreter.feed(data + b"\r\n\x0c") + interpreter.finish()


def ibm(data, **options):
    """The dots *data* prints in IBM mode."""
    return [page.dots for page in _pages(data, ibm_mode=True, **options)]


def standard(data, **options):
    """The dots *data* prints in Standard mode."""
    return [page.dots for page in _pages(data, ibm_mode=False, **options)]


def text(data, **options):
    pages = _pages(data, ibm_mode=True, **options)
    return "".join(mark.character for page in pages for mark in page.text).strip()


def test_switch_1_6_off_speaks_the_proprinters_language():
    assert StarLC10(name="star-lc10", ibm_mode=True).languages() == ("proprinter",)
    assert StarLC10(name="star-lc10").languages() == ("escp",)


def test_draft_prints_as_in_standard_mode():
    assert ibm(b"Draft") == standard(b"Draft")


def test_esc_i_chooses_the_lc10s_typefaces():
    assert ibm(ESC + b"I\x01Elite") == standard(ESC + b"MElite")
    assert ibm(ESC + b"I\x02Sanserif") == standard(ESC + b"x\x01" + ESC + b"k\x01Sanserif")
    assert ibm(ESC + b"I\x03Courier") == standard(ESC + b"x\x01" + ESC + b"k\x00Courier")
    assert ibm(ESC + b"I\x07Courier") == standard(ESC + b"x\x01" + ESC + b"k\x00Courier")
    assert ibm(ESC + b"I\x02" + ESC + b"I\x00Draft") == standard(b"Draft")


def test_the_commands_of_both_modes():
    for both in (b"x\x01NLQ", b"!\x08Master", b"h\x01Big", b"p\x01Proportional", b"~\x010"):
        assert ibm(ESC + both) == standard(ESC + both)


def test_double_strike_is_not_nlq():
    assert ibm(ESC + b"GStrike") == standard(ESC + b"GStrike")


def test_fs_gives_the_standard_mode_commands_the_proprinter_took():
    assert ibm(FS + b"4Italic") == standard(ESC + b"4Italic")
    assert ibm(FS + b"\\\x0a\x00A") == standard(ESC + b"\\\x0a\x00A")
    assert text(FS + b"R\x02@") == "§"


def test_esc_m_is_elite_dropping_condensed():
    assert ibm(b"\x0f" + ESC + b"MElite") == standard(ESC + b"MElite")


def test_esc_3_0_is_ignored():
    assert ibm(ESC + b"3\x00A\nA") == standard(b"A\nA")


def test_switch_1_7_chooses_character_set_2_or_1():
    assert text(b"\x80") == "Ç"
    assert text(b"\x80A", graphics_table=True) == "A"


def test_esc_equals_defines_download_characters_with_the_ram_free():
    define = ESC + b"=\x0f\x00\x14A" + bytes([0, 0, 0x80] + [0] * 10)
    assert ibm(define + ESC + b"I\x04A") == ibm(b"A")
    defined = ibm(define + ESC + b"I\x04A", download_characters=True)
    assert defined != ibm(b"A") and len(defined[0]) == 1


def test_esc_equals_is_ignored_in_nlq():
    define = ESC + b"=\x0f\x00\x14A" + bytes([0, 0, 0x80] + [0] * 10)
    data = ESC + b"x\x01" + define + ESC + b"x\x00" + ESC + b"I\x04A"
    assert ibm(data, download_characters=True) == ibm(b"A")


def test_tabs_count_as_in_standard_mode():
    assert ibm(ESC + b"D\x05\x00\tA") == standard(ESC + b"D\x05\x00\tA")


def test_delete_removes_the_last_character():
    assert ibm(b"AB\x7f") == standard(b"A")


def test_the_lc10_colour_prints_in_colour_in_ibm_mode():
    pages = _pages(ESC + b"r\x01A", ibm_mode=True, model=StarLC10Colour)
    assert pages[0].ink_dots and not pages[0].dots


def test_esc_d_takes_at_most_28_stops():
    stops = bytes(range(1, 31)) + b"\x00"
    assert ibm(ESC + b"D" + stops + b"\t" * 29 + b"A") == standard(b" " * 28 + b"A")
