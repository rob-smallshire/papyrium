# m1109-glyphs

One-off tools that reconstructed the Brother M-1109's draft characters
(`packages/papyrium-font-m1109-draft`) from the printed pages of its
owner's manual. They read the 400 dpi page scans in `docs/local/m1109/`,
which are not committed, and write their working files there.

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

Run them with numpy and scipy alongside the workspace, from this
directory, for example:

    uv run --project ../.. --with numpy --with scipy python build_font.py \
        ../../packages/papyrium-font-m1109-draft/src/papyrium/font/m1109_draft/glyphs.txt
