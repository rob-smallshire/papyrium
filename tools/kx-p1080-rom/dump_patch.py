"""Make a KX-P1080U EPROM that prints the CPU's internal ROM, and its job.

The KX-P1080U's draft fonts are in its uPD7811's 4 KB mask ROM, at
0x0000-0x0FFF, which the EPROM dump does not include
(docs/panasonic-kx-p1080.md). The firmware reads that ROM itself, so a
patched EPROM can have the printer print it.

The patch changes bit-image graphics only. Each graphics data byte
received is normally stored as the column to print ($3786: LDAW $74,
STAX (DE+)). The patch calls a routine in unused EPROM space instead,
which prints the byte at the address whose high byte is the ESC 3
argument ($7A) and whose low byte is the data byte received. A job that
sends ESC 3 page, then ESC K with data bytes 0-255, prints page page of
memory as dot columns, 1/60 inch apart, bit 7 the top pin. Text and every
other command are untouched, so the job labels each line in draft.

Pages 0x00-0x0F are the internal ROM. Pages 0x20 and 0x21 are EPROM bytes
we already have, printed to check the reading of the scan.

Usage: uv run python tools/kx-p1080-rom/dump_patch.py [ROM_FILEPATH]

Writes KX-P1080U-dump.bin (the image to program into a 27128) and
dump-job.prn (the job to send to the printer, on its parallel port, with
the print mode switch at Std. Pgm.) beside the ROM, in docs/local/, and
prints the patched code disassembled for checking.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

REPO_DIRPATH = Path(__file__).resolve().parents[2]
ROM_FILEPATH = REPO_DIRPATH / "docs/local/panasonic-kx-p1080/KX-P1080U.BIN"
UNIDASM_FILEPATH = REPO_DIRPATH / "docs/local/m50734/unidasm"

SHA1 = "4839aebb1c22222bf43eb4c6de6287909c0d0ce6"

#: $378A in the graphics byte store: LDAW $74, STAX (DE+); then CALL $1F40.
STORE_ADDRESS = 0x378A
STORE_ORIGINAL = bytes([0x01, 0x74, 0x3C])
STORE_PATCHED = bytes([0x40, 0x40, 0x1F])

#: $1F40, unused (0xFF): store the byte at ($7A, $74) as the column.
ROUTINE_ADDRESS = 0x1F40
ROUTINE = bytes(
    [
        0xB3,  # PUSH HL
        0x01, 0x7A,  # LDAW $7A   the ESC 3 argument: the page
        0x1E,  # MOV H,A
        0x01, 0x74,  # LDAW $74   the data byte received: the offset
        0x1F,  # MOV L,A
        0x2B,  # LDAX (HL)
        0x3C,  # STAX (DE+)  as the column, as the original did
        0xA3,  # POP HL
        0xB8,  # RET
    ]
)  # fmt: skip

#: The pages to print: the internal ROM, then two EPROM pages to check by.
PAGES = [*range(0x00, 0x10), 0x20, 0x21]
CHUNK = 64

ESC, CR, LF = b"\x1b", b"\r", b"\n"


def patched(rom: bytes) -> bytes:
    import hashlib

    if hashlib.sha1(rom).hexdigest() != SHA1:
        raise SystemExit("this is not the KX-P1080U ROM the patch was made for")
    image = bytearray(rom)
    if image[STORE_ADDRESS : STORE_ADDRESS + 3] != STORE_ORIGINAL:
        raise SystemExit(f"unexpected bytes at ${STORE_ADDRESS:04X}")
    span = image[ROUTINE_ADDRESS : ROUTINE_ADDRESS + len(ROUTINE)]
    if any(b != 0xFF for b in span):
        raise SystemExit(f"${ROUTINE_ADDRESS:04X} is not free")
    image[STORE_ADDRESS : STORE_ADDRESS + 3] = STORE_PATCHED
    image[ROUTINE_ADDRESS : ROUTINE_ADDRESS + len(ROUTINE)] = ROUTINE
    return bytes(image)


def job() -> bytes:
    """Each page on one line, twice: a draft label before each 64 bytes."""
    out = bytearray(ESC + b"@" + ESC + b"x\x00" + ESC + b"P")  # draft, pica
    out += b"KX-P1080U internal ROM dump" + CR + LF + CR + LF
    for page in PAGES:
        for _copy in range(2):
            for start in range(0, 256, CHUNK):
                out += f"{page:02X}{start:02X} ".encode("ascii")
                out += ESC + b"3" + bytes([page])
                out += ESC + b"K" + bytes([CHUNK, 0]) + bytes(range(start, start + CHUNK))
                out += b" "
            out += ESC + b"3" + bytes([36]) + CR + LF  # back to 1/6 inch
        out += CR + LF
    return bytes(out + b"\x0c")


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
    image = patched(rom_filepath.read_bytes())
    image_filepath = rom_filepath.with_name("KX-P1080U-dump.bin")
    job_filepath = rom_filepath.with_name("dump-job.prn")
    image_filepath.write_bytes(image)
    job_filepath.write_bytes(job())
    print(disassemble(image, 0x3786, 12))
    print(disassemble(image, ROUTINE_ADDRESS, len(ROUTINE)))
    print(f"wrote {image_filepath} and {job_filepath}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
