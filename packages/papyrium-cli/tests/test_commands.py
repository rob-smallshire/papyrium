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
    result = run("--version")
    assert result.exit_code == 0
    assert "papyrium" in result.output


def test_list_transports_includes_raw_tcp(run):
    result = run("list-transports", "--as", "json")
    assert result.exit_code == 0
    assert "raw-tcp" in result.output


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
