"""Golden pages: a job's pages compared, pixel for pixel, with pinned images.

For printer models' tests. Set PAPYRIUM_UPDATE_GOLDEN=1 to rewrite the
images after an intended change, then look at them before committing.
"""

from __future__ import annotations

import os
from collections.abc import Sequence
from pathlib import Path

from PIL import Image

from papyrium.core.page import Page
from papyrium.output.png import PngOutput

#: Low enough to keep the images small, high enough to resolve every dot.
GOLDEN_DPI = 120


def updating() -> bool:
    """Whether golden images are being rewritten rather than compared."""
    return os.environ.get("PAPYRIUM_UPDATE_GOLDEN") == "1"


def check_golden_pages(pages: Sequence[Page], golden_dirpath: Path, stem: str) -> None:
    """Assert *pages* print exactly as *stem*-page-N.png in *golden_dirpath*.

    When :func:`updating`, rewrite those images instead.
    """
    output = PngOutput(name="png", dpi=GOLDEN_DPI)
    images = [output.render(page) for page in pages]
    golden_filepaths = sorted(golden_dirpath.glob(f"{stem}-page-*.png"))
    if updating():
        for filepath in golden_filepaths:
            filepath.unlink()
        for number, image in enumerate(images, start=1):
            image.save(golden_dirpath / f"{stem}-page-{number}.png")
        return
    assert len(images) == len(golden_filepaths), stem
    for image, golden_filepath in zip(images, golden_filepaths):
        with Image.open(golden_filepath) as golden:
            assert image.size == golden.size, golden_filepath.name
            assert image.mode == golden.mode, golden_filepath.name
            assert image.tobytes() == golden.tobytes(), golden_filepath.name
