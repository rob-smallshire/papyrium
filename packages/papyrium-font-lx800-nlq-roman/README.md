# papyrium-font-lx800-nlq-roman

lx800-nlq-roman is the Epson LX-800's near letter quality Roman characters, extracted from the printer's
firmware ROM by `tools/lx800-rom/extract.py`. The characters are
Epson's; the ROM itself is not distributed. It covers printable ASCII and
the 32 international characters of the ESC/P national sets.

Glyphs are 18 rows by 24 columns: the first pass's pins on even rows and the second's on odd rows, the ninth pin on rows 16 and 17; columns 1/240 inch apart, most characters drawn on every other one, the widest on every one. As in the ROM, dots may stand in successive columns;
the printer prints such a dot once. The glyphs are in `glyphs.txt`, in
the Papyrium dot font text format.

Registered as `lx800-nlq-roman` on the `papyrium.font` axis.
