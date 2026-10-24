"""The options shared by ESC/P printer models."""

import pytest

from papyrium.core.page import inches
from papyrium.exception import ConfigurationError
from papyrium.language.escp.options import nine_row_font, paper_options

FONT_TEXT = "rows 9\ncolumns 11\nU+0041\n" + "...........\n" * 9


def test_an_installed_font_by_name():
    assert nine_row_font("draft-9").name == "draft-9"


def test_a_font_file_by_path(tmp_path):
    font_filepath = tmp_path / "rom.txt"
    font_filepath.write_text(FONT_TEXT)
    font = nine_row_font(str(font_filepath))
    assert font.characters() == frozenset({"A"})


def test_a_missing_font_file_is_a_configuration_error(tmp_path):
    with pytest.raises(ConfigurationError, match="nothing.txt"):
        nine_row_font(str(tmp_path / "nothing.txt"))


def test_an_nlq_font_must_be_18_rows_by_24_columns(tmp_path):
    from papyrium.language.escp.options import nlq_font

    with pytest.raises(ConfigurationError, match="18 x 24"):
        nlq_font("draft-9")
    font_filepath = tmp_path / "nlq.txt"
    font_filepath.write_text("rows 18\ncolumns 24\n")
    assert nlq_font(str(font_filepath)).rows == 18


def _paper(**options):
    settings = {"paper_width": None, "form_length": "11", "top_offset": "1/2"}
    return paper_options(**(settings | options))


def test_paper_width_follows_the_stationery_unless_given():
    assert _paper(stationery="sheet")["paper_width"] == inches(8) + inches(1) // 2
    assert _paper(stationery="fanfold")["paper_width"] == inches(9) + inches(1) // 2
    assert _paper(stationery="fanfold", paper_width="10")["paper_width"] == inches(10)


def test_a_line_reaching_the_tear_off_strips_is_logged(caplog):
    _paper(stationery="green-bar", paper_width="8.5")
    assert "tear-off strips" in caplog.text


def test_a_line_between_the_strips_is_not_logged(caplog):
    _paper(stationery="green-bar")
    _paper(stationery="sheet", paper_width="8.5")
    assert caplog.text == ""
