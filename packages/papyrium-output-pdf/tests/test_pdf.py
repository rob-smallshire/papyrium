"""PdfOutput: a job's pages as one PDF of vector dots."""

import zlib

import pytest
from pypdf import PdfReader

from papyrium.core.conformance import OutputConformance
from papyrium.core.page import Page, inches
from papyrium.extension import create_extension, namespace_for
from papyrium.output.pdf import PdfOutput


class TestPdfConformance(OutputConformance):
    def make_output(self):
        return PdfOutput(name="pdf")


def _letter(number, dots=()):
    return Page(
        number=number,
        width=inches(8) + inches(1) // 2,
        height=inches(11),
        dot_diameter=60,
        dots=dots,
    )


def _write(tmp_path, pages, **options):
    document = PdfOutput(name="pdf", **options).open_document(tmp_path)
    for page in pages:
        document.add_page(page)
    return document.close()


def test_is_registered_on_the_output_axis():
    assert isinstance(create_extension("output", namespace_for("output"), "pdf"), PdfOutput)


def test_one_document_for_the_whole_job(tmp_path):
    (filepath,) = _write(tmp_path, [_letter(1, ((60, 60),)), _letter(2)])
    assert filepath.name == "job.pdf"
    reader = PdfReader(filepath)
    assert len(reader.pages) == 2


def test_pages_are_the_paper_size_in_points(tmp_path):
    (filepath,) = _write(tmp_path, [_letter(1)])
    box = PdfReader(filepath).pages[0].mediabox
    assert (float(box.width), float(box.height)) == (612.0, 792.0)


def test_each_distinct_dot_is_one_degenerate_round_capped_stroke(tmp_path):
    (filepath,) = _write(tmp_path, [_letter(1, ((60, 120), (60, 120), (300, 600)))])
    content = PdfReader(filepath).pages[0].get_contents().get_data().decode("ascii")
    assert "1 J" in content
    assert "60 w" in content
    assert content.count(" m ") == 2
    assert "60 120 m 60 120 l" in content
    assert "300 600 m 300 600 l" in content


def test_filename_option(tmp_path):
    (filepath,) = _write(tmp_path, [_letter(1)], filename="out.pdf")
    assert filepath.name == "out.pdf"


def test_page_size_that_is_not_whole_points(tmp_path):
    page = Page(number=1, width=100, height=90, dot_diameter=6)
    (filepath,) = _write(tmp_path, [page])
    box = PdfReader(filepath).pages[0].mediabox
    assert float(box.width) == pytest.approx(100 / 60, abs=1e-4)


def test_no_temporary_files_are_left_behind(tmp_path):
    _write(tmp_path, [_letter(1)])
    assert [path.name for path in tmp_path.iterdir()] == ["job.pdf"]
