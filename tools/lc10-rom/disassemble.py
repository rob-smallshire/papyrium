"""Disassemble the Star LC-10's program, annotated from our map of it.

The program is the upper 32K of the ROM, at CPU addresses 0x8000-0xFFFF.
MAME's unidasm (architecture m740, which the M50734 is) disassembles the
code, used only as a tool. ``lc10-map.txt`` beside this script says where
the program keeps data rather than code, so that the disassembly stays on
instruction boundaries after it, and names the routines and RAM
locations traced so far. The listing gives each named routine a heading,
decodes the command tables, and notes the name of every address an
instruction refers to.

Usage: uv run python tools/lc10-rom/disassemble.py [ROM_FILEPATH [UNIDASM_FILEPATH]]

Writes docs/local/star-lc10/LC10-NX1P-1.5CL.dis, which stays uncommitted
like the ROM. Build unidasm from a MAME checkout with
``make EMULATOR=0 TOOLS=1 NOWERROR=1``; the script looks for it in
docs/local/m50734/.
"""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

REPO_DIRPATH = Path(__file__).resolve().parents[2]
MAP_FILEPATH = Path(__file__).with_name("lc10-map.txt")
PROGRAM_BASE = 0x8000
PROGRAM_END = 0x10000
_OPERAND = re.compile(r"\$([0-9a-f]{2,4})\b")


@dataclass(frozen=True)
class Region:
    """Data in the program: *kind* is ``data`` (bytes) or ``commands`` (a
    command table of three-byte entries, a byte and its handler, ended by
    a zero)."""

    first: int
    last: int
    kind: str
    name: str
    description: str


@dataclass(frozen=True)
class Name:
    """A routine, entry point or RAM location, and what it does."""

    address: int
    name: str
    description: str


def read_map(map_filepath: Path) -> tuple[list[Region], dict[int, Name]]:
    """The map's data regions, in address order, and its names by address.

    Each line is an address or range, a kind (``data``, ``commands``,
    ``code`` for a routine, ``ram`` for a RAM location), a name and a
    description; ``#`` starts a comment.
    """
    regions, names = [], {}
    for number, line in enumerate(map_filepath.read_text().splitlines(), 1):
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        try:
            span, kind, name, *rest = line.split(None, 3)
        except ValueError as error:
            raise SystemExit(f"{map_filepath}:{number}: {line!r}") from error
        description = rest[0] if rest else ""
        first_text, _, last_text = span.partition("-")
        first = int(first_text.lstrip("$"), 16)
        last = int(last_text.lstrip("$"), 16) if last_text else first
        if kind in ("data", "commands"):
            regions.append(Region(first, last, kind, name, description))
        elif kind not in ("code", "ram"):
            raise SystemExit(f"{map_filepath}:{number}: unknown kind {kind!r}")
        names[first] = Name(first, name, description)
    return sorted(regions, key=lambda region: region.first), names


def disassemble_code(unidasm_filepath: Path, program_filepath: Path, first: int, last: int) -> str:
    count = last - first + 1
    return subprocess.run(
        [
            str(unidasm_filepath),
            str(program_filepath),
            "-arch", "m740",
            "-basepc", hex(first),
            "-skip", hex(first - PROGRAM_BASE),
            "-count", str(count),
        ],
        check=True,
        capture_output=True,
        text=True,
    ).stdout  # fmt: skip


def data_lines(program: bytes, region: Region, names: dict[int, Name]) -> list[str]:
    def at(address: int) -> int:
        return program[address - PROGRAM_BASE]

    lines = []
    address = region.first
    if region.kind == "commands":
        while address + 2 <= region.last and at(address):
            command = at(address)
            handler = at(address + 1) | at(address + 2) << 8
            shown = repr(chr(command)) if 0x20 <= command < 0x7F else f"0x{command:02x}"
            name = names.get(handler)
            label = f"  {name.name}" if name else ""
            raw = " ".join(f"{at(a):02x}" for a in range(address, address + 3))
            lines.append(f"{address:04x}: {raw}  {shown:>6} -> ${handler:04x}{label}")
            address += 3
        if address <= region.last:
            lines.append(f"{address:04x}: {at(address):02x}        end")
            address += 1
    while address <= region.last:
        row = range(address, min(address + 16, region.last + 1))
        lines.append(f"{address:04x}: " + " ".join(f"{at(a):02x}" for a in row))
        address += 16
    return lines


def annotate(line: str, names: dict[int, Name]) -> str:
    """*line* with the names of the addresses it refers to."""
    referred = [
        names[int(match, 16)].name
        for match in _OPERAND.findall(line.split("  ", 1)[-1])
        if int(match, 16) in names
    ]
    return f"{line:<40}; {', '.join(referred)}" if referred else line


def heading(name: Name) -> list[str]:
    return ["", f"; {name.name}: {name.description}" if name.description else f"; {name.name}"]


def main() -> int:
    rom_filepath = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else (REPO_DIRPATH / "docs/local/star-lc10/LC10-NX1P-1.5CL.bin")
    )
    unidasm_filepath = (
        Path(sys.argv[2]) if len(sys.argv) > 2 else (REPO_DIRPATH / "docs/local/m50734/unidasm")
    )
    dis_filepath = rom_filepath.with_suffix(".dis")
    program = rom_filepath.read_bytes()[PROGRAM_BASE:]
    regions, names = read_map(MAP_FILEPATH)
    out: list[str] = []
    with tempfile.TemporaryDirectory() as temp_dirname:
        program_filepath = Path(temp_dirname) / "program.bin"
        program_filepath.write_bytes(program)
        address = PROGRAM_BASE
        for region in [*regions, Region(PROGRAM_END, PROGRAM_END, "end", "", "")]:
            if address < region.first:
                for line in disassemble_code(
                    unidasm_filepath, program_filepath, address, region.first - 1
                ).splitlines():
                    line_address = int(line.split(":", 1)[0], 16)
                    if line_address in names:
                        out.extend(heading(names[line_address]))
                    out.append(annotate(line, names))
            if region.kind == "end":
                break
            out.extend(heading(names[region.first]))
            out.extend(data_lines(program, region, names))
            address = region.last + 1
    dis_filepath.write_text("\n".join(out) + "\n")
    print(f"wrote {dis_filepath}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
