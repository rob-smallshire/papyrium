# Epson LX-800 behaviour notes

Facts about the Epson LX-800 that a future `lx800` printer model, through
Papyrium's `escp` language, would rely on, and against which the Star
LC-10's Standard mode (`docs/star-lc-10.md`) can be checked. They are
restated in our own words from Epson's *LX-800 User's Manual* (1987) and
*LX-800 Technical Manual* (1987, a service manual). Page numbers are the
**printed** ones (chapter-page, such as A-14 or 1-21), not the scan's PDF
page index. Unprefixed page numbers refer to the User's Manual; "TM"
marks the Technical Manual. The manuals are copyrighted and are kept,
uncommitted, in `docs/local/epson-lx800/`.

The LX-800 is a nine-pin, 80-column printer, described as upwardly
compatible with the LX-86 (TM 1-1) and, in the software selection list,
as best driven as an FX-86e, EX-800, LX-86, LX-80, FX-85 or FX-80, in
that order of preference (2-1). It is an FX-80 descendant with two NLQ
typefaces (Roman and Sans Serif), an IBM-style character table, more
international sets, panel type selection (SelecType) and paper handling
for single sheets, and without several FX-80 commands. The User's Manual
has the command reference (Appendix A) and the switch tables (Appendix
D); the TM has specifications, switches and jumper, and firmware and
mechanism detail but no command reference.

## DIP switches and jumper (D-2 to D-4; TM 1-12, 1-13)

Two banks on the back panel, eight and four switches, read only at power
on and (TM 1-12) on an INIT pulse. 1-1 is at the far left.

| Switch | Factory | Meaning |
|---|---|---|
| 1-1 | off | Power on in normal pitch (on: condensed) |
| 1-2 | off | Plain zero (on: slashed zero) |
| 1-3 | off | Codes 128-255 from the italic table (on: Epson Character Graphics) |
| 1-4 | off | Paper-out detection active (on: inactive); the TM states the opposite sense, see Open questions |
| 1-5 | off | Power on in draft (on: NLQ) |
| 1-6..1-8 | on, on, on | International set: USA (table below) |
| 2-1 | off | Page length 11 inches (on: 12 inches) |
| 2-2 | off | Cut sheet feeder mode off (on: on) |
| 2-3 | off | No skip-over-perforation (on: skip 1 inch) |
| 2-4 | off | CR only (on: every CR also feeds a line; the TM describes it as holding AUTO FEED XT low) |

The User's Manual gives all switches off except 1-6 to 1-8 (D-3). The TM
gives factory settings by market (TM 1-13): USA, South-East Asia and the
Middle East as above; Germany and Northern Europe with the German set and
**12-inch** pages (1-7 off, 2-1 on); the UK and Australia with the UK set;
France, Italy and Spain with the USA set but **graphics table** (1-3 on).

Switches 1-6, 1-7, 1-8 choose the power-on set, off counting as 1 and
1-6 as the high bit: 0 USA, 1 France, 2 Germany, 3 UK, 4 Denmark,
5 Sweden, 6 Italy, 7 Spain (D-4; TM 1-13). This is the `ESC R` order.
Japan, Norway, Denmark II, Spain II and Latin America only by `ESC R`.

Jumper J1 on the main (ROCX) board (TM 1-13; F-4): open (the factory
setting per the TM) leaves SLCT IN, pin 36, to the interface; closed
holds it low. When SLCT IN is low at initialization, DC1 and DC3 are
ignored (TM 1-5). There is no switch for power-on emphasized, the beeper,
or the use of RAM (download memory is separate; see below).

## Control panel (1-20 to 1-22, 3-1 to 3-4, C-4; TM 1-14 to 1-17)

Three touch buttons (ON/OFF LINE, NLQ/FORM FEED, DRAFT/LINE FEED with
AUTO LOAD) and four lamps.

- **On line**, NLQ/FORM FEED selects NLQ, alternating between Roman (two
  beeps) and Sans Serif (three beeps) on each press; DRAFT/LINE FEED
  selects draft (one beep) (1-21; TM 1-14, 1-17). These change printer
  state exactly as `ESC x` and `ESC k` would.
- **Off line**, FORM FEED feeds to the next top of form or ejects a
  sheet; LINE FEED feeds one line, repeating while held; with a sheet in
  the guide and paper out, LINE FEED auto-loads it (1-18, 1-21).
- **SelecType** (3-1 to 3-4; TM 1-16): on line, hold ON/OFF LINE and
  press FORM FEED (one beep, ON LINE lamp blinks). Press ON/OFF LINE n
  times for mode n: 1 emphasized, 2 double-strike, 3 condensed, 4 elite;
  FORM FEED sets it; LINE FEED leaves SelecType, off line. Further modes
  are added by repeating, counting on from the last count, lowest first.
  In draft any combination is allowed except emphasized with condensed;
  in NLQ only emphasized and elite are offered. The setting lasts until
  power off or until a command overrides it, and `ESC @` returns to it
  (D-1).
