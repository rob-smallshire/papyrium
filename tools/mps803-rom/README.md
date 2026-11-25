# mps803-rom

Tools for the Commodore MPS-803's firmware, the 4K internal mask ROM of
its NEC uPD78C11, kept uncommitted as
`docs/local/commodore-mps-803/mps803_78c11.bin` (SHA-1
69ee52b09d87ac3c0a5105a4f0af1e862d2a5814). The ROM holds both the control
program and the character generator. What the tools find is written up in
`docs/commodore-mps-803-firmware.md`; the manuals' account of the printer
is in `docs/commodore-mps-803.md`.

- `mps803-map.txt` is the map of the program, in our own words, from which
  `tools/rom-map/disassemble.py` writes the annotated disassembly,
  `docs/local/commodore-mps-803/mps803_78c11.dis`. Run
  `uv run python tools/rom-map/disassemble.py tools/mps803-rom/mps803-map.txt`;
  add to the map as tracing finds things, and run it again.

The character generator, with the code-to-glyph tables for both character
sets, is dumped in `docs/local/commodore-mps-803/mps803-characters.txt`.
