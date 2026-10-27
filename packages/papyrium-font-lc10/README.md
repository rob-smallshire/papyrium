# papyrium-font-lc10

The Star LC-10's fonts, extracted from the printer's firmware ROM (the
LC-10 Colour's, version 1.5) by `tools/lc10-rom/extract.py`. The
characters are Star's; the ROM itself is not distributed.

| Font | Typeface |
|---|---|
| `lc10-draft`, `lc10-draft-elite` | Draft |
| `lc10-block-graphics` | IBM block graphics |
| `lc10-nlq-courier`, `lc10-nlq-courier-elite` | Courier |
| `lc10-nlq-sanserif`, `lc10-nlq-sanserif-elite` | Sanserif |
| `lc10-nlq-orator`, `lc10-nlq-orator-elite` | Orator with lower case |
| `lc10-nlq-orator-small-capitals`, `lc10-nlq-orator-small-capitals-elite` | Orator with small capitals |

The draft and NLQ fonts cover ASCII, the national characters, the
slashed zero, the IBM PC's low symbols and the upper half of its
character set, less the block and box drawing characters and the
integral halves, which are `lc10-block-graphics`: 12 rows by 11 columns,
1/72 by 1/120 inch, the printer repeating each column's two lowest dots
below the line so that lines at 1/6 inch spacing join.

Draft glyphs are 9 rows by columns 1/120 inch apart, 12 for pica and the
ROM table's 11 for elite; a character with a descender sits a pin lower. The ROM's draft table is used only for
elite; the printer makes pica draft from Sanserif's second NLQ pass at
half width, and `lc10-draft` is made the same way when it is loaded,
from `lc10-nlq-sanserif` or a Sanserif given in its place. NLQ glyphs are
18 rows, the first pass's pins on even rows and the second's, half a dot
lower, on odd rows, a descender two rows lower; columns are 1/240 inch
apart, 24 to the pica cell and 20 to the elite, each character placed in
its cell as the printer places it. The elite fonts narrow the widest
characters. The glyphs are in the package's `.txt` files, in the Papyrium
dot font text format.

The ROM has no italic characters: the printer slants the upright ones.
