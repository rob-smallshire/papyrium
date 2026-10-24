# Brother M-1109 behaviour notes

Facts about the Brother M-1109 that Papyrium's `escp` language and an
`m1109` printer model rely on, restated in our own words from Brother's
*M-1109 Owner's Manual* (1985). Page numbers are the printed ones (the
scan's image index is not the page number). The manual is copyrighted and
is kept, uncommitted, in `docs/local/m1109/`.

The scan lacks printed pages 100 (`ESC Y`), 106-107, 122-123 and 125;
what is said about those subjects below comes from other pages.

The M-1109 has two personalities chosen by DIP switch 2-2: Mode I, which
the manual calls Epson-compatible (a handwritten note in our copy says
"Epson FX-80"), and Mode II, IBM-compatible (handwritten "IBM Graphics
Printer"). Most of these notes are about Mode I, compared against
`docs/epson-fx80.md`; Mode II has its own section.

## DIP switches (6-9)

Two banks of ten. Bank 1 is the same in both modes:

| Switch | Factory | Meaning |
|---|---|---|
| 1-1, 1-2 | on, on | Interface: both on parallel; otherwise serial with no (1-1 off, 1-2 on), odd (on, off) or even (off, off) parity |
| 1-3 | on | Serial: send XON/XOFF |
| 1-4..1-6 | off, off, on | Baud rate, 1200 (110, 150, 300, 600, 1200, 2400, 4800, 9600 counting 1-4 as the low bit) |
| 1-7 | on | 8-bit data (off: 7-bit) |
| 1-8 | on | Unused |
| 1-9 | off | No skip-over-perforation (on: skip 1 inch at the bottom of each form) |
| 1-10 | off | Power on in draft (on: NLQ) |

Bank 2 in Mode I (2-2 on):

| Switch | Factory | Meaning |
|---|---|---|
| 2-1 | on | Form length 11 inches (off: 12 inches) |
| 2-2 | on | Mode I (off: Mode II) |
| 2-3..2-5 | off, off, off | National set; see below. 2-3 is set on for machines sold outside the USA |
| 2-6 | on | Plain zero (off: slashed zero) |
| 2-7 | on | Parallel: use the data buffer. Serial: XON when 153 bytes or fewer are waiting (off: 1936) |
| 2-8 | on | Unused |
| 2-9 | off | CR only (on: CR also feeds a line); ORed in effect with the AUTO FEED XT line |
| 2-10 | on | SLCT IN ignored (printer always selected) |

Switches 2-3, 2-4, 2-5 (2-3 the low bit) choose the power-on national
set: 0 USA, 1 England I, 2 Germany, 3 France, 4 England II, 5 Sweden,
6 Italy, 7 Spain. Denmark I, Japan, Norway and Denmark II can only be had
with `ESC R`. Note the switch order differs from `ESC R` numbering.

Bank 2 in Mode II (2-2 off): 2-1 form length as above; 2-3 on character
set 1, off character set 2; 2-4 on CAN ignored, off CAN obeyed; 2-5 on
1/8 inch, off 1/6 inch power-on line spacing; 2-6 on a full line buffer
prints with a line feed, off without; 2-7, 2-9, 2-10 as in Mode I; 2-8
unused. The manual gives no factory column for Mode II (9).

Unlike the FX-80 there is no switch for power-on condensed, emphasized,
paper-out sensing, beeper or the RAM's use; there is no beeper at all.

## Power-on state

Pica, draft (or NLQ by 1-10), line spacing 1/6 inch (Mode II: 1/6 or 1/8
by 2-5), form length 11 or 12 inches by 2-1 (66 lines at 1/6 inch),
horizontal tabs every 8 pica columns, no vertical tabs (VT acts as LF),
VFU channel 0 selected, national set by switch, internal (ROM) character
set, bidirectional printing, paper-out detection active, skip-over-
perforation of 1 inch only if 1-9 is on (31, 32, 35, 40, 42, 44, 75, 87,
92). The margins at power on are not stated; the full line is 80 pica
columns.

`ESC @` (Mode I only) returns to the power-on state and discards the text
buffer; the example (88) shows text sent before it on the same line is
lost. The manual does not say whether it erases downloaded characters.

## Top of form and paper (15-16, 21, 126, 135-140)

- Cut sheets are the standard paper: A4 (8.3 inches) or Letter (8.5
  inches), friction fed, left edge set against a scale on the paper guide.
  The optional PF-50 pin feed unit takes fanfold 4 to 10 inches wide
  (101.6-254 mm). The optional roll holder takes 8.5 or 8.3 inch rolls,
  70 mm maximum diameter.
- Printable line 8 inches. With the paper's left edge on the scale, the
  first column prints 3-7 mm in from the edge (140, roll paper; the cut
  sheet pages give no figure).
- On roll paper torn at the window cover's cutter, the next first line
  lies 18-22 mm below the torn edge, and the last line printed lies
  22-40 mm above the tear (140). The cut-sheet procedure only says to
  wind the sheet back to "the print start position" (16); no distance.
- The top of form is where the paper is at power on and when `ESC C`
  arrives (34-35); `ESC @` presumably also, as it repeats power-on.
- The carriage parks at the centre of the platen at power on and when
  deselected, to ease paper loading (15, 21).
- After paper-out is sensed, about 1/2 inch more (three lines at 1/6) is
  printed before the printer stops (21).

## Character formation and sizes (22, 98, 126-128)

- Nine-pin head; vertical dot pitch 1/72 inch; horizontal dot pitch 1/60
  inch in pica and 1/72 inch in elite. Characters are a "9 x 9 dot matrix
  (half dot 4)"; see Open questions.
- Downloaded characters (90) are 11 columns, alternately full-dot and
  half-dot positions (F H F H F H F H F H F), so the character grid is
  1/120 inch in pica with dots only on alternate columns in any row.
- Character widths in 1/60-inch dot units, used for mixing text and bit
  image on one line (98): pica and emphasized 6 (enlarged 12), condensed
  3.5 (7), elite 5 (10).
- Pitches (127): pica 10 cpi (80 per line), elite 12 (96), condensed pica
  17 (136; but SI and `ESC Q` say 137), enlarged 5, 6 and 8.5. Condensed
  elite is 20 cpi (55), which the FX-80 does not have.
- Printed character sizes (127): pica 2.4 x 2.0 mm, elite 2.4 x 1.7 mm,
  condensed 2.4 x 1.2 mm (height x width); enlarged doubles the width;
  super/subscript halves the height (1.2 mm).
- Speed 100 cps draft, 25 cps NLQ; 220 ms per 1/6 inch line feed (126).
- Buffers: a data buffer of about 2.2K, a print buffer of 1920 bytes
  holding one line as pin images, and a separate download buffer for
  user-defined characters (22). The download buffer does not share
  memory with text as on the FX-80 (no switch 1-4 equivalent).

## Mode I command summary (25)

Codes 128-255 with the top bit set act the same as the codes without it
for the control codes listed (NUL, BS, HT, LF, VT, FF, CR, SO, SI, DC2,
DC4, CAN, ESC, DEL).

| Command | Function | Page | Versus FX-80 |
|---|---|---|---|
| NUL | Ends `ESC B`/`ESC D` lists | 41 | |
| BS | Backspace | 84 | see below |
| HT | Horizontal tab | 31 | |
| LF | Line feed | 28 | |
| VT | Vertical tab | 32 | no default stops |
| FF | Form feed | 30 | |
| CR | Carriage return | 27 | |
| SO | Enlarged for the line | 53 | also cancelled by CAN |
| SI | Condensed | 55 | 20 cpi with elite |
| DC2 | Cancel condensed | 56 | |
| DC4 | Cancel SO enlarged | 54 | |
| CAN | Clear the text buffer | 86 | also cancels SO |
| `ESC ! n` | Master select | 68 | different priorities |
| `ESC #` | Cancel MSB control | 95 | |
| `ESC % n 0` | ROM or downloaded set | 92 | |
| `ESC & 0 n m ...` | Define characters | 90 | |
| `ESC * m n1 n2` | Bit image, mode m | 102 | modes differ |
| `ESC - n` | Underline | 62 | |
| `ESC / n` | Select VFU channel | 38 | |
| `ESC 0`, `ESC 1`, `ESC 2` | 1/8, 7/72, 1/6 inch spacing | 45-49 | |
| `ESC 3 n` | n/216 inch spacing, 0-255 | 50 | |
| `ESC 4`, `ESC 5` | Italic on, off | 67 | |
| `ESC 6`, `ESC 7` | Print 128-159, 255 / restore controls | 78-80 | |
| `ESC 8`, `ESC 9` | Ignore paper-out / sense it | 86-87 | |
| `ESC : 0 0 0` | Copy ROM to download buffer | 93 | |
| `ESC <` | Home the head | 87 | see below |
| `ESC =`, `ESC >` | Force bit 7 to 0 / to 1 | 94 | |
| `ESC @` | Initialize | 88 | |
| `ESC A n` | n/72 inch spacing, 0-85 | 44 | |
| `ESC B n... 0` | Vertical tabs, channel 0 | 37 | see below |
| `ESC C n`, `ESC C 0 n` | Form length in lines (1-127) or inches (1-22) | 34 | also clears vertical tabs |
| `ESC D n... 0` | Horizontal tabs, 1-132 | 36 | |
| `ESC E`, `ESC F` | Emphasized on, off | 57-59 | |
| `ESC G`, `ESC H` | Double-strike on, off | 60-61 | |
| `ESC I n` | Print or obey codes 0-31, 128-159 | 82 | different set of codes |
| `ESC J n` | Feed n/216 inch, 0-255 | 33 | |
| `ESC K/L/Y/Z n1 n2` | Bit image 480/960/960/1920 per 8 inches | 96-101 | |
| `ESC M`, `ESC P` | Elite on, off | 64-65 | |
| `ESC N n`, `ESC O` | Skip-over-perforation n lines (1-127), off | 42-43 | |
| `ESC Q n` | Right margin | 52 | enlarged ranges |
| `ESC R n` | National set 0-11 | 76 | three more sets |
| `ESC S n`, `ESC T` | Super (0) or subscript (1), off | 71-72 | |
| `ESC U n` | Unidirectional (1) or bidirectional (0) | 75 | |
| `ESC W n` | Enlarged on (1), off (0) | 59 | |
| `ESC b c n... 0` | Store VFU channel c (0-7) | 40 | |
| `ESC l n` | Left margin | 51 | enlarged ranges |
| `ESC p n` | Proportional on, off | 66 | |
| `ESC s n` | Quiet printing on, off | 89 | FX-80: half speed |
| `ESC x n` | NLQ on (1), off (0) | 73 | FX-80 lacks |
| DEL | Delete the last character | 85 | |

FX-80 features the M-1109 lacks in Mode I: BEL (code 7 is never a
control here), DC1 and DC3 (select and deselect), `ESC SO` and `ESC SI`
(the escaped forms of SO and SI), `ESC ?` (reassign K/L/Y/Z), `ESC ^`
(nine-pin graphics; pin 9 is never used for bit images), `ESC j`
(reverse feed), `ESC i` (immediate mode) and `ESC EM`. An unknown
command letter after ESC is discarded together with the ESC (24).

Commands the FX-80 lacks: `ESC x` (NLQ), `ESC R` 9-11, the quiet mode of
`ESC s`, condensed elite, and `ESC *` modes with different densities.

## Mode I command details

### Line ends and feeds (27-35)

- CR prints the buffer; it feeds a line too if 2-9 is on or AUTO FEED XT
  is low. A CR that also feeds cancels SO enlarged. A bare CR (or spaces
  then CR) with auto feed on just feeds, without moving the head.
- LF, VT and FF print the buffer, feed, and cancel SO enlarged. A feed
  that runs into the skip-over-perforation zone goes to the first line of
  the next form. FF with an empty buffer just feeds the form.
- `ESC J n` feeds n/216 inch, does not cancel SO, does not change the line
  spacing, and does not return the carriage: the next character prints at
  the next column on the new line. n = 0 prints the buffer without
  feeding.
- With `ESC A 0` or `ESC 3 0`, LF and VT act as CR and the panel LF key
  does nothing. With `ESC 3` n of 1 or 2 the feed accuracy is not
  assured.
- `ESC A n` ignores bit 7 of n; values 86-127 (and 214-255) are ignored.
- Double-strike, super/subscript and NLQ print in two passes 1/216 inch
  apart; the printer compensates so the line pitch is unchanged.

### Forms and vertical tabs (34-43)

- `ESC C n` (1-127 lines; bit 7 ignored) and `ESC C 0 n` (1-22 inches)
  set the top of form here, cancel skip-over-perforation, and clear the
  vertical tabs. The form is stored as a distance, so later spacing
  changes do not alter it.
- If the form is shorter than one line feed, VT acts as LF and skip-over-
  perforation is ignored; if the form length is 0, LF and VT act as CR.
- `ESC N n` skips the last n lines of each form; n = 0 is ignored and n
  should not exceed the form length. Stored as a distance. Switch 1-9
  gives 1 inch (60 lines printed, 6 skipped on an 11-inch form);
  `ESC C` or `ESC O` cancels it.
- `ESC B n1...nk 0`: up to 16 stops (n 1-254) in lines of the current
  spacing, kept as distances, in channel 0. A value not greater than the
  one before is skipped, not a terminator as on the FX-80; the list ends
  at NUL or after the sixteenth stop.
- `ESC b c m1... 0` stores channel c (0-7), as `ESC B` does for 0;
  `ESC / c` chooses which channel VT uses. Channel 0 is chosen at power
  on.
- VT goes to the next stop; at or past the end of the form, to the top of
  the next form. With no stops, VT is LF. VT cancels SO enlarged.

### Horizontal layout (31, 36, 51-52, 84)

- `ESC D n1...nk 0`: up to 32 stops, n 1-132, in columns of the current
  pitch, fixed thereafter, counted from the left margin. Ends at NUL, the
  32nd stop, or a value lower than the one before.
- `ESC l n` sets the left margin in columns of the current pitch, and
  resets the tabs relative to it. `ESC Q n` sets the right margin n
  columns from the head's home. Out-of-range values are ignored. Both
  should be sent at the start of a line, or the buffer contents are not
  assured. Ranges:

  | Pitch | `ESC l` | `ESC l` enlarged | `ESC Q` | `ESC Q` enlarged |
  |---|---|---|---|---|
  | Pica, emphasized | 0-78 | 0-39 | 2-80 | 1-40 |
  | Condensed | 0-133 | 0-66 | 4-137 | 2-68 |
  | Elite | 0-93 | 0-46 | 3-96 | 2-48 |

  The manual states no minimum gap between the margins (the FX-80 does).
- BS moves back one column of the current pitch; in enlarged it moves
  back a double pica column. It never moves left of the home position (a
  BS there is ignored) and is ignored in proportional mode.
- DEL removes the last character from the buffer; ignored in bit image.
  CAN empties the buffer and cancels SO enlarged, but no other mode.
- `ESC <` homes the head; printing continues from the next column. The
  manual cross-refers to `ESC U` but does not say it makes one line
  unidirectional as the FX-80's does.

### Print modes (53-73, 104)

- SO: enlarged until DC4, CAN, `ESC W 0`, `ESC @`, INIT, a CR that feeds,
  any LF, VT or FF (not `ESC J`), or a line feed caused by a full buffer.
  `ESC W 1` lasts until `ESC W 0`; DC4 does not cancel it. `ESC W 0`
  cancels both.
- SI: condensed until DC2. Pica becomes 17 cpi, elite 20 cpi; with
  enlarged, 8.5 cpi.
- `ESC E` is overridden by elite and itself overrides condensed;
  cancelling the winner reveals the loser.
- `ESC M` elite (12 cpi); `ESC P` back to pica, touching nothing else.
- `ESC p 1` proportional: always emphasized, BS and DEL are ignored.
  Downloaded characters carry their own proportional extents.
- `ESC G` double-strike is ignored under super/subscript, except that the
  underline is still struck twice.
- `ESC S 0/1`: superscript or subscript in the upper or lower half of
  the cell, printed unidirectionally in two passes 1/216 inch apart; they
  replace each other. Nothing but the underline is double-struck.
- `ESC - 1` underlines spaces as well as characters, but not the gap
  jumped by HT. Underline is double-struck under double-strike.
- `ESC 4` italic is ignored for bit images; `ESC 5` cancels it. Italic is
  absent from the mixing table and from `ESC !`; the manual does not
  restrict it otherwise.
- `ESC x 1` NLQ (73, 22): 10 cpi only, though proportional works. Only
  underline, super/subscript and enlarged combine with it; other modes
  set meanwhile are recorded and take effect when NLQ ends. Characters
  with no NLQ form are simply double-struck. Downloaded characters are
  not available under NLQ (`ESC % 1` then only sets its flag). NLQ
  characters are struck twice with a 1/216 inch feed between, within a
  frame 18 dots high (3.1 mm) and 20 dots wide (2.0 mm), always
  unidirectional, at 25 cps. The panel LF key toggles NLQ when online.

`ESC ! n` (68-70): bit 0 elite, 2 condensed, 3 emphasized, 4 double-
strike, 5 enlarged; bits 1, 6 and 7 are ignored, so there is no italic
or underline bit (as on the FX-80). It overrides the separate commands.
The combination table (70) shows elite beats emphasized (9 prints elite,
13 prints condensed elite), emphasized beats condensed (12 prints
emphasized), and condensed and elite combine (5 is 20 cpi).

Mixing in a line (104) is described as eight combination types:

| Type | Basic | Allowed with it |
|---|---|---|
| A | pica | condensed, double-strike, enlarged, underline |
| B | pica | condensed, script, enlarged, underline |
| C | emphasized | double-strike, enlarged, underline |
| D | emphasized | script, enlarged, underline |
| E | proportional | double-strike, enlarged, underline |
| F | elite | condensed, double-strike, enlarged, underline |
| G | elite | condensed, script, enlarged, underline |
| H | NLQ | proportional, script, enlarged, underline |

Priority among basic modes: NLQ > elite > proportional > emphasized >
pica (FX-80: elite > proportional > emphasized > compressed > pica).
Condensed is subsidiary here, combining with pica and elite but masked
by emphasized and proportional. Proportional masks script. Masked modes
keep their flags and return when the winner is cancelled.

### Character sets (76-83, 108-119)

The ROM's 32 international characters, shown by `ESC 6` at 128-159 and
by `ESC I 1` at 0-31, are in the same order as the FX-80's locations
0-31 (`charsets.py`): a grave, e grave, u grave, o grave, i grave,
degree, pound, inverted !, inverted ?, N tilde, n tilde, currency sign,
Pt, A ring, a ring, c cedilla, section, sharp s, AE, ae, O slash,
o slash, diaeresis, A/O/U umlaut, a/o/u umlaut, E acute, e acute, yen.
`ESC 6` prints them only in italic. Code 255 under `ESC 6` prints a glyph
the scan does not resolve (78).

`ESC R n` (0-11), read from the sample printout (77) and the chapter 5
tables. Codes 160-254 give the same substitutions in italic. Sets 0-8
match the FX-80 exactly; 9-11 are new. Characters are given as FX-80 ROM
locations, then names.

| n | Set | 35 | 36 | 64 | 91 | 92 | 93 | 94 | 96 | 123 | 124 | 125 | 126 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 9 | Norway | | 11 | 29 | 18 | 20 | 13 | 25 | 30 | 19 | 21 | 14 | 28 |
| 10 | Denmark II | | | 29 | 18 | 20 | 13 | 25 | 30 | 19 | 21 | 14 | 28 |
| 11 | England II | | | | | | | | 6 | | | | |

That is: Norway replaces $ with the currency sign, @ with E acute,
[ \ ] ^ with AE, O slash, A ring, U umlaut, ` with e acute, and { | } ~
with ae, o slash, a ring, u umlaut (eleven characters). Denmark II is
the same but keeps $ (ten characters). England II keeps # and puts the
pound sign at 96 (`) instead (one character), where England I (n = 3)
puts it at 35. The spec's counts (127) agree: eleven Norwegian, ten
Danish II, one UK II.