- **Self test** (1-21, 1-22; TM 1-15): power on holding DRAFT for a
  draft test, NLQ for an NLQ test alternating Roman and Sans Serif lines;
  a sliding pattern of the ROM characters, the ROM's code number on the
  first line, until power off. With 1-5 on only the NLQ test runs.
- **Data dump** (C-4, C-5; TM 1-15): power on holding FORM FEED and LINE
  FEED. Prints "Data Dump Mode", then each 16 bytes received as a line:
  a four-digit line number, 16 hex values, and 16 guide characters (the
  character if printable, else a dot). Going off line prints the last
  partial line.

Beeper (TM 1-17): BEL one 0.1 s beep; paper out eight 0.5 s beeps;
carriage or voltage fault five 0.5 s beeps.

## Power-on state and initialization (D-1; TM 1-17)

The printer is initialized by power on, by INIT (pin 31) low, and by
`ESC @`. All three: head to home, on line, the current line cleared,
margins and vertical tabs cleared, line spacing 1/6 inch, horizontal
tabs every eight columns, vertical tab channel 0, page length and skip-
over-perforation from 2-1 and 2-3, top of form at the current line, ROM
characters selected, character table and international set from 1-3 and
1-6 to 1-8. Power on and INIT also empty the input buffer and set the
type style from the switches (condensed 1-1, slashed zero 1-2, NLQ 1-5);
`ESC @` instead restores the current SelecType settings, and uses the
switch settings read at power on, not their present positions.

So at power on: pica (or condensed), draft (or NLQ Roman, 4-1), upright,
no vertical tabs (VT acts as LF, A-15), justification left (A-26), codes
128-159 as controls (A-28), bidirectional (A-8), paper-out sensing on.
The margins after reset are not stated beyond "cleared": presumably 0
and the full 80 pica columns.

Unlike the FX-80, `ESC @` is not said to erase user-defined characters,
only to select the ROM set.

## Paper, printable area and top of form (1-7 to 1-19, F-1; TM 1-7 to 1-10, 2-30)

- Continuous paper 4 to 10 inches wide, including the hole strips, on a
  pull tractor fitted above the platen; single sheets 7.15 to 8.5 inches
  (182-216 mm), at most 12 inches long, friction fed; roll paper 8.5
  inches on an optional holder (F-1; TM 1-8). Up to three parts, 0.01
  inch in all.
- The line is 8 inches. On fanfold the first and last print positions
  are 0.75 inch in from the paper edges when the paper is narrower than
  9.5 inches (1.02 and 0.94 inch when wider), so 9.5-inch paper carries
  the 8-inch line centred, as Papyrium already assumes for the FX-80. At
  least 0.35 inch above and below each perforation is unprintable (TM
  1-10).
- Single sheets: at least 0.12 inch (3 mm) either side, about 0.87 inch
  (22 mm) at the top and about 1.2 inches at the bottom (TM 1-9). Auto
  loading parks the head at column 40 and feeds 433 steps of 1/216 inch,
  leaving the first line about 22 mm below the top edge (TM 2-30). The
  left edge guide is set to a mark on the paper guide (1-17).
- Roll paper: first line about 0.98 inch (25 mm) below the tear (TM 1-9).
- Top of form on continuous paper is where the paper stands at power on:
  the user winds a perforation to just below the top of the ribbon
  (1-14). `ESC C` and `ESC @` also make the current line the top of form.
- Paper out stops printing about 3/4 inch before the end of the sheet
  and beeps (A-9). The sensor sits behind the platen (C-4).
- The paper feed motor steps 1/216 inch (36 steps per 1/6 inch line,
  TM 2-29); a 1/6 inch line feed takes about 95 ms (TM 1-7).
- The first column is 25 carriage steps right of the home position
  (TM 2-26).

## Character formation (5-2, 5-8 to 5-10, 4-1 to 4-3, F-1; TM 1-6, 1-7, 2-21, 2-32, 2-35)

- Nine-pin head, dot pitch 1/72 inch (0.35 mm), pin diameter 0.29 mm.
  The ninth pin is "usually for underlining" (TM 2-32): the firmware's
  example (TM 2-34) drives pin 9 under every column of an underlined
  character, so the underline is printed by pin 9 in the same pass, not
  one row lower as on the FX-80.
- Draft characters: a 9 x 9 matrix (TM 1-6) in an 11-column cell at
  1/120 inch, the last two columns blank as character space; dots never
  overlap horizontally, and either the top or the bottom row is empty
  (5-2), as on the FX-80. All characters are 3.1 mm high; pica cells
  2.1 mm, condensed 1.05 mm (F-1).
- NLQ characters: "11 x 18" (TM 1-6), printed in two passes, the paper
  fed **1/216 inch** between them (TM 2-35), at half carriage speed
  (450 steps a second instead of 900, TM 2-25). The user-defined NLQ
  grid (5-8, 5-10) is 12 columns by 18 rows, with dots drawn as circles
  that overlap their neighbours both ways; see Open questions for its
  geometry.
