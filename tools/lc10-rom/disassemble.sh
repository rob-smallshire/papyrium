#!/bin/sh
# Disassemble the LC-10's program, the upper 32K of its ROM, at its CPU
# addresses, with MAME's unidasm (architecture m740, which the M50734 is).
#
# Usage: disassemble.sh [ROM_FILEPATH [UNIDASM_FILEPATH]]
#
# Writes docs/local/star-lc10/LC10-NX1P-1.5CL.dis, which stays uncommitted
# like the ROM. unidasm is built from a MAME checkout with
# `make EMULATOR=0 TOOLS=1 NOWERROR=1`; it is used only as a tool.
set -eu
repo_dirpath=$(cd "$(dirname "$0")/../.." && pwd)
rom_filepath=${1:-$repo_dirpath/docs/local/star-lc10/LC10-NX1P-1.5CL.bin}
unidasm_filepath=${2:-$repo_dirpath/docs/local/m50734/unidasm}
dis_filepath=${rom_filepath%.bin}.dis
program_filepath=$(mktemp)
trap 'rm -f "$program_filepath"' EXIT
dd if="$rom_filepath" of="$program_filepath" bs=32768 skip=1 2>/dev/null
"$unidasm_filepath" "$program_filepath" -arch m740 -basepc 0x8000 > "$dis_filepath"
echo "wrote $dis_filepath"
