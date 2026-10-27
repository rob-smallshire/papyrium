# IBM Proprinter II behaviour notes

Facts about the IBM Proprinter II (4201-002) that Papyrium's
`ibm-proprinter-ii` printer model and its `proprinter` language rely on,
restated in our own words from IBM's manuals. The Star LC-10's IBM mode
emulates this printer, so per the emulation rule it is modelled first,
from its own documents, and the LC-10's IBM mode is built on it
(`docs/star-lc-10.md`, `docs/star-lc10-firmware.md`).

Sources, kept uncommitted in `docs/local/ibm-proprinter/`:

- *IBM Proprinter Family Technical Reference*, cited as "TR" with the
  section-page numbers printed on its pages (TR 2-6). It covers the whole
  family; where a fact differs by model, these notes give the Proprinter
  II's.
- *IBM Proprinter Guide to Operations*, first edition (April 1985), cited
  as "G" with its printed section-page numbers (G 1-7). It is the guide to
  the original Proprinter (4201-001), which the Proprinter II extends. Its
  PDF has the pages a-b and i-xii before page 1, so page n of the
  continuous numbering 1-186 is PDF page n + 14.

Where the manuals are silent, the Star LC-10's firmware, a contemporary
implementation of this command set, is evidence of how such a printer
behaved, and is marked as such.

## Models in the family (TR 2-6, 4-1 to 4-21)

Nine-wire printers: the Proprinter (4201-001), Proprinter XL, Proprinter
II, Proprinter II XL, Proprinter III and Proprinter III XL. The XL models
have a 13.6-inch line; the Proprinter II has an 8-inch line. The
Proprinter II adds to the original Proprinter:

- **Fastfont**, a 12 cpi draft face of its own (`ESC I 1`).
- **NLQ II**, a second near letter quality face on a two-pass grid, beside
  the original **NLQ**, which the printer makes from the draft characters
  (below).
- Proportional spacing (`ESC P n`) and both margins at once (`ESC X`),
  which the original Proprinter lacks (TR 3-6, 3-7).
- Two download areas: one for draft or Fastfont characters, one for NLQ
  II characters, the latter only with the optional 8K buffer (TR 4-9).

The 24-wire Proprinters (X24, XL24 and their E models) are a different
design and out of scope.

## Switches (TR 2-6, 2-7)

Eight switches; in the U.S. and Canada the factory setting is 7 on and
the others off.

| Switch | On | Off |
|---|---|---|
| 1 | Ignore a form feed received at the top of a form with nothing printed on the page | Every form feed advances one form length |
| 2 | The panel's NLQ selects NLQ | The panel's NLQ selects NLQ II |
| 3 | Line feed after every CR (`ESC 5` overrides) | CR only returns |
| 4 | 12-inch forms (`ESC C` overrides) | 11-inch forms |
| 5 | Character set 2 (`ESC 7` overrides) | Character set 1 (`ESC 6` overrides) |
| 6 | Carriage return after LF, VT and `ESC J` | Those only feed |
| 7 | Reserved, always on | |
| 8 | Reserved, always off (some printers lack it) | |

## Character faces

### Draft (TR 4-1)

A cell twelve dots wide and nine high, columns 1/120 inch apart; a
character may use the first eleven columns, the twelfth staying blank,
and usually no more than nine, from column 1. A character prints on at
most eight of the nine wires: an ascending one on the top eight, a
descending one on the bottom eight. Ascenders use the top seven rows,
with row 7 as the base line; descenders the bottom seven. In draft the
printer drops a dot that follows a printed one in the same row (TR 4-3).

### Fastfont (TR 4-8)

12 cpi draft: a cell ten dots wide and nine high, at most nine columns,
the tenth blank; wider characters are cut off. It cannot print in NLQ.

### NLQ, made from the draft characters (TR 4-3 to 4-7)

The Proprinter's NLQ has no characters of its own: the printer prints
the draft characters in two passes, adding dots in the second, half a dot
lower, and prints every dot of a horizontal line, which draft would thin.
The added dots, from the manual's drawings:

- Between two dots in successive rows of the same column, a dot halfway
  between them, half a row down: a vertical line becomes solid.
- Between two dots in successive rows of neighbouring columns, a dot
  halfway between them, half a row down and half a column across: a
  diagonal fills in.
- No diagonal dot is added from a dot inside a horizontal line, one with
  dots either side of it in its row: where a vertical or a diagonal meets
  a horizontal line, the meeting is treated as a two-dot vertical line
  (TR 4-5, 4-6). The ends of a horizontal line, and dots standing alone,
  do make diagonals (the `M` and `K` of TR 4-7).

The half rows and half columns fall on a grid of 1/240 inch columns and
1/144 inch rows, two passes of the nine wires: 24 columns by 18 rows to
the pica cell, the same grid as NLQ II's. Downloaded draft characters
print in NLQ the same way; a design meant for both must give every dot of
its horizontal lines (TR 4-3).

### NLQ II (TR 4-8)

A face of its own on a grid 24 dots wide and 18 high, in two passes: at
most 23 columns, the 24th blank, and at most 16 rows, from row 1 for an
ascender or row 3 for a descender. Ascenders use the top 15 rows, with
row 15 as the base line; descenders rows 3 to 18. Capitals use rows 2 to
15, small letters such as a, c and e rows 6 to 15, ascenders rows 1 to
15 and descenders rows 6 to 18. Dots in successive columns of a row are
dropped, except in emphasized printing.

### Block graphics (TR 4-11, 4-14)