`ESC I 1` (82) makes codes 0-7, 16, 17, 21-26 and 28-31 (and 128-135,
144, 145, 149-154, 156-159) print the international characters at those
locations. Codes 8-15, 18-20 and 27 and their high twins always stay
controls, so locations 8-15 and 18-20 cannot be reached this way. The
FX-80 keeps 7-15, 17-20, 24 and 27 as controls; on the M-1109 code 7,
17 (DC1) and 24 (CAN) become printable. Codes 0-31 that are not
controls print nothing while `ESC I 0` is in force (tables, 108).

`ESC =` and `ESC >` force bit 7 of following bytes to 0 or 1, but not of
bit-image data; the manual adds that this applies to `ESC D`, `ESC B`,
`ESC b` and `ESC 3` parameters (94). `ESC #` stops it.

### User-defined characters (90-93)

- `ESC & 0 n m` then, for each code n to m (0-255), an attribute byte and
  11 column bytes, bit 7 the top pin, as on the FX-80. Attribute bit 7
  set: the top eight pins; clear: the bottom eight (descender). Bits 4-6
  are the first and bits 0-3 the last column printed in proportional
  mode.
- Columns alternate full-dot and half-dot positions; the manual does not
  state the FX-80 rule that two horizontally adjacent dots are never
  printed, but the F/H labelling implies it.
