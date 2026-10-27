# papyrium.language.escp

Epson's ESC/P printer language, as spoken by 9-pin dot-matrix printers such
as the FX-80, for Papyrium. It is written from the published command
descriptions, not from any other implementation.

`EscpInterpreter` turns a byte stream into pages incrementally, so pages
appear as the paper is ejected and never depend on how the bytes were
chunked. A printer model describes itself with an `EscpMechanism`: its
character ROM (a Papyrium dot font), paper, head, power-on switch settings
and the ESC commands it obeys.

Covered: text with pica, elite, condensed and proportional pitch;
emphasized, double-strike, double-width (permanent and one-line), italic,
underline, superscript and subscript; the international character sets;
MSB control and printable high codes; line spacing in 1/6, 1/8, 7/72, n/72
and n/216 inch; form length, skip-over-perforation, vertical and horizontal
tabs, margins, backspace, DEL and CAN; bit-image graphics (`ESC K`, `L`,
`Y`, `Z`, `*`, `^` and `?`); user-defined characters (`ESC &`, `%`, `:`).

Registered as `escp` on the `papyrium.language` axis.
