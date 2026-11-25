"""Golden replay: each model's demonstration page prints exactly its pinned page images.

Set PAPYRIUM_UPDATE_GOLDEN=1 to rewrite the images after an intended
change, then inspect them before committing.
"""

from pathlib import Path

import pytest

from papyrium.model.centronics_glp import BrotherM1009, CentronicsGlp, SchneiderNlq401
from papyrium.output.png.golden import check_golden_pages

GOLDEN_DIRPATH = Path(__file__).parent / "golden"


@pytest.mark.parametrize(
    ("stem", "model_class"),
    [("glp-demo", CentronicsGlp), ("nlq401-demo", SchneiderNlq401), ("m1009-demo", BrotherM1009)],
)
def test_demo_prints_the_golden_pages(stem, model_class):
    model = model_class(name=stem)
    interpreter = model.create_interpreter()
    check_golden_pages(interpreter.feed(model.demo()) + interpreter.finish(), GOLDEN_DIRPATH, stem)
