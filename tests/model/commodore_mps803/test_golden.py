"""Golden replay: the demonstration page prints exactly its pinned images.

Set PAPYRIUM_UPDATE_GOLDEN=1 to rewrite the images after an intended
change, then inspect them before committing.
"""

from pathlib import Path

from papyrium.model.commodore_mps803 import CommodoreMps803
from papyrium.output.png.golden import check_golden_pages

GOLDEN_DIRPATH = Path(__file__).parent / "golden"


def test_demo_prints_the_golden_pages():
    model = CommodoreMps803(name="commodore-mps-803")
    interpreter = model.create_interpreter()
    check_golden_pages(
        interpreter.feed(model.demo()) + interpreter.finish(), GOLDEN_DIRPATH, "demo"
    )