- `ESC % 1 0` selects the downloaded set, `ESC % 0 0` the ROM. With
  nothing downloaded, `ESC % 1` falls back to the ROM. `ESC : 0 0 0`
  copies the ROM into the download buffer.
- The download buffer is separate memory and needs no switch.

### Bit image (96-103)

- `ESC K/L/Y/Z n1 n2 d...`: n1 + 256 n2 columns; only the low three bits
  of n2 are used. One byte per column, bit 7 the top pin; pin 9 is never
  used. Prints the buffer first, then switches to bit image; text modes
  are kept and resume after.
- At most 480 columns (K), 960 (L, Y) or 1920 (Z) per line, counting text
  on the same line at the widths above (doubled for L and Y, quadrupled
  for Z). Data past the limit has unpredictable results.
- Bit images print unidirectionally, left to right.
- `ESC *` modes:

  | m | Mode | Per 8 inches | Per inch | Speed | Same as |
  |---|---|---|---|---|---|
  | 0 | Standard | 480 | 60 | normal | `ESC K` |
  | 1 | Double | 960 | 120 | reduced | `ESC L` |
  | 2 | Double-speed double | 960 | 120 | normal | `ESC Y` |
  | 3 | Quadruple | 1920 | 240 | reduced | `ESC Z` |
  | 4 | CRT I | 640 | 80 | reduced | |
  | 5 | Plotter | 576 | 72 | reduced | |
  | 6 | CRT II | 720 | 90 | reduced | |
  | 7 | Double plotter | 1152 | 144 | reduced | |

  In modes 2, 3 and 7 adjacent dots in a row are not printed. Modes 0-6
  match the FX-80's 0-6 in density and adjacent-dot rule; mode 7 is new.