- Two NLQ typefaces, Roman and Sans Serif (Introduction 1, 4-1). NLQ is
  pica only in the speed table (TM 1-7), but the TM says superscript,
  subscript, italic and elite work in NLQ (TM 1-1); condensed does not
  (NLQ masks it, C-2), nor double-strike (ignored, not cancelled, A-24).
  Emphasized does print in NLQ (sample, 4-3; SelecType, 3-2).
- Pitches (TM 1-7; 2-5): pica 10 cpi (80 a line), elite 12 (96),
  condensed pica 17 (132), condensed elite 20 (160), each halved by
  double width (40, 48, 66; 5, 6, 8.5 cpi). There is no proportional
  spacing.
- Emphasized prints each dot again slightly to the right; double-strike
  prints the line again slightly lower (4-3, A-23, A-24).
- Superscript and subscript: "about two-thirds" of normal height, in the
  upper or lower part of the cell (A-24, A-25); the TM gives 1.6 mm
  against 3.1 mm (TM 1-7).
- Italic comes from a separate italic table in ROM (A-27), for all
  printable ASCII and the international characters (B-8).
- Speeds: draft 150 cps pica, 180 elite, 128 condensed pica, 150
  condensed elite; emphasized or double width halve them; NLQ 25 cps
  (TM 1-7). `ESC s 1` halves the carriage speed and doubles the pin
  pulse (TM 2-35).
- Text prints bidirectionally with logic seeking; bit images always left
  to right (TM 1-6).

### Mode interactions

The manual has no priority table like the FX-80's. What it states:

- Emphasized overrides condensed (A-20, C-2).
- NLQ overrides condensed (C-2) and ignores double-strike (A-24).
- Pica and elite exclude each other (A-20).
- In SelecType, draft modes combine freely except emphasized with
  condensed (3-2); so emphasized elite may print, unlike the FX-80 where
  elite masks emphasized (TM 1-7 lists no emphasized elite speed).
- Epson Character Graphics characters cannot be italicized (A-27).
- Underline is continuous, through spaces, superscripts and subscripts
  (4-3, A-25).

## Commands

"vs FX-80" compares with `docs/epson-fx80.md`: blank means the same as
far as the manuals say. For `ESC s`, `ESC U`, `ESC x`, `ESC W`, `ESC S`,
`ESC -` and `ESC %` the parameter may be the code 0/1 or the digit "0"/"1"
(A-2). Codes 128-159 that mirror a control act as that control unless
`ESC 6` is in force (B-4).

### Control codes

| Bytes | Effect | Page | vs FX-80 |
|---|---|---|---|
| NUL (0) | Ends `ESC B`, `ESC b`, `ESC D` lists | A-15 | |
| BEL (7) | Beep | A-10 | |
| BS (8) | Print the buffer, then move back one column; not past the left margin; ignored under `ESC a` 1-3; position uncertain straight after graphics | A-17 | |
| HT (9) | Next horizontal tab | A-18 | |
| LF (10) | Print and feed one line at the current spacing | A-13 | |
| VT (11) | Next vertical tab in the selected channel; LF if none are set | A-15 | no default stops |
| FF (12) | Print and feed to the next top of form | A-11 | |
| CR (13) | Print and return to the left margin; also feed if 2-4 is on or AUTO FEED XT is low | A-10 | |
| SO (14), `ESC SO` | Double width until CR or DC4 | A-22 | ended by CR |
| SI (15), `ESC SI` | Condensed (pica 17 cpi, elite 20 cpi) | A-21 | condensed elite |
| DC1 (17) | Select after DC3 (not after the panel button) | A-7 | |
| DC2 (18) | Cancel condensed, however it was set (SI, SelecType or 1-1) | A-21 | |
| DC3 (19) | Deselect: data are acknowledged but ignored until DC1; only if SLCT IN is high | A-7; F-5 | |
| DC4 (20) | Cancel SO double width, not `ESC W` or `ESC !` double width | A-22 | |
| CAN (24) | Delete the text on the current line; controls are kept | A-10 | |
| DEL (127) | Delete the last text character on the line | A-11 | |

### Printer operation

| Bytes | Effect | Page | vs FX-80 |
|---|---|---|---|
| `ESC @` | Initialize (see above); text before it on the line is discarded | A-7; D-1 | restores SelecType; UDCs not said to be erased |
| `ESC s n` | Half speed on (1) / off (0) | A-8 | |
| `ESC <` | Unidirectional for one line: head home, print left to right; ends at CR | A-8 | |
| `ESC U n` | Unidirectional on (1) / off (0) | A-8 | |
| `ESC 8` | Ignore paper out | A-9 | |
| `ESC 9` | Sense paper out (default) | A-9 | |
| `ESC EM n` | Cut sheet feeder mode on ("4") / off ("0"); only the characters 48 and 52; overrides 2-2; ignored for other n | A-9 | |

### Vertical motion and forms

