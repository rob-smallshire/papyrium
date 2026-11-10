# rom-map

`disassemble.py` disassembles a printer's firmware from a map of it, with
MAME's `unidasm` used as a tool only. A map, kept beside the printer's
other ROM tools (`tools/lc10-rom/lc10-map.txt`,
`tools/kx-p1080-rom/kx-p1080-map.txt`), names the ROM, the CPU and how the
ROM appears at the CPU's addresses, marks where the program keeps data
rather than code, and names, in our own words, the routines, command
handlers and RAM locations traced so far. The listing it writes beside the
ROM in `docs/local/` keeps data apart from code, so it stays on
instruction boundaries, decodes command tables, heads each named routine
with its description, and names each address an instruction refers to.

    uv run python tools/rom-map/disassemble.py MAP_FILEPATH [UNIDASM_FILEPATH]

Build `unidasm` from a MAME checkout with
`make EMULATOR=0 TOOLS=1 NOWERROR=1`; the script looks for it in
`docs/local/m50734/`. The map format is described in the script.
