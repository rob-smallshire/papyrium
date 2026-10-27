# papyrium.font.lx800_draft

lx800-draft is the Epson LX-800's draft characters, extracted from the printer's
firmware ROM by `tools/lx800-rom/extract.py`. The characters are
Epson's; the ROM itself is not distributed. It covers printable ASCII and
the 32 international characters of the ESC/P national sets, and the
slashed zero.

Glyphs are 9 rows by 11 columns 1/120 inch apart, the last two left for spacing; a character with a descender sits a pin lower, on the ninth pin. As in the ROM, dots may stand in successive columns;
the printer prints such a dot once. The glyphs are in `glyphs.txt`, in
the Papyrium dot font text format.

Registered as `lx800-draft` on the `papyrium.font` axis.
