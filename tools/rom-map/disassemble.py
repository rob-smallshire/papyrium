"""Disassemble a printer's firmware, annotated from our map of it.

MAME's unidasm disassembles the code, used only as a tool. A map file says
which ROM it describes and how the ROM appears at the CPU's addresses,
where the program keeps data rather than code, so that the disassembly
stays on instruction boundaries after it, and names the routines and RAM
locations traced so far. The listing gives each named routine a heading,
decodes command tables, and notes the name of every address an
instruction refers to.

Usage: uv run python tools/rom-map/disassemble.py MAP_FILEPATH [UNIDASM_FILEPATH]

The listing is written where the map says, beside the ROM in docs/local/,
and stays uncommitted like the ROM. Build unidasm from a MAME checkout with
``make EMULATOR=0 TOOLS=1 NOWERROR=1``; the script looks for it in
docs/local/m50734/.

A map's directives, before its entries, are paths relative to the
repository and numbers in hexadecimal:

- ``@rom PATH``: the ROM image.
- ``@listing PATH``: the listing to write.
- ``@arch NAME``: unidasm's architecture, such as ``m740`` or ``upd7810``.
- ``@segment OFFSET-LAST at ADDRESS``: the ROM's bytes OFFSET to LAST
  appear at the CPU's ADDRESS on; one or more, listed in address order.
- ``@mirror FIRST-LAST at ADDRESS``: CPU addresses FIRST to LAST show the
  same bytes as those from ADDRESS on, so a name there names them too.
- ``@vpage PAGE``: the page a uPD7810's working-register operands
  (``VV:xx``) address, so that ``VV:E9`` is named as ``$PAGEE9``.

Each entry is a CPU address or range, a kind (``data`` for bytes,
``commands`` for a command table of three-byte entries, a byte and its
handler's address, ended by a zero; ``code`` for a routine or an entry
point within one; ``ram`` for a RAM location), a name and a description;
``#`` starts a comment.
"""

from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO_DIRPATH = Path(__file__).resolve().parents[2]
_OPERAND = re.compile(r"\$([0-9a-fA-F]{2,4})\b")
_WORKING_REGISTER = re.compile(r"VV:([0-9a-fA-F]{2})\b")


@dataclass(frozen=True)
class Segment:
    """ROM bytes *offset* to *last* appearing from CPU address *address*."""

    offset: int
    last: int
    address: int

    @property
    def end(self) -> int:
        return self.address + self.last - self.offset + 1


@dataclass(frozen=True)
class Region:
    """Data in the program, by CPU address: *kind* is ``data`` or ``commands``."""

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


@dataclass
class RomMap:
    """A map file's directives, data regions and names."""

    rom_filepath: Path = Path()
    listing_filepath: Path = Path()
    arch: str = ""
    vpage: int | None = None
    segments: list[Segment] = field(default_factory=list)
    mirrors: list[tuple[int, int, int]] = field(default_factory=list)
    regions: list[Region] = field(default_factory=list)
    names: dict[int, Name] = field(default_factory=dict)

    def name_for(self, address: int) -> Name | None:
        """The name for *address*, or for the address it mirrors."""
        if address in self.names:
            return self.names[address]
        for first, last, target in self.mirrors:
            if first <= address <= last:
                return self.names.get(target + address - first)
        return None


def _span(text: str) -> tuple[int, int]:
    first_text, _, last_text = text.partition("-")
    first = int(first_text.lstrip("$"), 16)
    return first, int(last_text.lstrip("$"), 16) if last_text else first


