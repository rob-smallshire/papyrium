"""StarLC10Colour: the LC-10 with a colour ribbon and embedded commands."""

from papyrium.core.conformance import PrinterModelConformance
from papyrium.core.page import Ink
from papyrium.extension import create_extension, namespace_for
from papyrium.model.star_lc10 import StarLC10, StarLC10Colour

SAMPLE_JOB = (
    b"\x1b@Star LC-10 Colour\r\n\x1br\x02Blue\x1br\x00\r\n((C))6Green\r\n\x0cSecond page\r\n\x0c"
)


class TestStarLC10ColourConformance(PrinterModelConformance):
    def make_model(self):
        return StarLC10Colour(name="star-lc10-colour")

    def sample_job(self):
        return SAMPLE_JOB


def _print(model, data):
    interpreter = model.create_interpreter()
    return interpreter.feed(data) + interpreter.finish()


def test_is_registered_on_the_model_axis():
    model = create_extension("model", namespace_for("model"), "star-lc10-colour")
    assert isinstance(model, StarLC10Colour)
    assert model.identity().display_name == "Star LC-10 Colour"


def test_prints_in_colour_and_obeys_embedded_commands():
    page, _ = _print(StarLC10Colour(name="star-lc10-colour"), SAMPLE_JOB)
    assert {inked.ink for inked in page.ink_dots} == {Ink.CYAN, Ink.YELLOW}


def test_the_plain_lc10_has_a_black_ribbon_and_only_the_sheet_feeders_commands():
    mechanism = StarLC10(name="star-lc10").mechanism
    assert not mechanism.colour_ribbon
    assert mechanism.embedded_commands == frozenset("04RT")
    page, _ = _print(StarLC10(name="star-lc10"), SAMPLE_JOB)
    assert page.ink_dots == ()
