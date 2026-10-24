"""Stationery: the paper's own printing, perforations and feed holes."""

import pytest

from papyrium.core.page import inches
from papyrium.core.stationery import STATIONERY, Circle, Rectangle, stationery_named

WIDTH = inches(9) + inches(1) // 2
HEIGHT = inches(11)
HALF_INCH = inches(1) // 2


def test_plain_sheet_has_no_features():
    assert stationery_named("sheet").features(WIDTH, HEIGHT) == ()


def test_fanfold_has_a_feed_hole_every_half_inch_down_each_strip():
    holes = [
        f for f in stationery_named("fanfold").features(WIDTH, HEIGHT) if isinstance(f, Circle)
    ]
    assert len(holes) == 2 * 22
    centres = {(hole.x, hole.y) for hole in holes}
    assert (HALF_INCH // 2, HALF_INCH // 2) in centres
    assert (WIDTH - HALF_INCH // 2, HEIGHT - HALF_INCH // 2) in centres


def test_fanfold_perforates_the_strips_and_the_top_of_the_sheet():
    features = stationery_named("fanfold").features(WIDTH, HEIGHT)
    dashes = [f for f in features if isinstance(f, Rectangle)]
    assert any(dash.x == HALF_INCH and dash.width < dash.height for dash in dashes)
    assert any(dash.y == 0 and dash.width > dash.height for dash in dashes)


def test_green_bar_tints_alternate_half_inch_bands_between_the_strips():
    features = stationery_named("green-bar").features(WIDTH, HEIGHT)
    bands = [f for f in features if isinstance(f, Rectangle) and f.height == HALF_INCH]
    assert [band.y for band in bands] == [HALF_INCH * n for n in range(1, 22, 2)]
    assert {(band.x, band.width) for band in bands} == {(HALF_INCH, WIDTH - 2 * HALF_INCH)}
    (colour,) = {band.colour for band in bands}
    assert colour[1] > colour[0] and colour[1] > colour[2]


def test_music_ruled_rules_every_line_of_alternate_bands():
    features = stationery_named("music-ruled").features(WIDTH, HEIGHT)
    rules = [f for f in features if isinstance(f, Rectangle) and f.width == WIDTH - 2 * HALF_INCH]
    line = inches(1) // 6
    first_band = [rule.y for rule in rules if HALF_INCH <= rule.y <= 2 * HALF_INCH]
    assert first_band == [HALF_INCH + n * line for n in range(4)]


def test_every_kind_is_listed():
    assert set(STATIONERY) == {"sheet", "fanfold", "green-bar", "blue-bar", "music-ruled"}


def test_unknown_stationery_is_a_key_error():
    with pytest.raises(KeyError):
        stationery_named("papyrus")
