# papyrium.font.m1109_draft

m1109-draft is the Brother M-1109's draft character set, reconstructed for
Papyrium from the printed pages of the printer's 1985 owner's manual: its
character tables and the program listings it printed. No ROM was read.
The dot patterns were fitted to scans in which neighbouring dots merge,
so they are a close estimate rather than a verified copy; the slashed
zero, which the manual never shows, is composed from the zero and the
slash. `tools/m1109-glyphs/` holds the tools that made it.

Glyphs are 11 columns by 9 rows: capitals 7 dots high, a lowercase
x-height of 5 dots and 2 rows of descender. As on the real head, no pin
strikes in two successive columns. It covers printable ASCII, the 32
international characters of the ESC/P national sets and a slashed zero
(`U+0030 U+0338`). The glyphs are in `glyphs.txt`, in the Papyrium dot
font text format.

Registered as `m1109-draft` on the `papyrium.font` axis; the
`brother-m1109` model prints with it by default, and with
`m1109-nlq` in near letter quality.
