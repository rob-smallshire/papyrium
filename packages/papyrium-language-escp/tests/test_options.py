"""The options shared by ESC/P printer models."""

import pytest

from papyrium.exception import ConfigurationError
from papyrium.language.escp.options import nine_row_font

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