Line-drawing and shading characters are 12 dots high: the cell's row 8
is extended downward through rows 9 to 12 for line drawing (characters
179 to 223), and rows 1 to 4 are repeated as rows 9 to 12 for shading
(176 to 178), which NLQ leaves as it is. (The Star LC-10 instead repeats
its block characters' last two rows; `docs/star-lc10-firmware.md`.)

### Proportional widths (TR A-1 to A-8)

Figure A-1 gives the Proprinter II's proportional spacing for code page
437: for each of the 256 characters a width in dots and an offset in dot
spaces, the columns to skip before the character's printed columns.
Characters 0-32 are 12 dots with no offset, `!` 5 dots from column 4,
`"` 8 from 2, `'`, `(` and `)` 6 from 3, and so on.

## Command summary (TR 3-1 to 3-10)

| Bytes | Effect | Notes |
|---|---|---|
| BEL | Beep | |
| BS | Back one column | |
| HT | Next horizontal tab | |
| LF | Line feed | carriage return too with switch 6 |
| VT | Next vertical tab | |
| FF | Form feed | switch 1 |
| CR | Carriage return | line feed too with switch 3 or `ESC 5 1` |
| SO | Double width for the rest of the line | |
| SI | Condensed | |
| DC1 / DC3 | Select / deselect the printer | |
| DC2 | 10 cpi | |
| DC4 | Cancel SO's double width | |
| CAN | Cancel the line's data | |
| `ESC -` n | Underline on / off | |
| `ESC _` n | Overline on / off | |
| `ESC 0`, `ESC 1` | 1/8, 7/72 inch line spacing | |
| `ESC A` n | Keep n/72 inch spacing | in force at `ESC 2` |
| `ESC 2` | Bring `ESC A`'s spacing into force | |
| `ESC 3` n | n/216 inch spacing | |
| `ESC J` n | Feed n/216 inch once | |
| `ESC 4` | This line is the top of form | |
| `ESC 5` n | Line feed after CR on / off | overrides switch 3 |
| `ESC 6`, `ESC 7` | Character set 2, 1 | override switch 5 |
| `ESC :` | 12 cpi | |
| `ESC B` n... 0 | Vertical tabs | |
| `ESC C` n, `ESC C 0` m | Form length in lines, in inches | |
| `ESC D` n... 0 | Horizontal tabs | |
| `ESC E`, `ESC F` | Emphasized on, off | |
| `ESC G`, `ESC H` | Double-strike on, off | |
| `ESC I` n | Print mode (below) | |
| `ESC K`, `L`, `Y`, `Z` | Bit-image graphics | |
| `ESC N` n, `ESC O` | Skip n lines over the perforation; cancel | |
| `ESC P` n | Proportional spacing off (0) or on (1) | not on the original Proprinter |
| `ESC Q 3` | Deselect | |
| `ESC R` | All tabs to their power-on settings | |
| `ESC S` n, `ESC T` | Superscript (0) or subscript (1); cancel | |
| `ESC U` n | Unidirectional (1) or both ways (0) | |
| `ESC W` n | Double width on, off | |
| `ESC X` n m | Left and right margins | not on the original Proprinter |
| `ESC \` n1 n2 | Print n1 + 256 n2 characters from the All Characters Chart | |
| `ESC ^` | Print one character from the All Characters Chart | |
| `ESC [ @` ... | Presentation highlight | |
| `ESC =` | Download characters (below) | |

`ESC I` n chooses the face (TR 3-4): 0 draft, 1 Fastfont, 2 NLQ, 3 NLQ
II, from the resident characters; 4 to 7 the same from the download
areas.

## Download characters (TR 4-9 to 4-21)

- At power on the Proprinter II copies its resident draft characters to
  the draft download area; `ESC = 0 0` (or `ESC = 1 0 20`) does so again,
  and `ESC = 1 0 21` initializes the NLQ II area to the resident NLQ II
  characters (TR 4-10).
- `ESC =` count1 count2 20 start, then for each character two attribute
  bytes and eleven column bytes: count1 + 256 count2 is 13 times the
  number of characters plus 2; 20 is the printer ID for a font derived
  from the draft font; characters replace consecutive codes from start;
  up to 256 in one command (TR 4-11 to 4-13).
- Attribute byte 1: bit 7 set for a descender, clear for an ascender;
  bits 1-0 are 00 for an ordinary character, 01 for line drawing (row 8
  extended through row 12; bit 7 ignored) and 10 for shading (rows 1-4
  repeated as rows 9-12; bit 7 ignored, NLQ ignored) (TR 4-13, 4-14).
- Attribute byte 2, for proportional spacing: bits 6-4 the number of
  leading columns to skip, bits 3-0 the number of columns to print (more
  than 11 counts as 11), each character then followed by one blank column;
  all zero prints all eleven columns (TR 4-14).
- Column bytes: one bit a wire, bit 7 the top wire of the eight used
  (TR 4-15).
- The draft download area can hold a Fastfont instead; the NLQ II area
  needs the 8K buffer (TR 4-9, 4-19).

## Open questions

- The guide's command descriptions (G section 4), for the details the
  technical reference's summary leaves out, are still to be read.
- Which characters to print with: no Proprinter II ROM is to hand, and
  the guide's printed samples (G 1-6, 1-7) cover only some 35 characters,
  too few and too blurred for a dot-accurate font. Papyrium uses the Star
  LC-10's characters as a stand-in until a self-test printout or the ROM
  is available.
