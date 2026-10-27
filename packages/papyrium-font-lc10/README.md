# papyrium-font-lc10

The Star LC-10's fonts, extracted from the printer's firmware ROM (the
LC-10 Colour's, version 1.5) by `tools/lc10-rom/extract.py`. The
characters are Star's; the ROM itself is not distributed.

| Font | Typeface |
|---|---|
| `lc10-draft` | Draft |
| `lc10-nlq-courier`, `lc10-nlq-courier-elite` | Courier |
| `lc10-nlq-sanserif`, `lc10-nlq-sanserif-elite` | Sanserif |
| `lc10-nlq-orator`, `lc10-nlq-orator-elite` | Orator with lower case |
| `lc10-nlq-orator-small-capitals`, `lc10-nlq-orator-small-capitals-elite` | Orator with small capitals |

Each covers ASCII, the national characters, the slashed zero, the IBM PC's
low symbols and the upper half of its character set, less the block and
box drawing characters and the integral halves, which the printer draws
differently.

Draft glyphs are 9 rows by 11 columns 1/120 inch apart, the last two left
for spacing; a character with a descender sits a pin lower. NLQ glyphs are
18 rows, the first pass's pins on even rows and the second's, half a dot
lower, on odd rows, a descender two rows lower; columns are 1/240 inch
apart, 24 to the pica cell and 20 to the elite, each character placed in
its cell as the printer places it. The elite fonts narrow the widest
characters. The glyphs are in the package's `.txt` files, in the Papyrium
dot font text format.

The ROM has no italic characters: the printer slants the upright ones.