| Bytes | Effect | Page | vs FX-80 |
|---|---|---|---|
| `ESC 0` | 1/8 inch spacing | A-13 | |
| `ESC 1` | 7/72 inch spacing | A-13 | |
| `ESC 2` | 1/6 inch spacing (default) | A-14 | |
| `ESC 3 n` | n/216 inch spacing, 0-255 | A-14 | |
| `ESC A n` | n/72 inch spacing, 0-85 | A-14 | |
| `ESC J n` | Feed n/216 inch now, 0-255; no CR, spacing unchanged | A-15 | |
| `ESC C n` | Page length n lines, 1-127; top of form here | A-11 | |
| `ESC C 0 n` | Page length n inches, 1-22; top of form here | A-12 | |
| `ESC N n` | Skip n lines at the page end, 1-127; same as 2-3 | A-12 | |
| `ESC O` | Cancel skip-over-perforation, overriding 2-3 | A-12 | |
| `ESC B n1 ... 0` | Up to 16 vertical tabs, 1-255 ascending, in lines of the current spacing, fixed thereafter; channel 0; `ESC B 0` clears | A-15 | |
| `ESC b c n1 ... 0` | As `ESC B` for channel c, 0-7; `ESC b c 0` clears | A-16 | |
| `ESC / c` | Select vertical tab channel c, 0-7 | A-16 | |
| `ESC e 1 s` | Vertical tabs every s lines | A-17 | new |
| `ESC f 1 s` | Feed s lines, without CR | A-18 | new |

`ESC N` is cancelled by `ESC O` and by either `ESC C` (A-12).

### Horizontal motion

| Bytes | Effect | Page | vs FX-80 |
|---|---|---|---|
| `ESC l n` | Left margin at column n of the current pitch; clears the tab stops and the text on the line | A-16 | ranges not given |
| `ESC Q n` | Right margin at column n of the current pitch; clears the tab stops and the text on the line | A-17 | ranges not given |
| `ESC D n1 ... 0` | Up to 32 horizontal tabs, 1-137, in columns of the current pitch, fixed thereafter; ends at NUL or a value lower than the one before; `ESC D 0` clears | A-18 | |
| `ESC e 0 s` | Horizontal tabs every s columns; at most 21 pica, 25 elite, 36 condensed | A-17 | new |
| `ESC f 0 s` | Print s spaces (at most 127), without CR | A-18 | new |

The margins must be at least one double-width pica character (1/5 inch)
apart (A-16, A-17). Set margins before tabs (C-2).

### Type style and size

| Bytes | Effect | Page | vs FX-80 |
|---|---|---|---|
| `ESC x n` | Draft (0) / NLQ (1) | A-19 | FX-80 lacks |
| `ESC k n` | NLQ typeface: Roman (0), Sans Serif (1); no effect on draft | A-19 | FX-80 lacks |
| `ESC ! n` | Master select: 1 elite, 4 condensed, 8 emphasized, 16 double-strike, 32 double width, 64 italic, 128 underline; emphasized beats condensed | A-20 | bits 6 and 7 new |
| `ESC P` | Pica | A-20 | |
| `ESC M` | Elite | A-21 | |
| `ESC W n` | Double width on (1) / off (0) | A-23 | |
| `ESC E` / `ESC F` | Emphasized on / off | A-23 | |
| `ESC G` / `ESC H` | Double-strike on / off; ignored, not cancelled, in NLQ | A-24 | |
| `ESC S 0` / `ESC S 1` | Superscript / subscript | A-24, A-25 | |
| `ESC T` | Cancel super/subscript | A-25 | |
| `ESC - n` | Underline on (1) / off (0), continuous through spaces | A-25 | |
| `ESC 4` / `ESC 5` | Italic on / off (not for graphics characters) | A-27 | |
| `ESC a n` | NLQ justification: 0 left (default), 1 centre, 2 right, 3 full | A-26 | FX-80 lacks |

Full justification (n = 3) is done when the buffer fills or at CR, VT,
LF or FF, so a paragraph must contain no CRs; HT and BS are invalid
except under n = 0; justification works only in NLQ (A-26).

### Character sets

| Bytes | Effect | Page | vs FX-80 |
|---|---|---|---|
| `ESC t n` | Codes 128-255 from the italic table (0) or Epson Character Graphics (1); only the bytes 0 and 1, not digits; same as 1-3 | A-26 | FX-80 lacks |
| `ESC R n` | International set 0-12 | A-28 | 9-12 new |
| `ESC 6` | Print codes 128-159 as characters | A-28 | different in graphics table |
| `ESC 7` | Codes 128-159 are controls (default) | A-28 | |

### User-defined characters

| Bytes | Effect | Page | vs FX-80 |
|---|---|---|---|
| `ESC & 0 c1 c2 ...` | Define codes c1 to c2 in the current quality (draft or NLQ); c1 and c2 must be 58-63 | A-29; 5-3 to 5-12 | 6 codes only; NLQ form new |
| `ESC : 0 0 0` | Copy the ROM characters into RAM | A-29 | |
| `ESC % n` | Normal (0) / user-defined (1) set; `ESC &` must come first | A-29 | one parameter byte? |

### Graphics

