# lx800-rom

`extract.py` builds the Epson LX-800's fonts, `papyrium-font-lx800-draft`
and `papyrium-font-lx800-nlq-roman`, from the printer's firmware: the 32K
program ROM at IC3C, the dump MAME lists as `lx800.ic3c` (CRC32 da06c45b,
SHA-1 9618c940dd10d5b43cd1edd5763b90e6447de667). The ROM is Epson's; it
is kept uncommitted in `docs/local/epson-lx800/`, and using its characters
was Rob's decision for this ROM (2026-10-26).

## What the ROM holds

This dump is a Cyrillic variant of the firmware: its second NLQ typeface is
Cyrillic, not the Sans Serif of the Western LX-800, so Sans Serif cannot
come from it.

| Table | At | Holds |
|---|---|---|
| Draft characters | 0x2804 | 10-byte records for ROM locations -10 to 256 |
| NLQ international pointers | 0x3236 | 33 pointers: locations 0-31 and one more |
| NLQ ASCII pointers | 0x3278 | 94 pointers: `!` to `~` |
| NLQ IBM symbol pointers | 0x3336 | 52 pointers: `Ç â ê ...` and the Greek and mathematical signs |
| NLQ Cyrillic pointers | 0x444E | the Cyrillic alphabet, `Ё ё`, arrows, `№` |

**Draft records** are a byte whose use is not known, then 9 columns of 8
dots, bit 7 the top dot and a 0 bit a dot. Record *r* is ROM location
*r* - 10: the 32 international characters (locations 0-31, in the order
of `papyrium.language.escp.charsets`), ASCII (32-126), the slashed zero
(127), then the IBM graphics characters and the Cyrillic, which are not
decoded yet. A character that leaves its top row empty and uses its bottom
row is printed a pin lower, its descender on the ninth pin. Characters
are stored with dots in successive columns, which the printer prints once.

**NLQ records** are a header byte, then for each of the two passes the
ninth pin's dots, if the header asks for them, and the columns of the
eight upper pins. A header of 0xFF is followed by a flags byte (bit 7:
ninth pin) and a width, with columns 1/240 inch apart and the ninth pin's
dots taking a byte for each 8 columns; otherwise the header's bits 0-3
are the width and bits 4-6 a left offset, in 1/120 inch columns, and bit 7
asks for the ninth pin, two bytes a pass. The first pass's pins print the
even rows, the second's the odd rows; the ninth pin prints rows 16 and 17.

## Not yet extracted

The IBM graphics characters (draft records 138 on, whose later part has a
different layout), the NLQ IBM symbols, the 33rd NLQ international record,
and the Cyrillic in both qualities.
