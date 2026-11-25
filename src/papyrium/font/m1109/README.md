# papyrium.font.m1109

m1109-draft is the Brother M-1109's draft character set, the Centronics
GLP II's, reconstructed for Papyrium from the printed pages of the
printer's 1985 owner's manual: its character tables and the program
listings it printed. The dot patterns were fitted to scans in which
neighbouring dots merge; the printable ASCII characters' dots have since
been taken from the first-edition Centronics GLP's firmware (the
Schneider NLQ401's EPROM), which holds the same design, placed at the
heights the M-1109 prints them, which corrected 15 characters
(`tools/nlq401-rom/correct_m1109_draft.py`). The international characters
are still the manual's estimates, and the slashed zero, which the manual
never shows, is composed from the zero and the slash.
`tools/m1109-glyphs/` holds the tools that made it.

Glyphs are 11 columns by 9 rows: capitals 7 dots high, a lowercase
x-height of 5 dots and 2 rows of descender. As on the real head, no pin
strikes in two successive columns. It covers printable ASCII, the 32
international characters of the ESC/P national sets and a slashed zero
(`U+0030 U+0338`). The glyphs are in `draft.txt`, in the Papyrium dot
font text format.

Registered as `m1109-draft` on the `papyrium.font` axis; the
`centronics-glp-ii` model (and its badges, such as `brother-m1109`) prints with it by default, and with
`m1109-nlq` in near letter quality.

m1109-nlq is the Brother M-1109's near letter quality character set,
reconstructed for Papyrium from the one NLQ sample in the printer's 1985
owner's manual (page 74), which prints each character from 33 to 126 once.
No ROM was read.

An NLQ character is the nine pins struck in two passes 1/216 inch apart,
so a glyph is 18 rows, the first pass's pins on even rows and the
second's on odd rows, by 24 columns 1/240 inch apart across the pica
cell. In the sample the dots merge into solid strokes, so many dot
patterns would print the same: these are sparse patterns fitted to print
the same shapes, not the ROM's exact dots. The capitals start on row 2
and stand on the same pin as the draft capitals.

It covers printable ASCII. The international characters have no NLQ form
here, since the manual shows none; the printer prints those, as it does
any character without an NLQ form, in draft struck twice.

Registered as `m1109-nlq` on the `papyrium.font` axis; the
`centronics-glp-ii` model prints near letter quality with it by default.
`tools/m1109-glyphs/` holds the tools that made it.
