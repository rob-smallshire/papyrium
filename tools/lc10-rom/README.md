# lc10-rom

Tools that read the Star LC-10 Colour's firmware ROM, kept uncommitted as
`docs/local/star-lc10/LC10-NX1P-1.5CL.bin`. What they have found is
written up in `docs/star-lc10-firmware.md`.

- `extract.py` decodes the ROM's character tables into the dot font files
  of `papyrium.font.lc10`.
- `lc10-map.txt` is the map of the program, in our own words, from which
  `tools/rom-map/disassemble.py` writes the annotated disassembly,
  `docs/local/star-lc10/LC10-NX1P-1.5CL.dis`: data kept apart from code,
  command tables decoded, and routines, handlers and RAM locations named.
  Run `uv run python tools/rom-map/disassemble.py tools/lc10-rom/lc10-map.txt`;
  add to the map as tracing finds things, and run it again.