| Bytes | Effect | Page | vs FX-80 |
|---|---|---|---|
| `ESC K n1 n2 d...` | 60 dpi, 8 pins | A-30 | |
| `ESC L n1 n2 d...` | 120 dpi | A-30 | |
| `ESC Y n1 n2 d...` | 120 dpi, high speed, no adjacent dots | A-30 | |
| `ESC Z n1 n2 d...` | 240 dpi, no adjacent dots | A-31 | |
| `ESC * m n1 n2 d...` | Mode m, 0-6 | A-31 | |
| `ESC ? s m` | Make `ESC` s (K, L, Y or Z) use mode m, 0-6 | A-31 | |
| `ESC ^ m n1 n2 d...` | Nine-pin graphics, 60 (m 0) or 120 (m 1) dpi, two bytes a column | A-32 | |

That is 73 commands, as in the manual's numerical list (A-4 to A-6),
counting `ESC C 0`, `ESC S 0` and `ESC S 1` separately and each of
`ESC SO`, `ESC SI` apart from SO and SI.

**FX-80 commands the LX-800 does not have**: `ESC I` (printable codes
0-31; on the LX-800 codes 0-31 that are not controls print nothing,
B-2), `ESC i` (immediate mode), `ESC j` (reverse feed), `ESC p`
(proportional), and `ESC =`, `ESC >`, `ESC #` (bit 7 control; 7-bit
hosts are advised only to keep graphics data below 128, C-3). The
FX-80's default vertical tabs and its RAM switch are also gone. Unknown
escape sequences are not discussed.

## Command details

### Line ends and buffer (A-10, A-11, A-15; TM 2-20, 2-21)

- Text is edited into a one-line buffer, three bytes a character (code
  and two bytes of attribute flags), printed at CR or when it fills
  (TM 2-21). The input buffer is 3K (TM 1-1, 2-18; the User's Manual
  says 8K, E-1).
- `ESC J` feeds at once without CR; `ESC f 1 s` feeds s lines without
  CR.
- CR feeds a line as well when 2-4 is on or AUTO FEED XT is held low at
  initialization (A-10; TM 1-4).
- SO double width is cancelled by CR (A-22); the manual names no other
  line end.

### Tabs and margins (A-16 to A-18, C-2)

- Horizontal tabs: defaults every eight columns of the default pitch;
  stops are fixed positions that do not move with pitch changes. Margin
  commands clear them, so tabs must be set after margins.
- `ESC e 0 s` sets stops every s columns of the current pitch; the
  limits 21 (pica), 25 (elite) and 36 (condensed) are as printed.
- Vertical tabs: stops in lines of the current spacing, fixed as
  distances; eight channels; none set at power on.

### User-defined characters (5-1 to 5-12, A-29; TM 2-18, 2-21)

- The download area is the CPU's 256 bytes of internal RAM (TM 2-18),
  separate from the buffers, so no switch is needed and the input buffer
  keeps its size. At most six characters, codes 58-63 (":" to "?"), can
  be defined (5-7, 5-11, A-29).
- Definitions go into the quality currently selected: send `ESC x 1`
  first for NLQ characters (5-11).
- Draft form: per character an attribute byte, then 11 column bytes, bit
  7 the top dot. The examples send attribute 128 to use the top eight
  pins and 0 to use the bottom eight (5-5), as on the FX-80; with no
  proportional mode the low attribute bits have no stated use. The last
  two columns are sent as zero, leaving nine designable columns (5-2,
  5-6). Overlapping dots print only once (5-3).
- NLQ form: per character three attribute bytes, then 36 data bytes:
  three bytes for each of 12 columns, the first for rows 1-8 (128 the
  top), the second for rows 9-16 and the top two bits of the third for
  rows 17-18 (5-9). The examples send the attributes 0, 12, 0 (5-11),
  which read as left space, width in columns and right space. All 18
  rows and 12 columns may be used, overlapping dots included, leaving a
  column or two blank for spacing (5-8).
- The example programs send `ESC % 1 0` (5-3, 5-6, 5-11), but A-29 gives
  `ESC %` a single parameter byte.
- In the RAM set, codes not redefined after `ESC : 0 0 0` print the ROM
  characters; without the copy their contents are not stated.

### Bit images (6-2 to 6-12, A-30 to A-32, C-3)

| m | Mode | dpi | Adjacent dots | Same as |
|---|---|---|---|---|
| 0 | Single density | 60 | printed | `ESC K` |
| 1 | Double density | 120 | printed | `ESC L` |
| 2 | High-speed double density | 120 | not printed | `ESC Y` |
| 3 | Quadruple density | 240 | not printed | `ESC Z` |
| 4 | CRT I | 80 | printed | |
| 5 | Plotter (1:1) | 72 | printed | |
| 6 | CRT II | 90 | printed | |

These match the FX-80's modes 0-6. The column count is n1 + 256 n2; the
printer takes exactly that many data bytes whatever they are (6-6, C-3).
480 columns fill an 8-inch line at 60 dpi (TM 1-6). Bit images print
left to right only. `ESC ^` takes two bytes a column; the manual gives
no bit layout for the second byte (FX-80: bit 7 is pin 9). The TM says
adjacent half dots are never fired on one pin; the firmware drops one of
them (TM 2-32).

