"""PngOutput: pages as greyscale raster images."""

from PIL import Image

from papyrium.core.conformance import OutputConformance
from papyrium.core.page import Page, inches
from papyrium.extension import create_extension, namespace_for
from papyrium.output.png import PngOutput


class TestPngConformance(OutputConformance):
    def make_output(self):
        return PngOutput(name="png")


def _page(dots, dot_diameter=60):
    return Page(number=1, width=inches(2), height=inches(1), dot_diameter=dot_diameter, dots=dots)


def _render(tmp_path, page, **options):
    document = PngOutput(name="png", **options).open_document(tmp_path)
    document.add_page(page)
    (filepath,) = document.close()
    return filepath


def test_is_registered_on_the_output_axis():
    assert isinstance(create_extension("output", namespace_for("output"), "png"), PngOutput)


def test_image_size_follows_page_size_and_dpi(tmp_path):
    with Image.open(_render(tmp_path, _page(()), dpi=100)) as image:
        assert image.size == (200, 100)
        assert image.mode == "L"
        assert round(image.info["dpi"][0]) == 100


def test_files_are_numbered_by_page(tmp_path):
    document = PngOutput(name="png").open_document(tmp_path)
    for number in (1, 2):
        document.add_page(Page(number=number, width=432, height=432, dot_diameter=60))
    assert [path.name for path in document.close()] == ["page-0001.png", "page-0002.png"]


def test_a_dot_is_ink_at_its_centre_and_paper_beyond_its_radius(tmp_path):
    # At 360 dpi a unit is 1/12 pixel; a 60-unit dot is 5 pixels across.
    centre = (inches(1), inches(1) // 2)
    with Image.open(_render(tmp_path, _page((centre,)), ink=0, paper=255)) as image:
        cx, cy = 360, 180
        assert image.getpixel((cx, cy)) == 0
        assert image.getpixel((cx + 4, cy)) == 255
        assert image.getpixel((cx, cy - 4)) == 255


def test_blank_page_is_all_paper(tmp_path):
    with Image.open(_render(tmp_path, _page(()), paper=250)) as image:
        assert image.getextrema() == (250, 250)


def test_no_temporary_files_are_left_behind(tmp_path):
    _render(tmp_path, _page(()))
    assert [path.name for path in tmp_path.iterdir()] == ["page-0001.png"]


def test_stationery_is_drawn_in_colour_under_the_dots(tmp_path):
    from papyrium.core.stationery import GREEN_BAND, HOLE_COLOUR, stationery_named

    page = Page(
        number=1,
        width=inches(9) + inches(1) // 2,
        height=inches(2),
        dot_diameter=60,
        dots=((inches(4), inches(3) // 4),),
        stationery=stationery_named("green-bar"),
    )
    with Image.open(_render(tmp_path, page, dpi=72, ink=0, paper=255)) as image:
        assert image.mode == "RGB"
        # The first green band runs from 1/2 to 1 inch down; the dot is in it.
        assert image.getpixel((200, 50)) == GREEN_BAND
        assert image.getpixel((inches(4) * 72 // 4320, 54)) == (0, 0, 0)
        assert image.getpixel((200, 20)) == (255, 255, 255)
        # A feed hole is centred 1/4 inch in from the edge.
        assert image.getpixel((18, 18)) == HOLE_COLOUR
