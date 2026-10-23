"""The ``papyrium`` command: run a virtual vintage printer and inspect its jobs."""

from __future__ import annotations

import asyncio
import contextlib
import logging
import signal
from datetime import datetime
from pathlib import Path

import click
from asyoulikeit import ByAudience, Report, Reports, TableContent
from asyoulikeit.cli import (
    describe_formatter_command,
    describe_report_command,
    list_formatters_command,
    list_reports_command,
    report_output,
)

from papyrium.cli.help import use_plain_help
from papyrium.cli.plugins import (
    AXES,
    MODELS,
    TRANSPORTS,
    Axis,
    create_outputs,
    parse_options,
    parse_output_options,
)
from papyrium.core.jobs import CAPTURE_FILENAME, JOB_RECORD_FILENAME, JobRecord, JobStore
from papyrium.core.rendering import JobRenderer, JobRendering
from papyrium.core.spooler import Spooler
from papyrium.core.transport import Transport
from papyrium.exception import ConfigurationError, DataError, handled_errors
from papyrium.extension import describe_extension

__version__ = "0.0.0"

__all__ = ["cli"]

_DEFAULT_TRANSPORT_NAME = "raw-tcp"
_DEFAULT_MODEL_NAME = "epson-fx80"
_DEFAULT_OUTPUT_NAMES = ("png", "pdf")
_DEFAULT_OUTPUT_DIRNAME = "papyrium-jobs"
_DEFAULT_IDLE_TIMEOUT_SECONDS = 5.0
_READ_SIZE = 65536


def _print_error(line: str, is_continuation: bool = False) -> None:
    click.secho(line, err=True, fg="yellow" if is_continuation else "red")


class _BoundaryGroup(click.Group):
    """Runs every command inside the handled_errors boundary, honouring --debug."""

    def invoke(self, ctx: click.Context):
        debug = bool(ctx.params.get("debug", False))
        with handled_errors(_print_error, debug=debug):
            return super().invoke(ctx)


@click.group(cls=_BoundaryGroup)
@click.option("--debug", is_flag=True, help="Show full tracebacks for errors.")
@click.version_option(__version__, prog_name="papyrium")
def cli(debug: bool) -> None:
    """Papyrium, a virtual vintage printer."""


_OUTPUT_DIR = click.option(
    "--output-dir",
    "output_dirpath",
    default=_DEFAULT_OUTPUT_DIRNAME,
    show_default=True,
    type=click.Path(file_okay=False, path_type=Path),
    help="Directory holding one numbered subdirectory per job.",
)

_MODEL_OPTION = click.option(
    "--model-option",
    "-M",
    "model_options",
    multiple=True,
    metavar="KEY=VALUE",
    callback=parse_options,
    help="An option for the printer model, such as auto-line-feed=yes (repeatable).",
)

_OUTPUT = click.option(
    "--output",
    "-o",
    "output_names",
    multiple=True,
    help="An output to write pages with (repeatable; default: png and pdf).",
)

_OUTPUT_OPTION = click.option(
    "--output-option",
    "-O",
    "output_options",
    multiple=True,
    metavar="OUTPUT.KEY=VALUE",
    callback=parse_output_options,
    help="An option for an output, such as png.dpi=300 (repeatable).",
)