## Character sets (4-4, B-1 to B-8, A-26 to A-28; TM 1-6)

The ROM holds 96 ASCII, 96 italic, 32 international, 32 italic
international, 32 graphics (the 128-159 accented letters) and 96 IBM
graphics characters (TM 1-6). Codes 128-255 come from one of two tables,
chosen by switch 1-3 or `ESC t` (B-4 to B-7):

| Codes | Italic table, `ESC 7` | Italic table, `ESC 6` | Graphics table | Graphics table, `ESC 7` |
|---|---|---|---|---|
| 128-159 | controls (mirrors of NUL, BEL-SI, DC1-DC4, CAN, EM, ESC); others print nothing | the 32 international characters in italic | accented letters and currency signs of the IBM PC set | controls as in the first column |
| 160-254 | italic versions of 32-126 | as before | IBM PC block and box drawing (176-223), Greek and mathematical signs (224-254), and accented letters and signs (160-175) | as before |
| 255 | DEL | an italic slashed O or zero | blank | blank |

The graphics table is the upper half of the IBM PC character set, which
Epson calls Epson Character Graphics (4-4). The italic international
characters under `ESC 6` are in the same order as the FX-80's ROM
locations 0-31 (`charsets.py`). Codes 0-31 that are not controls print
nothing (B-2). The column heads suggest that in the graphics table
128-159 print unless `ESC 7` is sent, though A-28 calls `ESC 7` the
default; see Open questions.

International sets (B-8, A-28), substituting at 35, 36, 64, 91-94, 96 and
123-126; italic forms are available through `ESC 4` (B-8):