- The `ESC Y` page itself (100) is missing from the scan.

### Other

- `ESC s 1` cuts the head drive pulse to about 85%, for quieter but
  possibly fainter printing; `ESC s 0` restores it (89). Nothing to model
  beyond, perhaps, lighter dots.
- `ESC 8` keeps printing past paper-out (the CHECK lamp and PE line still
  signal); `ESC 9` restores sensing and is the power-on state (86-87).
- `ESC U 1` unidirectional, `ESC U 0` bidirectional (default).

## Mode II (26, 105, 120-121)

An IBM Graphics Printer-style personality. Its command set (26) is NUL,
HT, LF, VT, FF, CR, SO, SI, DC2, DC4, CAN, `ESC -`, `ESC 0`, `ESC 1`,
`ESC 2`, `ESC 3`, `ESC 6`, `ESC 7`, `ESC 8`, `ESC 9`, `ESC <`, `ESC A`,
`ESC C`, `ESC D`, `ESC E`, `ESC F`, `ESC G`, `ESC H`, `ESC J`, `ESC K`,
`ESC L`, `ESC N`, `ESC O`, `ESC S`, `ESC T`, `ESC U`, `ESC W`, `ESC Y`,
`ESC Z`, `ESC x`. There is no BS, DEL, `ESC @`, `ESC B`, `ESC b`,
`ESC /`, margins, elite, proportional, italic, `ESC R`, `ESC I`,
`ESC !`, `ESC *`, download or MSB control. The high-bit control twins
work only with character set 1. Differences from Mode I:

