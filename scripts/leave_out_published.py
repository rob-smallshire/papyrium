#!/usr/bin/env python3
"""Remove from a dist directory every file already published on PyPI.

A version's files can never be replaced on PyPI, so a release that stopped
part way, such as when PyPI limits how many new projects may be created in
a period, is resumed by publishing only the files not yet there. Each file
left out is named.

Usage:
    python scripts/leave_out_published.py DIST_DIRPATH [--index-url URL]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

PYPI_JSON_URL = "https://pypi.org/pypi"

#: The project name and version at the start of a wheel's or sdist's filename.
_FILENAME_PATTERN = re.compile(r"^(?P<name>[A-Za-z0-9_.]+?)-(?P<version>[0-9][^-]*?)(-|\.tar\.gz$)")


def published_filenames(index_url: str, name: str, version: str) -> set[str]:
    """The filenames published for *name* at *version*; none if it has no such release."""
    try:
        with urllib.request.urlopen(f"{index_url}/{name}/{version}/json", timeout=30) as response:
            release = json.load(response)
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return set()
        raise
    return {file["filename"] for file in release["urls"]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("dist_dirpath", type=Path)
    parser.add_argument("--index-url", default=PYPI_JSON_URL)
    arguments = parser.parse_args()

    remaining = 0
    for filepath in sorted(arguments.dist_dirpath.iterdir()):
        match = _FILENAME_PATTERN.match(filepath.name)
        if match is None:
            continue
        published = published_filenames(arguments.index_url, match["name"], match["version"])
        if filepath.name in published:
            print(f"already published, leaving out: {filepath.name}")
            filepath.unlink()
        else:
            remaining += 1
    print(f"{remaining} files to publish")
    return 0


if __name__ == "__main__":
    sys.exit(main())
