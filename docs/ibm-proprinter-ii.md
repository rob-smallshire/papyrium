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
  between them, half a row down: a vertical line becomes solid (TR 4-3).
  Dots with a row between them are not joined.
- Between two dots in successive rows one or two columns apart, a dot
  halfway between them, half a row down: a diagonal fills in, whether it
  moves a column or two to a row (TR 4-4).
- No diagonal dot is added from a dot inside a line, with dots either
  side of it in its row or above and below it in its column: a diagonal
  joins a line only at its end. Where a diagonal meets a horizontal line
  at its end, the join is a vertical one (the Z of TR 4-6); a diagonal
  meets the end of a vertical line (the M of TR 4-7), and to meet one
  part way a design gives a horizontal dot at the meeting, whose end the
  diagonal joins (the K of TR 4-7). A vertical line still joins a
  horizontal one it crosses (the T of TR 4-5).

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

## Command details (G 4-4 to 4-35)

The guide describes the original Proprinter's commands; the Proprinter
II has them all.

- **BS** moves back one character width at the current spacing; at the
  first column it is ignored. **CAN** clears the line not yet printed,
  leaving the print position where it is (G 4-4).
- **CR** prints and returns to the left; it also feeds a line with switch
  3 on or after `ESC 5 1`. With character set 1, code 141 is CR without
  bit 7 being a character code (G 4-5).
- **DC2** cancels condensed and 12 cpi, not double width. **DC3** is
  ignored. **DC4** ends SO's double width, returning to the previous
  spacing (G 4-6).
- **FF** feeds to the next top of form and returns the carriage. **HT**
  goes to the next tab stop, and is ignored if it is past the right
  margin; power-on tabs are every eight columns from column 9 (G 4-6).
- **SI** is condensed, 17.1 cpi, until DC2. **SO** doubles the width until
  CR, CAN, LF, FF, VT, `ESC W` or DC4 (G 4-7).
- **VT** feeds to the next vertical tab stop, returning the carriage with
  switch 6 on; with no stops set, or the next beyond the form (less any
  perforation skip), it is a line feed (G 4-8).
- **`ESC A` n** keeps n/72 inch, 1 to 85, for `ESC 2` to bring into force;
  line feeds before `ESC 2` keep the old spacing. With n = 0 the previous
  `ESC A` value stays, or 1/6 inch if there was none (G 4-9). **`ESC 2`**
  brings the kept spacing into force, 1/6 inch if `ESC A` was never sent
  (G 4-25).
- **`ESC B`** sets up to 64 vertical stops in lines, line 1 being the top
  of form; it replaces the previous stops, and `ESC B 0` or `ESC R`
  clears them (G 4-10).
- **`ESC C` n** sets the form length in lines (at most 255) from the
  current spacing, kept as a distance, and makes the current line the top
  of form; **`ESC C 0` n** sets it in inches, n = 0 being ignored. Both
  cancel the perforation skip (G 4-11, 4-12).
- **`ESC D`** sets up to 28 horizontal stops, ascending, ended by 0;
  `ESC D 0` clears them and `ESC R` restores the power-on stops (G 4-12).
- **`ESC E`** strikes each character twice, the smallest possible distance
  apart, at half speed. **`ESC G`** (double strike) prints in NLQ
  (G 4-13).
- **`ESC I` n**, on the original Proprinter: 0 draft, 2 NLQ, 4 draft from
  the download font, 6 NLQ from it (G 4-14); the Proprinter II adds 1, 3,
  5 and 7 (TR 3-4).
- **`ESC J` n** feeds n/216 inch once, 1 to 255; it returns the carriage
  with switch 6 on and ignores the perforation skip (G 4-15).
- **`ESC K`, `L`, `Y`, `Z`**: bit-image graphics at 60, 120 (half speed),
  120 (no dot in the column after a printed one) and 240 dots an inch
  (half speed, no adjacent dots), on the top eight wires, bit 7 the top;
  bytes beyond the 8-inch line are dropped (G 4-16 to 4-24).
- **`ESC N` n** skips n lines (1 to 255) at the end of each form, kept as
  a distance; a new form length cancels it. **`ESC O`** cancels it
  (G 4-19).
- **`ESC Q 3`** deselects the printer until DC1 or a reset. **`ESC R`**
  restores the power-on horizontal tabs and clears the vertical ones
  (G 4-20).
- **`ESC S` n** is superscript (0) or subscript (1); **`ESC T`** ends it
  (G 4-21). **`ESC W` n** doubles the width on (1) or off (0), and ends
  SO's (G 4-22).
- **`ESC _` n** and **`ESC -` n** overscore and underscore what follows,
  spaces included but not a tab's gap (G 4-28, 4-29). **`ESC :`** is 12
  cpi until DC2 (G 4-29).
- **`ESC 6`** and **`ESC 7`** choose character set 2 and 1, overriding
  switch 5 (G 4-27, 4-28).
- **`ESC \` n1 n2** prints the next n1 + 256 n2 bytes as characters from
  the All Characters Chart, with no control codes acting, an unassigned
  code printing a space; **`ESC ^`** prints one such character (G 4-33,
  4-34).
- **`ESC =`** on the original Proprinter downloads up to 94 characters,
  codes 33 to 126, with one attribute byte (0 ascending, 1 descending)
  where the Proprinter II takes two (G 4-30, 4-31; TR 4-13). Reset does
  not clear the download font or its selection (G 4-32).

Mixing print modes (G 4-35): condensed with emphasized prints
emphasized, condensed with 12 cpi prints 12 cpi, condensed with NLQ
prints condensed, NLQ with emphasized prints emphasized, and 10 cpi and
12 cpi, or superscript and subscript, take whichever came last. Block
graphics (176-223 and 244) are never underscored or overscored.

## Character sets (G 4-36 to 4-38)

- **Character set 1**: codes 0-31 are controls or print nothing; 32-126
  ASCII; 128-159 are the controls with bit 7 set (BEL at 135, ESC at
  155), the rest printing nothing; 160-254 the IBM PC characters of
  code page 437; 255 a space.
- **Character set 2**: as set 1, but 3, 4, 5 and 6 print the card suits
  and 21 the section sign, and 128-159 are the IBM PC characters (Ç, ü,
  é, ...).
- **All Characters Chart**, for `ESC \` and `ESC ^`: every code, the low
  ones as the IBM PC's symbols.

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

## Where Papyrium decides

The manuals leave some combinations open; the `proprinter` language
(`papyrium.language.proprinter`) settles them so:

- Double strike (`ESC G`) prints NLQ with the draft face chosen; where
  condensed or a script masks NLQ, it prints draft struck twice.
- Condensed (unless 12 cpi masks it) and super- and subscript mask NLQ and
  NLQ II; emphasized masks NLQ only, since NLQ II has an emphasized form
  (TR 4-8).
- Fastfont masks condensed, as 12 cpi does, and ignores `ESC G`.
- `ESC X` counts its columns as the Star LC-10's manual shows for its IBM
  mode: `ESC X 12 92` leaves twelve elite columns, an inch, to the left.
- NLQ II download characters are skipped, their bytes counted; the
  Figure A-1 widths are not yet used, proportional characters taking
  their width from their dots; double height prints at single height.

## Open questions

- Which characters to print with: no Proprinter II ROM is to hand, and
  the guide's printed samples (G 1-6, 1-7) cover only some 35 characters,
  too few and too blurred for a dot-accurate font. Papyrium uses the Star
  LC-10's characters as a stand-in until a self-test printout or the ROM
  is available.