- `ESC A n` (1-85) only stores a spacing; `ESC 2` brings it into force
  (1/6 inch if no `ESC A` was sent). `ESC 3` takes 1-255.
- If a line holds the box-drawing characters 176-223 or 244 (not in
  script), any spacing below 1/6 inch is raised to 1/6 for that line.
- CR always cancels SO enlarged. VT is LF. `ESC J` returns the carriage.
- `ESC D`: up to 28 stops, kept as character counts, so they move with
  the pitch (except enlarged).
- Condensed is 17 cpi, 132 per line.
- Underline covers only characters and the spaces or tab gaps between
  them, never leading or trailing spaces; box-drawing characters are not
  underlined.
- CAN is obeyed or ignored by switch 2-4.
- `ESC 6` selects character set 2 and `ESC 7` set 1.
- Mixing: five types; emphasized > pica, NLQ above all; condensed,
  script, double-strike, enlarged and underline subsidiary (105).
- Graphic characters are 8 x 6 dots, 2.8 mm high; "special graphic"
  characters are 4.2 mm high (128), which is 1/6 inch, presumably so
  box-drawing joins between lines at 1/6 inch spacing.

Character set 1 (120): 32-126 ASCII; 128-159 controls (mirroring 0-31);
160-254 the upper half of the IBM PC character set (accented letters
from a acute, block and box-drawing, Greek and mathematical); 255 a
space. Character set 2 (121) is the same but 128-159 print the IBM
accented letters (C cedilla to f hook), and 3-6 print the card suits and
21 the section sign. Codes 127, 7 and 8 print nothing in either set.

