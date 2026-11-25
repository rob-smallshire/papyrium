# papyrium.language.cbm

The language of Commodore's serial bus printers, for Papyrium, as the
Commodore MPS-803 speaks it: PETSCII text in the graphic set (upper case
and graphics) or the business set (lower and upper case), double width,
reverse, quote mode, bit images with repeated columns, and positioning by
column or by dot.

`CbmInterpreter` follows the MPS-803's firmware, read from its ROM
(`docs/commodore-mps-803-firmware.md`): a line of 480 dots 1/60 inch apart
and seven wires 1/72 inch apart, wrapped lazily when the next item will
not fit; CR and LF alike, feeding 7/72 inch after a bit-image line;
positioning that only moves forwards; quote mode, in which control codes
print as reversed characters. `charset.py` turns a PETSCII code into the
character generator's glyph as the firmware does, for each set.

The serial bus's addressing does not reach Papyrium, which receives only
the bytes: the model chooses the set a job's secondary address would.

Registered as `cbm` on the `papyrium.language` axis.
