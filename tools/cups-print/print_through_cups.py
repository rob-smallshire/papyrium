"""Print a test page through a CUPS printer driver to Papyrium.

The test page (test_page.py) goes through the driver of a CUPS queue,
such as one added with

    sudo lpadmin -p FX80 -D "Epson FX-80" -E -v socket://localhost:9100 \\
        -m drv:///sample.drv/epson9.ppd

and the bytes the driver makes are printed by Papyrium, so what the
driver sends, and how Papyrium prints it, can be seen together.

By default the page goes through the driver with cupsfilter, which
needs no running printer and makes the same bytes every time; the
capture and pages are written to the output directory. With --queue it
is printed with lp to the queue itself, which sends it on to a running
`papyrium serve`, and the job appears among that printer's jobs.

Run from the repository root:

    uv run python tools/cups-print/print_through_cups.py
    uv run python tools/cups-print/print_through_cups.py --resolution 240x72dpi
    uv run python tools/cups-print/print_through_cups.py --model epson-lx800
    uv run python tools/cups-print/print_through_cups.py --queue
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import click

sys.path.insert(0, str(Path(__file__).parent))
from test_page import test_page_pdf  # noqa: E402


@click.command()
@click.option(
    "--printer",
    "printer_name",
    default="FX80",
    show_default=True,
    help="The CUPS queue whose driver to use.",
)
@click.option(
    "--resolution", help="The driver's resolution, such as 60x72dpi, 120x72dpi or 240x72dpi."
)
@click.option("--page-size", default="Letter", show_default=True, help="The driver's page size.")
@click.option(
    "--queue", is_flag=True, help="Print with lp to the queue, and on to a running papyrium serve."
)
@click.option(
    "--model",
    default="epson-fx80",
    show_default=True,
    help="The Papyrium printer model to print the capture.",
)
@click.option(
    "--output-dirpath",
    type=click.Path(file_okay=False, path_type=Path),
    default=Path("cups-print-output"),
    show_default=True,
    help="Where the PDF, capture and pages go (not with --queue).",
)
def main(printer_name, resolution, page_size, queue, model, output_dirpath):
    """Print a test page through a CUPS printer driver to Papyrium."""
    output_dirpath.mkdir(parents=True, exist_ok=True)
    pdf_filepath = output_dirpath / "test-page.pdf"
    pdf_filepath.write_bytes(test_page_pdf())
    options = ["-o", f"PageSize={page_size}"]
    if resolution:
        options += ["-o", f"Resolution={resolution}"]

    if queue:
        subprocess.run(["lp", "-d", printer_name, *options, str(pdf_filepath)], check=True)
        click.echo(
            f"Sent {pdf_filepath} to {printer_name}; the job appears among papyrium serve's jobs."
        )
        return

    ppd_filepath = Path("/etc/cups/ppd") / f"{printer_name}.ppd"
    if not ppd_filepath.exists():
        raise click.ClickException(f"No PPD for the queue {printer_name!r} at {ppd_filepath}")
    # cupsfilter rasterises the PDF as the queue would; the driver's own
    # filter, named in the PPD, turns the raster into the printer's bytes.
    raster_filepath = output_dirpath / "test-page.ras"
    with raster_filepath.open("wb") as raster:
        _run(
            [
                "cupsfilter",
                "-P",
                str(ppd_filepath),
                "-m",
                "application/vnd.cups-raster",
                *options,
                str(pdf_filepath),
            ],
            stdout=raster,
        )
    capture_filepath = output_dirpath / "capture.prn"
    filter_filepath = _driver_filter_filepath(ppd_filepath)
    option_text = " ".join(options[1::2])
    with capture_filepath.open("wb") as capture:
        _run(
            [
                str(filter_filepath),
                "1",
                "papyrium",
                "test-page",
                "1",
                option_text,
                str(raster_filepath),
            ],
            stdout=capture,
            env={**os.environ, "PPD": str(ppd_filepath)},
        )
    click.echo(f"The driver made {capture_filepath.stat().st_size} bytes: {capture_filepath}")
    pages_dirpath = output_dirpath / model
    subprocess.run(
        [
            "papyrium",
            "render",
            str(capture_filepath),
            "--model",
            model,
            "-M",
            "stationery=sheet",
            "--output-dir",
            str(pages_dirpath),
        ],
        check=True,
    )
    click.echo(f"Pages: {pages_dirpath}")


def _run(command, **kwargs):
    result = subprocess.run(command, stderr=subprocess.PIPE, text=False, **kwargs)
    if result.returncode != 0:
        raise click.ClickException(
            f"{command[0]} failed:\n{result.stderr.decode(errors='replace')}"
        )


def _driver_filter_filepath(ppd_filepath: Path) -> Path:
    """The filter the PPD names for CUPS raster, in CUPS's filter directory."""
    for line in ppd_filepath.read_text(errors="replace").splitlines():
        if line.startswith("*cupsFilter:") and "application/vnd.cups-raster" in line:
            name = line.split('"')[1].split()[-1]
            return Path("/usr/libexec/cups/filter") / name
    raise click.ClickException(f"{ppd_filepath} names no filter for CUPS raster")


if __name__ == "__main__":
    main()
