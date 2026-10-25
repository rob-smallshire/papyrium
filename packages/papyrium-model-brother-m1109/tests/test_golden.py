"""Golden replay: each capture in golden/, and the demonstration page, print
exactly the pinned page images.

Set PAPYRIUM_UPDATE_GOLDEN=1 to rewrite the images after an intended
change, then inspect them before committing.
"""

from pathlib import Path

import pytest

from papyrium.model.brother_m1109 import BrotherM1109
from papyrium.output.png.golden import check_golden_pages

GOLDEN_DIRPATH = Path(__file__).parent / "golden"
CAPTURE_FILEPATHS = sorted(GOLDEN_DIRPATH.glob("*.prn"))


def _print(data):
    interpreter = BrotherM1109(name="brother-m1109").create_interpreter()
    return interpreter.feed(data) + interpreter.finish()


@pytest.mark.parametrize("capture_filepath", CAPTURE_FILEPATHS, ids=lambda path: path.stem)
def test_capture_prints_the_golden_pages(capture_filepath):
    check_golden_pages(_print(capture_filepath.read_bytes()), GOLDEN_DIRPATH, capture_filepath.stem)


def test_demo_prints_the_golden_pages():
    check_golden_pages(_print(BrotherM1109(name="brother-m1109").demo()), GOLDEN_DIRPATH, "demo")


def test_there_are_golden_captures():
    assert len(CAPTURE_FILEPATHS) >= 1