@cli.command()
@click.option(
    "--transport",
    "-t",
    "transport_name",
    default=_DEFAULT_TRANSPORT_NAME,
    show_default=True,
    help="Transport plug-in to receive bytes on.",
)
@click.option(
    "--transport-option",
    "-T",
    "transport_options",
    multiple=True,
    metavar="KEY=VALUE",
    callback=parse_options,
    help="An option for the transport, such as port=9100 (repeatable).",
)
@click.option(
    "--model",
    "-m",
    "model_name",
    default=_DEFAULT_MODEL_NAME,
    show_default=True,
    help="The printer model to emulate.",
)
@_MODEL_OPTION
@_OUTPUT
@_OUTPUT_OPTION
@click.option(
    "--capture-only", is_flag=True, help="Capture jobs without interpreting them into pages."
)
@_OUTPUT_DIR
@click.option(
    "--idle-timeout",
    "idle_timeout_seconds",
    type=click.FloatRange(min=0),
    default=_DEFAULT_IDLE_TIMEOUT_SECONDS,
    show_default=True,
    help="Seconds without bytes after which a job ends; 0 never ends one.",
)
def serve(
    transport_name: str,
    transport_options: dict[str, str],
    model_name: str,
    model_options: dict[str, str],
    output_names: tuple[str, ...],
    output_options: dict[str, dict[str, str]],
    capture_only: bool,
    output_dirpath: Path,
    idle_timeout_seconds: float,
) -> None:
    """Run a printer until interrupted, printing every job it receives.

    Each job gets a numbered directory under ``--output-dir`` holding its
    raw bytes (``capture.prn``), a record (``job.json``) and its pages, as
    written by each ``--output``, which appear as the paper is ejected. A
    job ends after ``--idle-timeout`` seconds without bytes, or at
    shutdown; a disconnect never ends one.
    """
    transport = TRANSPORTS.create(transport_name, transport_options)
    model = MODELS.create(model_name, model_options)
    renderer = None
    if not capture_only:
        outputs = create_outputs(output_names or _DEFAULT_OUTPUT_NAMES, output_options)
        renderer = JobRenderer(model, outputs)
    spooler = Spooler(
        transport,
        JobStore(output_dirpath),
        idle_timeout_seconds=idle_timeout_seconds,
        printer_setup={"model": model_name, "options": model.config},
        listener=renderer,
    )
    logging.basicConfig(level=logging.INFO, format="papyrium: %(message)s")
    asyncio.run(_serve_until_signalled(transport, spooler, renderer))


async def serve_until(
    transport: Transport, spooler: Spooler, renderer: JobRenderer | None, stop: asyncio.Event
) -> None:
    """Open the transport, spool and render, and shut down gracefully when *stop* is set."""
    render_task = None if renderer is None else asyncio.create_task(renderer.run())
    await transport.open()
    spool_task = asyncio.create_task(spooler.run())
    try:
        await stop.wait()
    finally:
        await transport.close()
        await spool_task
        if renderer is not None:
            renderer.close()
            await render_task


async def _serve_until_signalled(
    transport: Transport, spooler: Spooler, renderer: JobRenderer | None
) -> None:
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for signal_number in (signal.SIGINT, signal.SIGTERM):
        with contextlib.suppress(NotImplementedError):
            loop.add_signal_handler(signal_number, stop.set)
    await serve_until(transport, spooler, renderer, stop)


@cli.command()
@click.argument("capture_path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--model",
    "-m",
    "model_name",
    default=None,
    help="The printer model; default: the one recorded with the job, else epson-fx80.",
)
@_MODEL_OPTION
@_OUTPUT
@_OUTPUT_OPTION
@click.option(
    "--output-dir",
    "output_dirpath",
    default=None,
    type=click.Path(file_okay=False, path_type=Path),
    help="Where to write pages; default: the job directory, or beside the capture file.",
)
@report_output(reports={"files": "Files written."})
def render(
    capture_path: Path,
    model_name: str | None,
    model_options: dict[str, str],
    output_names: tuple[str, ...],
    output_options: dict[str, dict[str, str]],
    output_dirpath: Path | None,
):
    """Print a captured job again, from a job directory or a raw capture file.

    Given a job directory, the printer model and options recorded with the
    job are used unless ``--model`` is given; ``-M`` options are applied on
    top. The same capture and setup always give identical pages.
    """
    if capture_path.is_dir():
        capture_filepath = capture_path / CAPTURE_FILENAME
        if not capture_filepath.is_file():
            raise DataError(f"{capture_path} holds no {CAPTURE_FILENAME}")
        setup = None
        if (capture_path / JOB_RECORD_FILENAME).is_file():
            setup = JobRecord.read(capture_path).printer_setup
        default_dirpath = capture_path
    else:
        capture_filepath, setup, default_dirpath = capture_path, None, capture_path.parent
    if model_name is None and setup is not None:
        model_name = setup["model"]
        model_options = {**setup.get("options", {}), **model_options}
    model = MODELS.create(model_name or _DEFAULT_MODEL_NAME, model_options)
    outputs = create_outputs(output_names or _DEFAULT_OUTPUT_NAMES, output_options)
    target_dirpath = output_dirpath or default_dirpath
    target_dirpath.mkdir(parents=True, exist_ok=True)
    rendering = JobRendering(model, outputs, target_dirpath)
    with open(capture_filepath, "rb") as capture:
        while chunk := capture.read(_READ_SIZE):
            rendering.feed(chunk)
    table = TableContent(title=f"{rendering.page_count} pages from {capture_filepath}")
    table.add_column("path", "File", header=True)
    for filepath in rendering.finish():
        table.add_row(path=str(filepath))
    return Reports(files=Report(data=table))


