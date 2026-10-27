"""Golden replay: the demonstration page prints exactly the pinned page images.

Set PAPYRIUM_UPDATE_GOLDEN=1 to rewrite the images after an intended
change, then inspect them before committing.
"""

from pathlib import Path

from papyrium.model.ibm_proprinter_ii import IBMProprinterII
from papyrium.output.png.golden import check_golden_pages

GOLDEN_DIRPATH = Path(__file__).parent / "golden"


def test_demo_prints_the_golden_pages():
    model = IBMProprinterII(name="ibm-proprinter-ii")
    interpreter = model.create_interpreter()
    pages = interpreter.feed(model.demo()) + interpreter.finish()
    check_golden_pages(pages, GOLDEN_DIRPATH, "demo")
