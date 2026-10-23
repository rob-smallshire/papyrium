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
from papyrium.core.jobs import JobStore
from papyrium.core.spooler import Spooler
from papyrium.core.transport import Transport
from papyrium.exception import ConfigurationError, handled_errors
from papyrium.extension import describe_extension, extension, list_extensions, namespace_for

__version__ = "0.0.0"

__all__ = ["cli"]

_TRANSPORT_KIND = "transport"
_TRANSPORT_NAMESPACE = namespace_for(_TRANSPORT_KIND)

_DEFAULT_TRANSPORT_NAME = "raw-tcp"
_DEFAULT_OUTPUT_DIRNAME = "papyrium-jobs"
_DEFAULT_IDLE_TIMEOUT_SECONDS = 5.0


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


def _parse_options(_ctx, _param, values: tuple[str, ...]) -> dict[str, str]:
    options = {}
    for value in values:
        key, separator, setting = value.partition("=")
        if not separator or not key:
            raise click.BadParameter(f"expected KEY=VALUE, got {value!r}")
        options[key.strip()] = setting.strip()
    return options


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
    callback=_parse_options,
    help="An option for the transport, such as port=9100 (repeatable).",
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
    output_dirpath: Path,
    idle_timeout_seconds: float,
) -> None:
    """Run a printer until interrupted, capturing every job it receives.

    Each job gets a numbered directory under ``--output-dir`` holding its
    raw bytes (``capture.prn``) and a record (``job.json``). A job ends
    after ``--idle-timeout`` seconds without bytes, or at shutdown; a
    disconnect never ends one.
    """
    transport = _create_transport(transport_name, transport_options)
    spooler = Spooler(
        transport, JobStore(output_dirpath), idle_timeout_seconds=idle_timeout_seconds
    )
    logging.basicConfig(level=logging.INFO, format="papyrium: %(message)s")
    asyncio.run(_serve_until_signalled(transport, spooler))


def _create_transport(name: str, options: dict[str, str]) -> Transport:
    transport_class = extension(_TRANSPORT_KIND, _TRANSPORT_NAMESPACE, name)
    return transport_class.from_config(name=name, config=options)


async def serve_until(transport: Transport, spooler: Spooler, stop: asyncio.Event) -> None:
    """Open the transport, spool, and shut down gracefully when *stop* is set."""
    await transport.open()
    spool_task = asyncio.create_task(spooler.run())
    try:
        await stop.wait()
    finally:
        await transport.close()
        await spool_task


async def _serve_until_signalled(transport: Transport, spooler: Spooler) -> None:
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for signal_number in (signal.SIGINT, signal.SIGTERM):
        with contextlib.suppress(NotImplementedError):
            loop.add_signal_handler(signal_number, stop.set)
    await serve_until(transport, spooler, stop)


@cli.command("list-jobs")
@_OUTPUT_DIR
@report_output(reports={"jobs": "Jobs captured in the output directory."})
def list_jobs(output_dirpath: Path):
    """List the jobs captured in an output directory."""
    table = TableContent(title=str(output_dirpath))
    table.add_column("number", "Job", header=True)
    table.add_column("transport", "Transport")
    table.add_column("started_at", "Started")
    table.add_column("ended_at", "Ended")
    table.add_column("end_reason", "Ended by")
    table.add_column("byte_count", "Bytes")
    for record in JobStore(output_dirpath).records():
        table.add_row(
            number=record.number,
            transport=record.transport_name,
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


@cli.command("list-transports")
@report_output(reports={"transports": "Installed transport plug-ins."})
def list_transports():
    """List the installed transport plug-ins."""
    table = TableContent(title="Transports")
    table.add_column("name", "Name", header=True)
    table.add_column("description", "Description")
    for name in sorted(list_extensions(_TRANSPORT_NAMESPACE)):
        table.add_row(
            name=name,
            description=describe_extension(
                _TRANSPORT_KIND, _TRANSPORT_NAMESPACE, name, single_line=True
            ),
        )
    return Reports(transports=Report(data=table))


@cli.command("describe-transport")
@click.argument("name")
def describe_transport(name: str) -> None:
    """Describe a transport plug-in and its options."""
    if name not in list_extensions(_TRANSPORT_NAMESPACE):
        raise ConfigurationError(
            f"no transport named {name!r}; installed transports: "
            f"{', '.join(sorted(list_extensions(_TRANSPORT_NAMESPACE)))}"
        )
    click.echo(describe_extension(_TRANSPORT_KIND, _TRANSPORT_NAMESPACE, name))


cli.add_command(list_formatters_command(), name="list-report-formats")
cli.add_command(describe_formatter_command(), name="describe-report-format")
cli.add_command(list_reports_command(), name="list-reports")
cli.add_command(describe_report_command(), name="describe-report")

use_plain_help(cli)
