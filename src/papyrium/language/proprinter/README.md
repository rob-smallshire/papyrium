# papyrium.language.proprinter

The IBM Proprinter's printer language, as its 9-wire printers speak it,
for Papyrium. It is written from IBM's Proprinter manuals, restated in
`docs/ibm-proprinter-ii.md`, not from any other implementation.

`ProprinterInterpreter` shares the ESC/P interpreter's machinery (the
line buffer, paper motion, forms, tabs, bit-image graphics and the
character generator) and has the Proprinter's own command table, in which
many letters mean something other than Epson's. A printer model describes
itself with a `ProprinterMechanism`: its draft characters, its Fastfont
and NLQ II faces where it has them, its paper, and its switches.

Covered: 10, 12 and 17.1 cpi and proportional spacing; the faces `ESC I`
chooses, draft, Fastfont, NLQ and NLQ II, resident or downloaded, with
NLQ made from the draft characters by the printer's own rule
(`nlq_from_draft`); how condensed, 12 cpi, emphasized, NLQ and the scripts
mask one another; emphasized, double-strike, double width (continuous and
for one line), underscore and overscore, super- and subscript; character
sets 1 and 2 and the All Characters Chart (`ESC \` and `ESC ^`); line
spacing in 1/8, 7/72, n/72 (`ESC A`, brought into force by `ESC 2`) and
n/216 inch; form length, top of form, perforation skip, vertical and
horizontal tabs numbered from 1, margins; bit-image graphics (`ESC K`,
`L`, `Y`, `Z`); draft download characters (`ESC =`), with line drawing
and shading; switches 1, 3, 5 and 6.

Proportional spacing takes each character's width and offset from IBM's
table (`PROPORTIONAL_WIDTHS`), in draft and, on its finer grid, in NLQ;
download characters take theirs from their attribute byte.

NLQ II download characters (`ESC =` with printer ID 21) print with
`ESC I 7`. Not yet: double height, which IBM's manuals do not describe
for the 9-wire printers.

Registered as `proprinter` on the `papyrium.language` axis.
