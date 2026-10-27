"""Golden replay: the demonstration page prints exactly the pinned page images.

Set PAPYRIUM_UPDATE_GOLDEN=1 to rewrite the images after an intended
change, then inspect them before committing.
"""

from pathlib import Path

from papyrium.model.star_lc10 import StarLC10
from papyrium.output.png.golden import check_golden_pages

GOLDEN_DIRPATH = Path(__file__).parent / "golden"


def test_demo_prints_the_golden_pages():
    interpreter = StarLC10(name="star-lc10").create_interpreter()
    pages = interpreter.feed(StarLC10(name="star-lc10").demo()) + interpreter.finish()
    check_golden_pages(pages, GOLDEN_DIRPATH, "demo")
