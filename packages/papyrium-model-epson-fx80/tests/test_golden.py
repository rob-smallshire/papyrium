"""Golden replay: each capture in golden/ prints exactly the pinned page images.

Set PAPYRIUM_UPDATE_GOLDEN=1 to rewrite the images after an intended
change, then inspect them before committing.
"""

import os
from pathlib import Path

import pytest
from PIL import Image

from papyrium.model.epson_fx80 import EpsonFx80
from papyrium.output.png import PngOutput

GOLDEN_DIRPATH = Path(__file__).parent / "golden"
CAPTURE_FILEPATHS = sorted(GOLDEN_DIRPATH.glob("*.prn"))
UPDATE = os.environ.get("PAPYRIUM_UPDATE_GOLDEN") == "1"

#: Low enough to keep the images small, high enough to resolve every dot.
GOLDEN_DPI = 120


def _render(capture_filepath):
    interpreter = EpsonFx80(name="epson-fx80").create_interpreter()
    pages = interpreter.feed(capture_filepath.read_bytes()) + interpreter.finish()
    output = PngOutput(name="png", dpi=GOLDEN_DPI)
    return [output.render(page) for page in pages]


@pytest.mark.parametrize("capture_filepath", CAPTURE_FILEPATHS, ids=lambda path: path.stem)
def test_capture_prints_the_golden_pages(capture_filepath):
    images = _render(capture_filepath)
    golden_filepaths = sorted(GOLDEN_DIRPATH.glob(f"{capture_filepath.stem}-page-*.png"))
    if UPDATE:
        for filepath in golden_filepaths:
            filepath.unlink()
        for number, image in enumerate(images, start=1):
            image.save(GOLDEN_DIRPATH / f"{capture_filepath.stem}-page-{number}.png")
        return
    assert len(images) == len(golden_filepaths)
    for image, golden_filepath in zip(images, golden_filepaths):
        with Image.open(golden_filepath) as golden:
            assert image.size == golden.size, golden_filepath.name
            assert image.mode == golden.mode, golden_filepath.name
            assert image.tobytes() == golden.tobytes(), golden_filepath.name


def test_there_are_golden_captures():
    assert len(CAPTURE_FILEPATHS) >= 5