def read_map(map_filepath: Path) -> RomMap:
    rom_map = RomMap()
    for number, line in enumerate(map_filepath.read_text().splitlines(), 1):
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        where = f"{map_filepath}:{number}"
        if line.startswith("@"):
            directive, _, value = line.partition(" ")
            value = value.strip()
            if directive == "@rom":
                rom_map.rom_filepath = REPO_DIRPATH / value
            elif directive == "@listing":
                rom_map.listing_filepath = REPO_DIRPATH / value
            elif directive == "@arch":
                rom_map.arch = value
            elif directive == "@vpage":
                rom_map.vpage = int(value.lstrip("$"), 16)
            elif directive in ("@segment", "@mirror"):
                span, at, address = value.split()
                if at != "at":
                    raise SystemExit(f"{where}: expected 'at' in {line!r}")
                first, last = _span(span)
                if directive == "@segment":
                    rom_map.segments.append(Segment(first, last, int(address.lstrip("$"), 16)))
                else:
                    rom_map.mirrors.append((first, last, int(address.lstrip("$"), 16)))
            else:
                raise SystemExit(f"{where}: unknown directive {directive!r}")
            continue
        try:
            span, kind, name, *rest = line.split(None, 3)
        except ValueError as error:
            raise SystemExit(f"{where}: {line!r}") from error
        first, last = _span(span)
        if kind in ("data", "commands"):
            rom_map.regions.append(Region(first, last, kind, name, rest[0] if rest else ""))
        elif kind not in ("code", "ram"):
            raise SystemExit(f"{where}: unknown kind {kind!r}")
        rom_map.names[first] = Name(first, name, rest[0] if rest else "")
    rom_map.regions.sort(key=lambda region: region.first)
    if not (rom_map.rom_filepath.name and rom_map.listing_filepath.name and rom_map.arch):
        raise SystemExit(f"{map_filepath}: @rom, @listing and @arch are required")
    if not rom_map.segments:
        raise SystemExit(f"{map_filepath}: at least one @segment is required")
    return rom_map


def disassemble_code(
    unidasm_filepath: Path, rom_map: RomMap, segment: Segment, first: int, last: int
) -> str:
    return subprocess.run(
        [
            str(unidasm_filepath),
            str(rom_map.rom_filepath),
            "-arch", rom_map.arch,
            "-basepc", hex(first),
            "-skip", hex(segment.offset + first - segment.address),
            "-count", str(last - first + 1),
        ],
        check=True,
        capture_output=True,
        text=True,
    ).stdout  # fmt: skip


def data_lines(rom: bytes, segment: Segment, region: Region, rom_map: RomMap) -> list[str]:
    def at(address: int) -> int:
        return rom[segment.offset + address - segment.address]

    lines = []
    address = region.first
    if region.kind == "commands":
        while address + 2 <= region.last and at(address):
            command = at(address)
            handler = at(address + 1) | at(address + 2) << 8
            shown = repr(chr(command)) if 0x20 <= command < 0x7F else f"0x{command:02x}"
            name = rom_map.name_for(handler)
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


def annotate(line: str, rom_map: RomMap) -> str:
    """*line* with the names of the addresses it refers to."""
    referred = []
    instruction = line.split("  ", 1)[-1]
    addresses = [int(match, 16) for match in _OPERAND.findall(instruction)]
    if rom_map.vpage is not None:
        addresses += [
            rom_map.vpage << 8 | int(m, 16) for m in _WORKING_REGISTER.findall(instruction)
        ]
    for address in addresses:
        name = rom_map.name_for(address)
        if name is not None:
            referred.append(name.name)
    return f"{line:<40}; {', '.join(referred)}" if referred else line


def heading(name: Name) -> list[str]:
    return ["", f"; {name.name}: {name.description}" if name.description else f"; {name.name}"]


def listing(rom_map: RomMap, unidasm_filepath: Path) -> list[str]:
    rom = rom_map.rom_filepath.read_bytes()
    out: list[str] = []
    for segment in rom_map.segments:
        out.append(
            f"; ---- ROM 0x{segment.offset:04x}-0x{segment.last:04x} at ${segment.address:04x}"
        )
        regions = [r for r in rom_map.regions if segment.address <= r.first < segment.end]
        address = segment.address
        for region in [*regions, Region(segment.end, segment.end, "end", "", "")]:
            if address < region.first:
                code = disassemble_code(
                    unidasm_filepath, rom_map, segment, address, region.first - 1
                )
                for line in code.splitlines():
                    line_address = int(line.split(":", 1)[0], 16)
                    if line_address in rom_map.names:
                        out.extend(heading(rom_map.names[line_address]))
                    out.append(annotate(line, rom_map))
            if region.kind == "end":
                break
            out.extend(heading(rom_map.names[region.first]))
            out.extend(data_lines(rom, segment, region, rom_map))
            address = region.last + 1
    return out


def main() -> int:
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    map_filepath = Path(sys.argv[1])
    unidasm_filepath = (
        Path(sys.argv[2]) if len(sys.argv) > 2 else REPO_DIRPATH / "docs/local/m50734/unidasm"
    )
    rom_map = read_map(map_filepath)
    rom_map.listing_filepath.write_text("\n".join(listing(rom_map, unidasm_filepath)) + "\n")
    print(f"wrote {rom_map.listing_filepath}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
