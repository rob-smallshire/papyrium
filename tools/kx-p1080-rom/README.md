# kx-p1080-rom

Tools for the Panasonic KX-P1080U's firmware, kept uncommitted as
`docs/local/panasonic-kx-p1080/KX-P1080U.BIN`. What they have found is
written up in `docs/panasonic-kx-p1080.md`.

- `kx-p1080-map.txt` is the map of the EPROM's program, in our own words,
  from which `tools/rom-map/disassemble.py` writes the annotated
  disassembly, `docs/local/panasonic-kx-p1080/KX-P1080U.dis`. Run
  `uv run python tools/rom-map/disassemble.py tools/kx-p1080-rom/kx-p1080-map.txt`.
- `dump_patch.py` makes an EPROM image that has the printer print its
  CPU's internal ROM, which holds the draft fonts and is not in the dump,
  and the job that prints it: `KX-P1080U-dump.bin`, to program into a
  27128 in place of the original, and `dump-job.prn`, to send to the
  printer's parallel port with the print mode switch at Std. Pgm. Each
  page of the internal ROM prints twice as bit-image columns, bit 7 the
  top pin, labelled in draft, with two pages of known EPROM bytes to check
  the reading of a scan by.