@cli.command("list-jobs")
@_OUTPUT_DIR
@report_output(reports={"jobs": "Jobs captured in the output directory."})
def list_jobs(output_dirpath: Path):
    """List the jobs captured in an output directory."""
    table = TableContent(title=str(output_dirpath))
    table.add_column("number", "Job", header=True)
    table.add_column("transport", "Transport")
    table.add_column("model", "Model")
    table.add_column("started_at", "Started")
    table.add_column("ended_at", "Ended")
    table.add_column("end_reason", "Ended by")
    table.add_column("byte_count", "Bytes")
    for record in JobStore(output_dirpath).records():
        setup = record.printer_setup or {}
        table.add_row(
            number=record.number,
            transport=record.transport_name,
            model=setup.get("model", ""),
            started_at=_timestamp_cell(record.started_at),
            ended_at=_timestamp_cell(record.ended_at),
            end_reason=ByAudience(
                machine=None if record.end_reason is None else record.end_reason.value,
                human="" if record.end_reason is None else record.end_reason.value,
            ),
            byte_count=record.byte_count,
        )
    return Reports(jobs=Report(data=table))


def _timestamp_cell(when: datetime | None) -> ByAudience:
    """Full ISO 8601 for machines; local time to the second for humans."""
    if when is None:
        return ByAudience(machine=None, human="")
    return ByAudience(
        machine=when.isoformat(),
        human=when.astimezone().isoformat(sep=" ", timespec="seconds"),
    )


def _list_command(axis: Axis) -> click.Command:
    @click.command(f"list-{axis.plural}", help=f"List the installed {axis.plural}.")
    @report_output(reports={axis.plural: axis.summary})
    def list_plugins():
        table = TableContent(title=axis.plural.capitalize())
        table.add_column("name", "Name", header=True)
        table.add_column("description", "Description")
        for name in axis.names():
            table.add_row(
                name=name,
                description=describe_extension(axis.kind, axis.namespace, name, single_line=True),
            )
        return Reports(**{axis.plural: Report(data=table)})

    return list_plugins


def _describe_command(axis: Axis) -> click.Command:
    @click.command(
        f"describe-{axis.singular}", help=f"Describe one of the installed {axis.plural}."
    )
    @click.argument("name")
    def describe_plugin(name: str) -> None:
        if name not in axis.names():
            raise ConfigurationError(
                f"no {axis.singular} named {name!r}; installed {axis.plural}: "
                f"{', '.join(axis.names()) or 'none'}"
            )
        click.echo(describe_extension(axis.kind, axis.namespace, name))

    return describe_plugin


for _axis in AXES:
    cli.add_command(_list_command(_axis))
    cli.add_command(_describe_command(_axis))

cli.add_command(list_formatters_command(), name="list-report-formats")
cli.add_command(describe_formatter_command(), name="describe-report-format")
cli.add_command(list_reports_command(), name="list-reports")
cli.add_command(describe_report_command(), name="describe-report")

use_plain_help(cli)
