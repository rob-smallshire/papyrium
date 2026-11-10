"""Make a KX-P1080U EPROM whose self test prints the CPU's internal ROM.

The KX-P1080U's draft fonts are in its uPD7811's 4 KB mask ROM, at
0x0000-0x0FFF, which the EPROM dump does not include
(docs/panasonic-kx-p1080.md). The firmware reads that ROM itself, and its
self test is in the EPROM, so a patched EPROM can print it as text.

The self test ($2339, started by holding LF while switching on) feeds
characters to the printer as if they had been received: it waits for
$8F bit 6 to clear, puts the character in $74 and calls CALT $009E, and
ends a line by putting LF in $74 and calling $2EF8 and $2245. The patch
replaces its first instruction with a jump to a routine in unused EPROM
space that does the same with a hex dump of 0x0000-0x0FFF, sixteen bytes
a line after the address, with a checksum (the bytes' sum, modulo 256) at
the end, twice over, then stops as the self test's end does. It keeps its
state in the self test's own RAM, $FFF0-$FFF4.

Usage: uv run python tools/kx-p1080-rom/dump_patch.py [ROM_FILEPATH]

Writes KX-P1080U-dump.bin, the image to program into a 27128 in place of
the original EPROM, beside the ROM in docs/local/, and prints the patched
code disassembled for checking. Switch the printer on holding LF, with
the print mode switch at NLQ for the clearest characters or Std. Pgm. for
draft; it prints about eight pages and stops.
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_DIRPATH = Path(__file__).resolve().parents[2]
ROM_FILEPATH = REPO_DIRPATH / "docs/local/panasonic-kx-p1080/KX-P1080U.BIN"
UNIDASM_FILEPATH = REPO_DIRPATH / "docs/local/m50734/unidasm"

SHA1 = "4839aebb1c22222bf43eb4c6de6287909c0d0ce6"

#: The self test's first instruction, LXI HL,$078F, becomes JMP to the dump.
SELF_TEST = 0x2339
SELF_TEST_ORIGINAL = bytes([0x34, 0x8F, 0x07])

#: Where the dump routine goes: unused EPROM, 0xFF to $1FFF.
ORIGIN = 0x1F40

#: The self test's RAM: $FFF0-$FFF1 the address, $FFF2 the checksum,
#: $FFF3 the bytes left on the line, $FFF4 the passes left.
POINTER, CHECKSUM, COUNT, PASSES = 0xF0, 0xF2, 0xF3, 0xF4
RECEIVED = 0x74  # $FF74: the byte the printer takes next
READY = 0x8F  # $FF8F bit 6 set while the printer cannot take a byte
SIZE_PAGES = 0x10  # 0x0000-0x0FFF


def program() -> list[tuple]:
    """The dump routine, as (label,) or (mnemonic, operand...) entries."""
    return [
        ("label", "start"),
        ("mviw", PASSES, 1),  # two passes: DCRW stops below zero
        ("label", "pass"),
        ("lxi_hl", 0x0000),
        ("shld", 0xFF00 | POINTER),
        ("label", "line"),
        ("ldaw", POINTER + 1),  # the address, high byte then low
        ("call", "hexbyte"),
        ("ldaw", POINTER),
        ("call", "hexbyte"),
        ("mvi_a", ord(":")),
        ("call", "putc"),
        ("mviw", CHECKSUM, 0),
        ("mviw", COUNT, 15),  # sixteen bytes: DCRW stops below zero
        ("label", "byte"),
        ("mvi_a", ord(" ")),
        ("call", "putc"),
        ("lhld", 0xFF00 | POINTER),
        ("ldax_hl_inc",),
        ("shld", 0xFF00 | POINTER),
        ("push_va",),
        ("addw", CHECKSUM),
        ("staw", CHECKSUM),
        ("pop_va",),
        ("call", "hexbyte"),
        ("dcrw", COUNT),
        ("jre", "byte"),
        ("mvi_a", ord(" ")),
        ("call", "putc"),
        ("mvi_a", ord(" ")),
        ("call", "putc"),
        ("ldaw", CHECKSUM),
        ("call", "hexbyte"),
        ("call", "newline"),
        ("ldaw", POINTER + 1),
        ("eqi_a", SIZE_PAGES),  # skips the jump back once past the end
        ("jre", "line"),
        ("call", "newline"),
        ("dcrw", PASSES),
        ("jre", "pass"),
        ("jmp", 0x2384),  # the self test's end: wait for printing, reset
        ("label", "newline"),
        ("mviw", RECEIVED, 0x0A),
        ("call", 0x2EF8),
        ("call", 0x2245),
        ("ret",),
        ("label", "hexbyte"),  # A as two hex digits
        ("push_va",),
        ("slr_a",),
        ("slr_a",),
        ("slr_a",),
        ("slr_a",),
        ("call", "nibble"),
        ("pop_va",),
        ("ani_a", 0x0F),
        ("label", "nibble"),  # A, 0-15, as a hex digit
        ("adi_a", ord("0")),
        ("gti_a", ord("9")),  # skips the jump for A to F
        ("jr", "putc"),
        ("adi_a", ord("A") - ord("9") - 1),
        ("label", "putc"),  # the character in A, as the self test does
        ("offiw", READY, 0x40),  # skips the jump once ready
        ("jr", "putc"),
        ("staw", RECEIVED),
        ("mvi_d", 0x00),
        ("calt_9e",),
        ("ret",),
    ]


def _word(value: int) -> list[int]:
    return [value & 0xFF, value >> 8]


#: Encodings, each one seen in the KX-P1080U's own code.
_SIZES = {
    "mviw": 3, "lxi_hl": 3, "shld": 4, "lhld": 4, "ldaw": 2, "staw": 2,
    "call": 3, "jmp": 3, "mvi_a": 2, "mvi_d": 2, "ldax_hl_inc": 1,
    "push_va": 1, "pop_va": 1, "addw": 3, "dcrw": 2, "jr": 1, "jre": 2,
    "eqi_a": 2, "gti_a": 2, "ani_a": 2, "adi_a": 2, "slr_a": 2,
    "offiw": 3, "calt_9e": 1, "ret": 1,
}  # fmt: skip


def assemble(origin: int) -> bytes:
    entries = program()
    labels, address = {}, origin
    for entry in entries:
        if entry[0] == "label":
            labels[entry[1]] = address
        else:
            address += _SIZES[entry[0]]
    out = bytearray()
    for entry in entries:
        op, *args = entry
        if op == "label":
            continue
        here = origin + len(out)
        after = here + _SIZES[op]

        def target(value):
            return labels[value] if isinstance(value, str) else value

        if op == "mviw":
            out += bytes([0x71, args[0], args[1]])
        elif op == "lxi_hl":
            out += bytes([0x34, *_word(args[0])])
        elif op == "shld":
            out += bytes([0x70, 0x3E, *_word(args[0])])
        elif op == "lhld":
            out += bytes([0x70, 0x3F, *_word(args[0])])
        elif op == "ldaw":
            out += bytes([0x01, args[0]])
        elif op == "staw":
            out += bytes([0x63, args[0]])
        elif op == "call":
            out += bytes([0x40, *_word(target(args[0]))])
        elif op == "jmp":
            out += bytes([0x54, *_word(target(args[0]))])
        elif op == "mvi_a":
            out += bytes([0x69, args[0]])
        elif op == "mvi_d":
            out += bytes([0x6C, args[0]])
        elif op == "ldax_hl_inc":
            out += bytes([0x2D])
        elif op == "push_va":
            out += bytes([0xB0])
        elif op == "pop_va":
            out += bytes([0xA0])
        elif op == "addw":
            out += bytes([0x74, 0xC0, args[0]])
        elif op == "dcrw":
            out += bytes([0x30, args[0]])
        elif op == "jr":
            displacement = target(args[0]) - after
            if not -32 <= displacement <= 31:
                raise SystemExit(f"JR out of range at ${here:04X}")
            out += bytes([0xC0 | (displacement & 0x3F)])
        elif op == "jre":
            displacement = target(args[0]) - after
            if not -256 <= displacement <= 255:
                raise SystemExit(f"JRE out of range at ${here:04X}")
            out += bytes([0x4E if displacement >= 0 else 0x4F, displacement & 0xFF])
        elif op == "eqi_a":
            out += bytes([0x77, args[0]])
        elif op == "gti_a":
            out += bytes([0x27, args[0]])
        elif op == "ani_a":
            out += bytes([0x07, args[0]])
        elif op == "adi_a":
            out += bytes([0x46, args[0]])
        elif op == "slr_a":
            out += bytes([0x48, 0x21])
        elif op == "offiw":
            out += bytes([0x55, args[0], args[1]])
        elif op == "calt_9e":
            out += bytes([0x8F])
        elif op == "ret":
            out += bytes([0xB8])
        else:
            raise SystemExit(f"no encoding for {op}")
        if len(out) != after - origin:
            raise SystemExit(f"{op} at ${here:04X} is not {_SIZES[op]} bytes")
    return bytes(out)


def patched(rom: bytes) -> tuple[bytes, bytes]:
    if hashlib.sha1(rom).hexdigest() != SHA1:
        raise SystemExit("this is not the KX-P1080U ROM the patch was made for")
    routine = assemble(ORIGIN)
    image = bytearray(rom)
    if image[SELF_TEST : SELF_TEST + 3] != SELF_TEST_ORIGINAL:
        raise SystemExit(f"unexpected bytes at ${SELF_TEST:04X}")
    if (
        any(b != 0xFF for b in image[ORIGIN : ORIGIN + len(routine)])
        or ORIGIN + len(routine) > 0x2000
    ):
        raise SystemExit(f"no room for {len(routine)} bytes at ${ORIGIN:04X}")
    image[SELF_TEST : SELF_TEST + 3] = bytes([0x54, *_word(ORIGIN)])
    image[ORIGIN : ORIGIN + len(routine)] = routine
    return bytes(image), routine


def disassemble(image: bytes, address: int, count: int) -> str:
    with tempfile.TemporaryDirectory() as temp_dirname:
        image_filepath = Path(temp_dirname) / "image.bin"
        image_filepath.write_bytes(image)
        return subprocess.run(
            [
                str(UNIDASM_FILEPATH), str(image_filepath), "-arch", "upd7810",
                "-basepc", hex(address), "-skip", hex(address), "-count", str(count),
            ],
            check=True,
            capture_output=True,
            text=True,
        ).stdout  # fmt: skip


def main() -> int:
    rom_filepath = Path(sys.argv[1]) if len(sys.argv) > 1 else ROM_FILEPATH
    image, routine = patched(rom_filepath.read_bytes())
    image_filepath = rom_filepath.with_name("KX-P1080U-dump.bin")
    image_filepath.write_bytes(image)
    print(disassemble(image, SELF_TEST, 3))
    print(disassemble(image, ORIGIN, len(routine)))
    print(f"wrote {image_filepath}: {len(routine)} bytes of routine at ${ORIGIN:04X}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
