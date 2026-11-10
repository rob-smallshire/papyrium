# papyrium.font.kx_p1080

The Panasonic KX-P1080U's fonts, extracted from the printer's firmware by
`tools/kx-p1080-rom/extract.py`: draft from the CPU's internal mask ROM,
which the printer was made to print as a hex dump
(`docs/panasonic-kx-p1080-rom-recovery.md`), and near letter quality from
its EPROM. The characters are Panasonic's; the ROMs themselves are not
distributed. Each covers printable ASCII, the 32 international characters
of the ESC/P national sets and the slashed zero.

kx-p1080-draft has glyphs of 9 rows, pins 1-9, by 12 columns 1/120 inch
apart, the last three blank. The ROM lowers a character's columns two
pins one by one, so a j's hook reaches the ninth pin while its stem does
not. As in the ROM, a few characters have a dot in successive columns.

kx-p1080-draft-italic is the ROM's own draft italics, stored slanted,
laid out as kx-p1080-draft.

kx-p1080-nlq has glyphs of 18 rows by 24 columns: the first pass's pins on
even rows and the second's on odd rows, a character with a descender a
pin lower; columns 1/240 inch apart. It is built as the printer builds it
from the EPROM's compressed columns, so no pin fires in successive columns.

kx-p1080-nlq-italic is kx-p1080-nlq slanted as the printer slants it at
print time: each pass's pins in pairs, each pair one column further right
than the pair below.

The glyphs are in `draft.txt`, `draft-italic.txt`, `nlq.txt` and
`nlq-italic.txt`, in the Papyrium dot font text format. Registered as
`kx-p1080-draft`, `kx-p1080-draft-italic`, `kx-p1080-nlq` and
`kx-p1080-nlq-italic` on the `papyrium.font` axis.
