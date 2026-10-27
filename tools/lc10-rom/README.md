# lc10-rom

Tools that read the Star LC-10 Colour's firmware ROM, kept uncommitted as
`docs/local/star-lc10/LC10-NX1P-1.5CL.bin`. What they have found is
written up in `docs/star-lc10-firmware.md`.

- `extract.py` decodes the ROM's character tables into the dot font files
  of `papyrium-font-lc10`.
- `disassemble.sh` disassembles the program with MAME's `unidasm`
  (architecture `m740`), used as a tool only, into
  `docs/local/star-lc10/LC10-NX1P-1.5CL.dis`. Build `unidasm` from a MAME
  checkout with `make EMULATOR=0 TOOLS=1 NOWERROR=1`; the script looks for
  it in `docs/local/m50734/`.
