# nlq401-rom

Tools for the Schneider NLQ401's firmware, its 16K EPROM Rev 004, kept
uncommitted as `docs/local/schneider-nlq401/schneider_nlq401_rev004.bin`
(SHA-1 b6374abaebb8e484e573caa21b1cc87f1554c8d6, as MAME's `nlq401`
device lists it). The NLQ401 is the Centronics GLP (Model 3101) with
Schneider's near letter quality, so this firmware is the best source for
the first-edition GLP. What the tools find is written up in
`docs/schneider-nlq401-firmware.md`.

- `nlq401-map.txt` is the map of the program, in our own words, from which
  `tools/rom-map/disassemble.py` writes the annotated disassembly,
  `docs/local/schneider-nlq401/schneider_nlq401_rev004.dis`. Run
  `uv run python tools/rom-map/disassemble.py tools/nlq401-rom/nlq401-map.txt`;
  add to the map as tracing finds things, and run it again.
