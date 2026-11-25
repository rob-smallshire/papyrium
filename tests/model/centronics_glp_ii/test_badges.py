"""The GLP II's other badges: the Brother M-1109, Sony PRN-M09 and RCA VP2100.

The Great Little Printer II (Centronics Model 3102) was also sold under
these names. They print exactly as the GLP II does and name themselves by
their own badges.
"""

import pytest

from papyrium.core.conformance import PrinterModelConformance
from papyrium.core.instance import default_printer_name
from papyrium.extension import create_extension, namespace_for
from papyrium.model.centronics_glp_ii import BrotherM1109, CentronicsGlpIi, RcaVp2100, SonyPrnM09

BADGES = [
    ("brother-m1109", BrotherM1109, "Brother M-1109"),
    ("sony-prn-m09", SonyPrnM09, "Sony PRN-M09"),
    ("rca-vp2100", RcaVp2100, "RCA VP2100"),
]


class TestBrotherM1109Conformance(PrinterModelConformance):
    def make_model(self):
        return BrotherM1109(name="brother-m1109")

    def sample_job(self):
        return b"GREAT LITTLE PRINTER\r\n\x0cSECOND PAGE\r\n"


@pytest.mark.parametrize(("name", "model_class", "display_name"), BADGES)
def test_is_registered_on_the_model_axis(name, model_class, display_name):
    model = create_extension("model", namespace_for("model"), name)
    assert type(model) is model_class


@pytest.mark.parametrize(("name", "model_class", "display_name"), BADGES)
def test_names_itself_by_its_own_badge(name, model_class, display_name):
    model = model_class(name=name)
    assert model.identity().display_name == display_name
    assert default_printer_name(model.identity()) == f"{display_name} (Papyrium)"


@pytest.mark.parametrize(("name", "model_class", "display_name"), BADGES)
def test_is_the_glp_ii_under_another_name(name, model_class, display_name):
    assert model_class.rebadge_of is CentronicsGlpIi
    assert model_class(name=name).languages() == ("escp",)


@pytest.mark.parametrize(("name", "model_class", "display_name"), BADGES)
def test_prints_the_glp_ii_demonstration_exactly(name, model_class, display_name):
    options = {"near-letter-quality": "yes", "stationery": "fanfold"}
    rebadge = model_class.from_config(name=name, config=options)
    original = CentronicsGlpIi.from_config(name="centronics-glp-ii", config=options)
    rebadge_interpreter = rebadge.create_interpreter()
    original_interpreter = original.create_interpreter()
    job = original.demo()
    assert rebadge.demo() == job
    assert rebadge_interpreter.feed(job) + rebadge_interpreter.finish() == (
        original_interpreter.feed(job) + original_interpreter.finish()
    )