## Panel functions (18-21)

- Power on holding LF: self test, printing all ROM characters in each
  style, with a header showing the firmware revision and switch bank 1.
  Runs until power off.
- Power on holding LF and ON LINE: hex dump. Received bytes print as hex
  only, 27 per line, in pica or NLQ, when the buffer fills or ON LINE is
  pressed. Power off to leave.
- LF offline feeds a line (held 0.5 s, continuously); LF online toggles
  NLQ.

## Open questions

- Page 100 (`ESC Y`) is missing; its behaviour is inferred from the
  summary and `ESC *` mode 2.
- "9 x 9 dot matrix (half dot 4)" (127): the meaning of the half-dot
  count is unclear, as is how it relates to the 11-column download grid.
- NLQ is described as 18 x 20 dots in a 3.1 x 2.0 mm frame; the
  horizontal resolution this implies does not fit 1/120 inch half dots.
  Papyrium reads it as the nine pins in two passes 1/216 inch apart (18
  rows) on a 1/240 inch grid (20 dots in 2.0 mm is close to 1/240 inch);
  the sample on page 74 fits that grid within 24 columns of the pica cell.
- The mixing notes (104, 105) list "Double-Strike > Script", but `ESC !`
  (68), `ESC G` (60) and `ESC S` (71) all say script beats double-strike.
- Condensed pica: 136 per line (127) or 137 (55, 52)?
- Power-on margins are not stated; presumably 0 and 80 pica.
- Whether `ESC Q`, like `ESC l`, resets the tab stops (not stated).
- Several mode commands say they act "after printing the data in the
  print buffer" (`ESC E`, `ESC F`, `ESC H`, `ESC T`, `ESC x`, DC2); the
  examples show modes changing within a line, so this probably has no
  visible effect. In Elite, `ESC F` neither acts nor prints.
- Whether `ESC @` erases downloaded characters, and how many characters
  the download buffer holds (codes 0-255 are accepted).
- How `ESC =` and `ESC >` affect the `ESC D/B/b/3` parameters.
- In enlarged, BS moves a double pica column even in elite or condensed?
- Code 255 under `ESC 6` (78) is illegible.
- The roll-paper diagram (140) is the only figure for the print
  position; where the first line sits on a cut sheet is not given.
- Printed pages 106-107, 122-123 and 125 are not in the scan; their
  contents (probably dividers and the end of troubleshooting) are
  unknown.
