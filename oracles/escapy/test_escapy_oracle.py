"""EscaPy as a test oracle for Papyrium's ESC/P interpretation.

EscaPy (PyPI ``pyscape``, AGPL-3.0) is an independent ESC/P interpreter.
It is run here as a separate program through ``uvx``, never imported and
never distributed, and only its output is examined. Not part of the
default suite; run from the repository root with::

    uv run pytest oracles/escapy

EscaPy draws text with outline fonts on A4 with margins, so pages cannot be
compared pixel for pixel. What is compared is content: the text printed on
each page, in printing order, with whitespace ignored, which checks
character sets, page breaks and which bytes print at all. Known
divergences are marked as expected failures with the reason.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest
from pypdf import PdfReader

from papyrium.model.epson_fx80 import EpsonFx80

ESCAPY_REQUIREMENT = "pyscape==1.1.1"

GOLDEN_DIRPATH = (
    Path(__file__).parents[2] / "packages" / "papyrium-model-epson-fx80" / "tests" / "golden"
)

KNOWN_DIVERGENCES = {
    "pages-and-layout": (
        "EscaPy 1.1.1 does not implement DEL or CAN, which edit the FX-80's line buffer"
    ),
}

pytestmark = pytest.mark.skipif(shutil.which("uvx") is None, reason="needs uvx to run EscaPy")


def _comparable(text: str) -> str:
    """Text with whitespace removed and characters outside Windows-1252 dropped.

    EscaPy prints a box for characters its fonts lack, such as the peseta sign.
    """
    text = re.sub(r"\s+", "", text)
    return "".join(c for c in text if c.encode("cp1252", errors="ignore"))


def _papyrium_pages(capture_filepath: Path) -> list[str]:
    interpreter = EpsonFx80(name="epson-fx80").create_interpreter()
    pages = interpreter.feed(capture_filepath.read_bytes()) + interpreter.finish()
    return [_comparable("".join(mark.character for mark in page.text)) for page in pages]


def _escapy_pages(capture_filepath: Path, output_dirpath: Path) -> list[str]:
    pdf_filepath = output_dirpath / f"{capture_filepath.stem}.pdf"
    subprocess.run(
        [
            "uvx",
            "--from",
            ESCAPY_REQUIREMENT,
            "escapy",
            "--pins",
            "9",
            "--no-single_sheets",
            "-o",
            str(pdf_filepath),
            str(capture_filepath),
        ],
        check=True,
        capture_output=True,
        timeout=300,
    )
    pages = [_comparable(page.extract_text()) for page in PdfReader(pdf_filepath).pages]
    # EscaPy starts a new, blank page after a trailing form feed; a real
    # printer ejects one sheet and prints nothing on the next.
    while pages and not pages[-1]:
        pages.pop()
    return pages


def _cases():
    for capture_filepath in sorted(GOLDEN_DIRPATH.glob("*.prn")):
        reason = KNOWN_DIVERGENCES.get(capture_filepath.stem)
        marks = [pytest.mark.xfail(reason=reason, strict=True)] if reason else []
        yield pytest.param(capture_filepath, id=capture_filepath.stem, marks=marks)


@pytest.mark.parametrize("capture_filepath", list(_cases()))
def test_pages_print_the_same_text_as_escapy(capture_filepath, tmp_path):
    assert _papyrium_pages(capture_filepath) == _escapy_pages(capture_filepath, tmp_path)
