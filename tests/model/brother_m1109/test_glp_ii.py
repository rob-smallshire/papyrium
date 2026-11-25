"""The M-1109's other badges: the Centronics GLP II and its other names.

The Great Little Printer II (Centronics model 3102) was sold as the
Brother M-1109, the Sony PRN-M09 and the RCA VP2100. They print exactly as
the M-1109 does and name themselves by their own badges.
"""

import pytest

from papyrium.core.conformance import PrinterModelConformance
from papyrium.core.instance import default_printer_name
from papyrium.extension import create_extension, namespace_for
from papyrium.model.brother_m1109 import BrotherM1109, CentronicsGlpIi, RcaVp2100, SonyPrnM09

BADGES = [
    ("centronics-glp-ii", CentronicsGlpIi, "Centronics GLP II"),
    ("sony-prn-m09", SonyPrnM09, "Sony PRN-M09"),
    ("rca-vp2100", RcaVp2100, "RCA VP2100"),
]


class TestCentronicsGlpIiConformance(PrinterModelConformance):
    def make_model(self):
        return CentronicsGlpIi(name="centronics-glp-ii")

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
def test_is_the_m1109_under_another_name(name, model_class, display_name):
    assert model_class.rebadge_of is BrotherM1109
    assert model_class(name=name).languages() == ("escp",)


@pytest.mark.parametrize(("name", "model_class", "display_name"), BADGES)
def test_prints_the_m1109_demonstration_exactly(name, model_class, display_name):
    options = {"near-letter-quality": "yes", "stationery": "fanfold"}
    rebadge = model_class.from_config(name=name, config=options)
    original = BrotherM1109.from_config(name="brother-m1109", config=options)
    rebadge_interpreter = rebadge.create_interpreter()
    original_interpreter = original.create_interpreter()
    job = original.demo()
    assert rebadge.demo() == job
    assert rebadge_interpreter.feed(job) + rebadge_interpreter.finish() == (
        original_interpreter.feed(job) + original_interpreter.finish()
    )
