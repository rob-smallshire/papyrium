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
- `extract.py` writes the fonts of `papyrium.font.kx_p1080` from the
  EPROM and `KX-P1080U-internal.bin`, the internal ROM transcribed from
  that printout: draft and draft italic as the internal ROM stores them,
  NLQ built from the EPROM as the printer builds it, and NLQ italic
  slanted as the printer slants it. Run
  `uv run python tools/kx-p1080-rom/extract.py`.
- `read_dump_scan.py` reads a scan of that printout back into
  `KX-P1080U-internal.bin` and its transcript: it fits each line's
  character grid, learns the sixteen digits from the scan itself, starting
  from the line addresses, accepts a line only if its checksum holds, and
  reads every accepted character again by its nearest neighbours on other
  lines. Lines it cannot read are listed to be read by eye and given in a
  file of hand readings, whose checksums are checked too. Run
  `uv run --with numpy --with pillow python tools/kx-p1080-rom/read_dump_scan.py SCAN_PDF_FILEPATH [HAND_READINGS_FILEPATH]`;
  it needs `pdftoppm` (Poppler). How it came to work is told in
  `docs/panasonic-kx-p1080-rom-recovery.md`.
