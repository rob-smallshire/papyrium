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
    (filepath,) = _write(tmp_path, [_letter(1, ((300, 600), (60, 120), (60, 120), (90, 120)))])
    content = PdfReader(filepath).pages[0].get_contents().get_data().decode("ascii")
    assert "1 J" in content
    assert "60 w" in content
    assert content.count(" m ") == 3
    # Rows in order down the page, each reached by a relative translation.
    assert "1 0 0 1 0 120 cm\n60 0 m 60 0 l\n90 0 m 90 0 l\nS" in content
    assert "1 0 0 1 0 480 cm\n300 0 m 300 0 l\nS" in content


def test_dense_pages_stay_small(tmp_path):
    dots = tuple((x, y) for y in range(0, 47520, 720) for x in range(1080, 35640, 36))
    (filepath,) = _write(tmp_path, [_letter(1, dots)])
    assert filepath.stat().st_size < 50_000


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


def _text_page(text, y=0):
    from papyrium.core.page import TextMark

    marks = tuple(
        TextMark(x=1080 + 432 * index, y=y, width=432, height=540, character=character)
        for index, character in enumerate(text)
    )
    return Page(number=1, width=36720, height=47520, dot_diameter=60, dots=((60, 60),), text=marks)


def test_text_layer_makes_the_page_searchable(tmp_path):
    (filepath,) = _write(tmp_path, [_text_page("HELLO (1) \\ " + chr(0x00A3) + "9")])
    extracted = PdfReader(filepath).pages[0].extract_text()
    assert "HELLO (1) \\ " + chr(0x00A3) + "9" in extracted


def test_text_layer_is_invisible(tmp_path):
    (filepath,) = _write(tmp_path, [_text_page("HELLO")])
    content = PdfReader(filepath).pages[0].get_contents().get_data().decode("ascii")
    assert "3 Tr" in content


def test_text_layer_can_be_switched_off(tmp_path):
    (filepath,) = _write(tmp_path, [_text_page("HELLO")], text=False)
    assert "HELLO" not in PdfReader(filepath).pages[0].extract_text()


def test_dots_are_scaled_exactly_to_points(tmp_path):
    (filepath,) = _write(tmp_path, [_letter(1, ((60, 60),))])
    content = PdfReader(filepath).pages[0].get_contents().get_data().decode("ascii")
    scale = content.splitlines()[1].split()[0]
    assert abs(float(scale) * 47520 - 792) < 1e-4
