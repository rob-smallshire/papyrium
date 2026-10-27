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


def test_each_distinct_dot_is_one_placement_of_a_dot_form(tmp_path):
    (filepath,) = _write(tmp_path, [_letter(1, ((300, 600), (60, 120), (60, 120), (90, 120)))])
    content = PdfReader(filepath).pages[0].get_contents().get_data().decode("ascii")
    assert content.count("/D Do") == 3
    # Rows in order down the page; within a row, each dot is reached by a
    # relative translation from the one before.
    assert "q\n1 0 0 1 60 120 cm\n/D Do\n1 0 0 1 30 0 cm\n/D Do\nQ" in content
    assert "q\n1 0 0 1 300 600 cm\n/D Do\nQ" in content


def test_the_dot_is_a_filled_circle_the_diameter_of_a_printed_dot(tmp_path):
    # A filled path, not a zero-length stroke, which some renderers drop at
    # small scales and so draw thumbnails blank.
    (filepath,) = _write(tmp_path, [_letter(1, ((60, 60),))])
    form = PdfReader(filepath).pages[0]["/Resources"]["/XObject"]["/D"].get_object()
    assert form["/Subtype"] == "/Form"
    assert [float(value) for value in form["/BBox"]] == [-30, -30, 30, 30]
    drawing = form.get_data().decode("ascii")
    assert drawing.startswith("30 0 m") and drawing.count(" c") == 4
    assert drawing.rstrip().endswith("f")


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


def test_text_cells_are_as_tall_as_the_printed_cell(tmp_path):
    # Viewers size selection boxes from the font's ascent and descent, which
    # are set so that a box covers the whole cell, baseline at 7/9 of it.
    (filepath,) = _write(tmp_path, [_text_page("HELLO")])
    font = PdfReader(filepath).pages[0]["/Resources"]["/Font"]["/F1"].get_object()
    descriptor = font["/FontDescriptor"].get_object()
    assert (descriptor["/Ascent"], descriptor["/Descent"]) == (778, -222)
    assert (font["/FirstChar"], font["/LastChar"]) == (32, 255)
    assert set(font["/Widths"]) == {600}


def test_stationery_is_drawn_under_the_dots(tmp_path):
    from papyrium.core.stationery import stationery_named

    page = Page(
        number=1,
        width=inches(9) + inches(1) // 2,
        height=inches(11),
        dot_diameter=60,
        dots=((inches(4), inches(1)),),
        stationery=stationery_named("green-bar"),
    )
    (filepath,) = _write(tmp_path, [page])
    content = PdfReader(filepath).pages[0].get_contents().get_data().decode("ascii")
    band = content.index("2160 2160 36720 2160 re")
    assert content.index(" rg", band - 40) < band < content.index("/D Do")


def test_inked_dots_are_filled_in_their_ink_and_multiplied(tmp_path):
    from papyrium.core.page import Ink, InkDots

    page = Page(
        number=1, width=inches(8), height=inches(11), dot_diameter=60,
        ink_dots=(InkDots(Ink.MAGENTA, ((60, 60),)),),
    )  # fmt: skip
    (filepath,) = _write(tmp_path, [page])
    pdf_page = PdfReader(filepath).pages[0]
    content = pdf_page.get_contents().get_data().decode("ascii")
    assert "/M gs" in content and " rg" in content and content.count("/D Do") == 1
    assert pdf_page["/Resources"]["/ExtGState"]["/M"]["/BM"] == "/Multiply"
