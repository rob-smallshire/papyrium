# kx-p1080-rom

Tools for the Panasonic KX-P1080U's firmware, kept uncommitted as
`docs/local/panasonic-kx-p1080/KX-P1080U.BIN`. What they have found is
written up in `docs/panasonic-kx-p1080.md`.

- `kx-p1080-map.txt` is the map of the EPROM's program, in our own words,
  from which `tools/rom-map/disassemble.py` writes the annotated
  disassembly, `docs/local/panasonic-kx-p1080/KX-P1080U.dis`. Run
  `uv run python tools/rom-map/disassemble.py tools/kx-p1080-rom/kx-p1080-map.txt`.
- `dump_patch.py` makes `KX-P1080U-dump.bin`, an EPROM image whose self
  test prints the CPU's internal ROM, which holds the draft fonts and is
  not in the dump, as hex text: each line an address, sixteen bytes and
  their checksum, the whole 4 KB twice. Program it into a 27128 in place
  of the original EPROM and switch on holding LF, with the print mode
  switch at NLQ; it prints about eight pages and stops. Nothing else in
  the firmware changes.
