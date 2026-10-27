# m1109-glyphs

One-off tools that reconstructed the Brother M-1109's draft characters
(`papyrium.font.m1109`) from the printed pages of its
owner's manual. They read the 400 dpi page scans in
`docs/local/brother-m1109/m1109-user-guide-pages/` and write their working
files to `docs/local/brother-m1109/glyph-work/`; neither is committed.

The scan cannot resolve neighbouring dots, so dots are fitted rather than
read: for each character, the dot pattern on the printer's lattice (rows
1/72 inch apart, half-columns 1/120 inch apart, never two adjacent in a
row) whose rendering best matches the scans.

1. `ocr.sh` OCRs each page image (pages extracted with `pdfimages -png`).
2. `cache.py` deskews the fourteen character table pages and finds their
   16 x 16 cells (`cells.py`, `glyphs.py`).
3. `calibrate.py` estimates the reproduction scale and dot size.
4. `extract.py` fits each character jointly to all its copies across the
   twelve Mode I national tables (`fit.py`), writing `fits.json`.
5. `classify.py` finds the characters in the manual's program listings,
   which are the printer's own output at actual size, giving exact rows
   and columns (`lines.py`, `positions.py`, `punctuation.py`); the tables
   are pasted up and their columns drift.
6. `build_font.py` places each fitted shape in the 9 x 11 matrix and
   writes the font.

The near letter quality characters (`papyrium.font.m1109`)
come from the one NLQ sample, on page 74: `nlq.py` fits each character in
its own cell on the 18 x 24 NLQ grid, with a cost per dot so the pattern
stays sparse, and `build_nlq_font.py` aligns the sample lines by their
baselines and writes the font.

Run them with numpy and scipy alongside the workspace, from this
directory, for example:

    uv run --project ../.. --with numpy --with scipy python build_font.py \
        ../../src/papyrium/font/m1109/draft.txt
