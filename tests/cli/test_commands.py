"""The papyrium command's reporting commands, through Click's test runner."""

import json

import pytest
from click.testing import CliRunner

from papyrium.cli import cli
from papyrium.core.jobs import JobEndReason, JobStore


@pytest.fixture
def run():
    runner = CliRunner()

    def _run(*args):
        return runner.invoke(cli, list(args), catch_exceptions=False)

    return _run


def test_version(run):
    from importlib.metadata import version

    result = run("--version")
    assert result.exit_code == 0
    assert f"papyrium, version {version('papyrium')}" in result.output


def test_list_transports_includes_raw_tcp(run):
    result = run("list-transports", "--as", "json")
    assert result.exit_code == 0
    assert "raw-tcp" in result.output


def test_list_advertisers_includes_mdns(run):
    result = run("list-advertisers", "--as", "json")
    assert result.exit_code == 0
    assert "mdns" in result.output


@pytest.mark.parametrize(
    "options, advertise, expected",
    [
        ({}, False, {}),
        ({}, True, {"host": ""}),
        ({"host": "127.0.0.1"}, True, {"host": "127.0.0.1"}),
        ({"port": "9101"}, True, {"host": "", "port": "9101"}),
    ],
)
def test_advertising_listens_on_every_interface_unless_a_host_is_given(
    options, advertise, expected
):
    from papyrium.cli import transport_options_for

    assert transport_options_for("raw-tcp", options, advertise=advertise) == expected


def test_describe_transport(run):
    result = run("describe-transport", "raw-tcp")
    assert result.exit_code == 0
    assert "port 9100" in result.output


def test_describe_unknown_transport_is_a_configuration_error(run):
    result = run("describe-transport", "carrier-pigeon")
    assert result.exit_code == 78
    assert "carrier-pigeon" in result.output


def test_list_jobs(run, tmp_path):
    store = JobStore(tmp_path)
    job = store.create_job(transport_name="raw-tcp")
    job.append(b"HELLO\n\r")
    job.close(JobEndReason.IDLE)
    store.create_job(transport_name="raw-tcp")
    result = run("list-jobs", "--output-dir", str(tmp_path), "--as", "json")
    assert result.exit_code == 0
    rows = json.loads(result.output)["reports"]["jobs"]["rows"]
    assert [row["number"] for row in rows] == [1, 2]
    assert rows[0]["end_reason"] == "idle"
    assert rows[0]["byte_count"] == 7
    assert rows[1]["end_reason"] is None
    assert rows[1]["ended_at"] is None


def test_serve_rejects_an_unknown_transport_option(run, tmp_path):
    result = run("serve", "--output-dir", str(tmp_path), "-T", "colour=red")
    assert result.exit_code == 78
    assert "colour" in result.output


def test_serve_rejects_a_malformed_transport_option(run, tmp_path):
    result = run("serve", "--output-dir", str(tmp_path), "-T", "port")
    assert result.exit_code != 0
    assert "KEY=VALUE" in result.output


@pytest.mark.parametrize(
    "command, name",
    [
        ("list-models", "epson-fx80"),
        ("list-languages", "escp"),
        ("list-fonts", "draft-9"),
        ("list-outputs", "pdf"),
    ],
)
def test_axis_listings(run, command, name):
    result = run(command, "--as", "json")
    assert result.exit_code == 0
    assert name in result.output


def test_describe_model_lists_its_options(run):
    result = run("describe-model", "epson-fx80")
    assert result.exit_code == 0
    assert "auto-line-feed" in result.output


def test_render_a_capture_file_writes_pages_beside_it(run, tmp_path):
    capture_filepath = tmp_path / "hello.prn"
    capture_filepath.write_bytes(b"HELLO\r\n\x0cWORLD\r\n")
    result = run("render", str(capture_filepath), "--as", "json")
    assert result.exit_code == 0, result.output
    names = sorted(path.name for path in tmp_path.iterdir())
    assert names == ["hello.prn", "job.pdf", "page-0001.png", "page-0002.png"]


def test_render_selected_outputs_with_options(run, tmp_path):
    capture_filepath = tmp_path / "hello.prn"
    capture_filepath.write_bytes(b"HELLO\r\n")
    out_dirpath = tmp_path / "out"
    result = run(
        "render",
        str(capture_filepath),
        "-o",
        "png",
        "-O",
        "png.dpi=72",
        "--output-dir",
        str(out_dirpath),
    )
    assert result.exit_code == 0, result.output
    assert sorted(path.name for path in out_dirpath.iterdir()) == ["page-0001.png"]


def test_render_a_job_uses_its_recorded_printer_setup(run, tmp_path):
    store = JobStore(tmp_path)
    job = store.create_job(
        transport_name="raw-tcp",
        printer_setup={"model": "epson-fx80", "options": {"auto-line-feed": "yes"}},
    )
    job.append(b"A\rB\r")
    job.close(JobEndReason.REQUESTED)
    result = run("render", str(job.dirpath), "-o", "png")
    assert result.exit_code == 0, result.output
    from papyrium.model.epson_fx80 import EpsonFx80

    auto = EpsonFx80(name="m", auto_line_feed=True).create_interpreter()
    (expected,) = auto.feed(b"A\rB\r") + auto.finish()
    from PIL import Image

    from papyrium.output.png import PngOutput

    with Image.open(job.dirpath / "page-0001.png") as image:
        assert image.tobytes() == PngOutput(name="png").render(expected).tobytes()


def test_render_rejects_options_for_unselected_outputs(run, tmp_path):
    capture_filepath = tmp_path / "x.prn"
    capture_filepath.write_bytes(b"X")
    result = run("render", str(capture_filepath), "-o", "png", "-O", "pdf.ink=0")
    assert result.exit_code == 78
    assert "pdf" in result.output


def test_render_an_unknown_model_is_a_configuration_error(run, tmp_path):
    capture_filepath = tmp_path / "x.prn"
    capture_filepath.write_bytes(b"X")
    result = run("render", str(capture_filepath), "--model", "teletype")
    assert result.exit_code == 78
    assert "teletype" in result.output


def test_serving_a_model_that_is_not_installed_suggests_capturing_only():
    from click.testing import CliRunner

    result = CliRunner().invoke(cli, ["serve", "--model", "no-such-printer"])
    assert result.exit_code != 0
    assert "no-such-printer" in result.output
    assert "--capture-only" in result.output


def test_demo_prints_a_models_demonstration_page(run, tmp_path):
    result = run("demo", "epson-lx800", "--output-dir", str(tmp_path), "--as", "json")
    assert result.exit_code == 0
    assert (tmp_path / "page-0001.png").is_file()
    assert (tmp_path / "job.pdf").is_file()
    assert "page-0001.png" in result.output


def test_demo_takes_model_and_output_options(run, tmp_path):
    result = run(
        "demo", "brother-m1109", "-M", "stationery=green-bar", "-o", "png",
        "-O", "png.dpi=60", "--output-dir", str(tmp_path), "--as", "json",
    )  # fmt: skip
    assert result.exit_code == 0
    from PIL import Image

    with Image.open(tmp_path / "page-0001.png") as image:
        assert image.mode == "RGB" and image.width == 570
    assert not (tmp_path / "job.pdf").exists()


def test_demo_of_an_unknown_model_is_a_configuration_error(run, tmp_path):
    result = run("demo", "no-such-printer", "--output-dir", str(tmp_path))
    assert result.exit_code == 78
    assert "no-such-printer" in result.output
