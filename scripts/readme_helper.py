"""Helpers for README example recipes in scripts/readme-examples/.

A recipe calls :func:`show` for each command the reader should see. The
README shows ``$ command`` and its output, run against the workspace's
own code, so the transcript cannot drift from what the command does.
"""

from __future__ import annotations

import shlex
import subprocess
import sys

#: papyrium subcommands with report output. Captured output is not a
#: terminal, so the report would otherwise print as TSV; ``--as display``
#: is added when running them, but not to the command shown.
REPORT_SUBCOMMANDS = frozenset(
    {
        "list-fonts",
        "list-jobs",
        "list-languages",
        "list-models",
        "list-outputs",
        "list-transports",
        "render",
    }
)


def show(command: str) -> None:
    """Run *command* and print ``$ command`` and its output.

    Raises:
        SystemExit: The command failed, so a broken example stops the render.
    """
    print(f"$ {command}")
    tokens = shlex.split(command)
    run_command = command
    if tokens[:1] == ["papyrium"] and tokens[1:2] and tokens[1] in REPORT_SUBCOMMANDS:
        if "--as" not in tokens and "--no-reports" not in tokens:
            run_command = f"{command} --as display"
    result = subprocess.run(run_command, shell=True, capture_output=True, text=True)
    sys.stdout.write(result.stdout)
    sys.stdout.write(result.stderr)
    if result.returncode != 0:
        sys.stderr.write(f"recipe step failed: {command}\n")
        raise SystemExit(result.returncode)