| n | Set | vs FX-80 |
|---|---|---|
| 0-8 | USA, France, Germany, UK, Denmark I, Sweden, Italy, Spain I, Japan | the same as the FX-80's 0-8 |
| 9 | Norway | new; as the M-1109's 9: $ to currency sign, @ to E acute, [ \ ] ^ to AE, O slash, A ring, U umlaut, ` to e acute, { \| } ~ to ae, o slash, a ring, u umlaut |
| 10 | Denmark II | new; Norway keeping $ (the M-1109's 10) |
| 11 | Spain II | new: @ a acute, [ inverted !, \ N tilde, ] inverted ?, ^ e acute, { i acute, \| n tilde, } o acute, ~ u acute |
| 12 | Latin America | new: Spain II with ` as u umlaut |

Spain II and Latin America need a acute, i acute, o acute and u acute,
which are not among the FX-80's 32 international ROM characters.

## Interface (F-3 to F-6; TM 1-3 to 1-5, 2-17, 2-22)

Centronics parallel, 8-bit; optional serial (#8143, #8148) and IEEE-488
boards (E-1). ACKNLG about 12 microseconds (5 in the F-5 timing figure). BUSY is
high while receiving, printing, off line or in error. INIT low for at least 50 microseconds
resets to the power-on state and clears the buffer. AUTO FEED XT low
adds a line feed to each CR (fixed low by 2-4). SLCT IN decides whether
DC1/DC3 are obeyed (see J1). ERROR goes low on paper end, off line or a
fault; PE high on paper out.

## Compared with the FX-80

- **Quality**: NLQ in two typefaces (`ESC x`, `ESC k`, panel, switch 1-5),
  two passes 1/216 inch apart; NLQ masks condensed and double-strike,
  keeps emphasized, elite, italic and scripts.
- **Pitch**: condensed elite at 20 cpi (160 a line); no proportional
  spacing (`ESC p` gone; `ESC !` has no proportional bit either).
- **Master select** adds italic (64) and underline (128).
- **Character tables**: `ESC t` and switch 1-3 choose italics or the IBM
  PC upper half at 128-255; `ESC 6` in the graphics table governs the
  IBM accented letters, not italic internationals.
- **International sets**: 13 (0-12); 9 Norway, 10 Denmark II, 11 Spain
  II, 12 Latin America are new, and 11 differs from the M-1109's
  England II.
- **New commands**: `ESC x`, `ESC k`, `ESC a` (including full
  justification), `ESC t`, `ESC e`, `ESC f`.
- **Missing commands**: `ESC I`, `ESC i`, `ESC j`, `ESC p`, `ESC =`,
  `ESC >`, `ESC #`.
- **User-defined characters**: six codes, 58-63, in separate RAM (no
  switch, no lost buffer), with a separate NLQ form (3 attribute bytes,
  12 x 18 grid); not said to be erased by `ESC @`.
- **Switches**: different layout: condensed, slashed zero, character
  table, paper-out, NLQ, set, page length 11/12, cut sheet feeder,
  skip-over-perforation, auto line feed. No emphasized, beeper, RAM or
  always-selected switch (selection is J1 and SLCT IN instead).
- **Defaults**: no vertical tab stops at power on; page length 11 or 12
  inches by switch; `ESC @` returns to the SelecType style.
- **SO** ends at CR (the FX-80's at the end of the line).
- **Margins** clear the tab stops and the line; minimum gap 1/5 inch
  instead of a column count.
- **Underline** on pin 9 in the same pass (inferred from TM 2-34), not
  one row lower.
- **Paper**: single sheets with automatic loading, top line about 22 mm
  down; pull tractor; paper-out about 3/4 inch before the end.
- **Panel**: SelecType, NLQ/draft buttons, data dump, two self tests.

## The Star LC-10's Standard mode

Where `docs/star-lc-10.md` shows the LC-10 in Standard mode matching or
departing from the LX-800.

Matching:

- Draft 9 x 9 on 1/120 inch, condensed elite at 20 cpi and 160 columns,
  1/6 inch default spacing, 11 or 12-inch pages by switch, no default
  vertical tabs, bit image modes 0-6 with `ESC ?` and `ESC ^`, `ESC x`,
  `ESC 4/5`, `ESC 8/9`, `ESC U`, `ESC <`, `ESC e 0/1`, `ESC f 1`, DC1/DC3.
- `ESC t` chooses italics or the IBM set at 128-255 (LC-10 switch 1-7
  versus LX-800 1-3), and `ESC !` bits 6 and 7 are italic and underline.
- `ESC k` 0 and 1 select the first two NLQ typefaces (LC-10 Courier and
  Sanserif for LX-800 Roman and Sans Serif).
- `ESC R` 0-12 are the same thirteen sets with the same numbers; the
  international DIP switches give sets 0-7 in the same order.
- Emphasized cannot combine with condensed on either.

Departing:

- **Switches**: entirely different banks; the LC-10 has no switch for
  condensed, slashed zero, NLQ or skip-over-perforation, adds auto CR,
  IBM mode, Orator variant and a RAM/buffer switch, and its factory
  setting is all on (1-8 off for CR plus LF; LX-800 2-4 on).
- **NLQ**: four typefaces (Courier, Sanserif, two Orators) with italics;
  `ESC k` 2 and 3 are new. The LC-10 manual says the second pass is half
  a dot (1/144 inch) lower on a 1/240 inch grid of 23 columns; the
  LX-800 TM says 1/216 inch. Emphasized is draft-only on the LC-10 but
  prints in NLQ on the LX-800.
- **Download characters**: LC-10 codes 32-127 and 160-255, up to 192
  draft or 78 NLQ characters in main RAM (shrinking the buffer); NLQ
  form one attribute byte and 46 data bytes (23 columns by 16 rows).
  LX-800: six codes 58-63, NLQ three attribute bytes and 36 data bytes.
  NLQ downloads are therefore not interchangeable.
- **Codes 128-159**: in the LC-10's standard (italic) set there is no way
  to print the international characters there; the LX-800 does it with
  `ESC 6`. The LC-10's `ESC 6`/`ESC 7` choose IBM set #2/#1, which agrees
  with the LX-800's graphics-table columns.
- **International sets**: the LC-10 adds 13, Denmark/Norway.
- **`ESC a`**: the LC-10 lists 0-2 only; the LX-800 also has 3, full
  justification, and restricts justification to NLQ.
- **`ESC f 0 n`**: the LC-10 notes read it as an absolute move to column
  n; the LX-800 manual says it prints n spaces.
- **`ESC !`**: the LC-10 adds bit 1, proportional; the LX-800 has no
  proportional mode.
- **`ESC EM`**: the LC-10 has `0`, `4`, `R` and `T n` and their `((x))`
  forms; the LX-800 only `0` and `4`.
- **`ESC D`**: LC-10 stops 1-255, LX-800 1-137.
- **Margins**: LC-10 ranges are tabulated with a two-column minimum gap;
  the LX-800 gives a 1/5 inch minimum gap and no ranges. The LC-10's
  minimum right margins (pica 4) suggest a different rule.
- **SO** on the LC-10 ends at LF, VT, FF, DC4 or `ESC W 0`; on the LX-800
  at CR or DC4.
- **`ESC J`** takes 1-255 on the LC-10, 0-255 on the LX-800.
- **Commands the LC-10 adds over the LX-800**: `ESC p`, `ESC SP`, `ESC h`,
  `ESC w`, `ESC [ @`, `ESC _`, `ESC ~`, `ESC $`, `ESC \`, `ESC X`,
  `ESC c`, `ESC LF`, `ESC FF`, `ESC j`, `ESC i`, `ESC +`, `ESC =`, `ESC >`,
  `ESC #`, and the extra `ESC EM` forms; it also restores several FX-80
  commands the LX-800 dropped.
- **Commands the LX-800 has and the LC-10 does not document**: `ESC s`
  (half speed).
- **Panel**: the LC-10 has pitch and style buttons with power-on locks
  in place of SelecType.
- **Paper**: the LC-10 has a push tractor and paper parking; the LX-800 a
  pull tractor that must be removed for single sheets.

## For Papyrium

Configurable now through `EscpMechanism`:

- `sheet_length` 11 or 12 inches (2-1); `paper_width` 9.5 inches and
  `left_offset` 0.75 inch (TM 1-10); `columns` 80, `condensed_columns`
  132 (or 137 for the full 8 inches, as on the FX-80).
- `auto_line_feed` (2-4), `character_set` 0-7 (1-6 to 1-8),
  `skip_perforation_lines` 6 when 2-3 is on, `slashed_zero` (1-2),
  `condensed` (1-1), `emphasized` False, `near_letter_quality` (1-5),
  `nlq` True.
- `software_select` from J1 and SLCT IN; `user_defined_characters` True
  (download RAM is separate).
- `underline_row` 8 (pin 9), `default_vertical_tabs` False,
  `condensed_elite` True, `graphics_modes` 0-6, `high_codes_printable`
  for `ESC 6` in the italic table.
- `commands` without `I`, `i`, `j`, `p`, `=`, `>`, `#`.
- `top_offset` about 22 mm for automatically loaded single sheets.
- The draft font could start as the FX-80's `draft-9` until LX-800
  glyphs are reconstructed from the manual's samples.

New work:

1. **Two NLQ typefaces**, Roman and Sans Serif, with italics, and
   `ESC k` and the panel choice; `nlq_font` becomes a pair (or a
   mapping) of fonts. Reconstructed from the manual's printed samples as
   our own data.
2. **Character tables**: `ESC t` and switch 1-3, the Epson Character
   Graphics table (the IBM PC upper half, glyphs to be drawn), and
   `ESC 6`/`ESC 7` acting differently in each table.
3. **International sets 9-12** with per-model numbering: our
   `CharacterSet` has 11 as England II (M-1109), while the LX-800 and
   LC-10 use 11 for Spain II; also the new accented glyphs, upright and
   italic. `character_sets` needs a value of 13.
4. **Mode rules**: NLQ masks condensed and double-strike but keeps
   emphasized; `ESC !` bits 6 and 7; no proportional.
5. **New commands**: `ESC a` with full justification (which needs the
   whole paragraph line before placing it), `ESC e`, `ESC f`.
6. **User-defined characters** limited to 58-63 and the 3 + 36 byte NLQ
   form, with its own grid geometry.
7. A **SelecType** style option, which `ESC @` restores; an option for
   SO ending at CR; margins that clear tabs and the line.
8. `ESC EM` and `ESC s` as accepted no-ops (nothing visible on paper).

## Open questions

- **NLQ geometry.** The TM says the second NLQ pass is 1/216 inch lower
  (TM 2-35) and calls the matrix 11 x 18 (TM 1-6). The download grid is
  12 columns by 18 rows with overlapping circles, which on a pica cell
  suggests 1/120 inch columns and, at 18 rows over nine pins, 1/144 inch
  rows, not 1/216. Which is right, and how do the 18 rows map onto the
  two passes?
- **NLQ download attributes**: are 0, 12, 0 really left space, width and
  right space? What do other values do?
- **`ESC %`**: one parameter byte (A-29) or two (the examples)?
- **`ESC &`** outside 58-63: ignored, or are the bytes still consumed?
  What do RAM codes print without `ESC : 0 0 0`?
- **`ESC 6`/`ESC 7` in the graphics table**: the B-4 headings imply the
  accented letters print by default, A-28 that controls are the default.
- **Code 255 under `ESC 6`** prints a glyph like an italic O or zero with
  a slash; which?
- **Switch 1-4**: the User's Manual says on disables paper-out detection
  (D-3), the TM that on enables it (TM 1-12).
- **Input buffer**: 3K (TM 1-1, 2-18) or 8K (E-1)?
- **SLCT IN**: the TM says J1 is open at the factory, leaving SLCT IN to
  the cable; F-4 says the level is factory set low. So is DC3 obeyed on
  an ordinary cable?
- **Super/subscript height**: two-thirds (A-24) or 1.6 of 3.1 mm (TM
  1-7)? Are they double-struck as on the FX-80?
- **Elite with emphasized** in draft: SelecType allows it, the speed
  table omits it, and the FX-80 masks emphasized under elite.
- **Margins**: the ranges for `ESC l` and `ESC Q` and the power-on
  margins are not given.
- **`ESC e 0`** limits of 21, 25 and 36 columns look odd; are they right?
- **`ESC f 0 s`**: are the spaces printed (and underlined) or is it a
  plain move?
- **`ESC a`** in draft: ignored, or does it act? How do tabs, BS and
  mixed pitches behave on a justified line?
- **SO**: is it ended by LF, VT and FF as well as CR?
- **`ESC @`** and user-defined characters: kept or erased?
- **Codes 0-31** that are not controls: swallowed, or printed as spaces?
  Is EM (25) a control on its own or only after ESC?
- **`ESC ^`**: the bit layout of the second byte is not given.
- **`ESC k`** sent in draft: is the typeface stored for the next `ESC x 1`?
- **Factory switch settings** differ by market in the TM (TM 1-13) and
  not in the User's Manual (D-3).
- **The draft and NLQ glyphs** themselves: only the self-test and sample
  printouts in the manual show them.
