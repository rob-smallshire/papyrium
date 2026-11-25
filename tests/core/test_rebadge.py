"""rebadged(): a printer model sold under another maker's or model's name."""

import pytest

from papyrium.core.model import ModelIdentity, PrinterModel, rebadged
from papyrium.core.testing import ByteDotModel

Rebadge = rebadged(ByteDotModel, manufacturer="Acme", model="Dotter 9")


def test_names_itself_by_its_own_badge():
    assert Rebadge(name="r").identity() == ModelIdentity(manufacturer="Acme", model="Dotter 9")


def test_is_a_printer_model_of_its_own_class():
    assert issubclass(Rebadge, ByteDotModel)
    assert issubclass(Rebadge, PrinterModel)
    assert Rebadge.__name__ == "AcmeDotter9"


def test_records_the_model_it_rebadges():
    assert Rebadge.rebadge_of is ByteDotModel
    assert ByteDotModel.rebadge_of is None


def test_prints_exactly_as_the_original():
    job = b"ABC\x0cDE"
    original = ByteDotModel(name="o").create_interpreter()
    rebadge = Rebadge(name="r").create_interpreter()
    assert rebadge.feed(job) + rebadge.finish() == original.feed(job) + original.finish()


def test_takes_the_original_options():
    model = Rebadge.from_config(name="r", config={"width": "32"})
    assert model.config == {"width": "32"}


def test_describes_itself_as_the_original_under_another_name():
    first_line = Rebadge.__doc__.strip().splitlines()[0]
    assert first_line == "Acme Dotter 9: the Papyrium Byte Dot sold under another name."


def test_rejects_a_badge_that_cannot_name_a_printer():
    with pytest.raises(ValueError, match="model"):
        rebadged(ByteDotModel, manufacturer="Acme", model="Bad;Name")
