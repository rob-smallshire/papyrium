# papyrium.font.glp

The Centronics GLP's (Model 3101) characters, extracted by
`tools/nlq401-rom/extract.py` from the firmware of the Schneider NLQ401,
which is the GLP with Schneider's near letter quality. The characters are
Centronics'. `docs/schneider-nlq401-firmware.md` describes where they are
in the ROM and how the firmware prints them.

glp-draft is the draft character set: 9 rows by 11 columns 1/120 inch
apart in a 12-column pica cell, ASCII and the German characters § Ä Ö Ü
ä ö ü ß of character set 2. The firmware prints ; _ g p q y a pin lower,
and so does the font. Its ASCII characters' dots are the same as the GLP
II's (`m1109-draft`), whose ASCII characters were corrected from this
ROM; three characters stand at different heights, the M-1109 printing
, : j a pin lower.

glp-graphics is the GLP's graphics, the Amstrad CPC's codes 129-255, which
the GLP prints after ESC =: 8 rows by 11 columns, six columns of dots 1/60
inch apart, so that block and line drawing characters join their
neighbours. Each glyph is keyed by its Unicode character, the Symbols for
Legacy Computing among them; three characters Unicode encodes only from
version 16 use U+E0EF, U+E0FC and U+E0FD in the Private Use Area.

Registered as `glp-draft` and `glp-graphics` on the `papyrium.font` axis.
