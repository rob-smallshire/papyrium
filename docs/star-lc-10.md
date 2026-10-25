# Star LC-10 and LC-10 Colour behaviour notes

Facts about the Star Micronics LC-10 ("Multi-Font") and LC-10 Colour
that a future `lc10` printer model, through Papyrium's `escp` language,
would rely on. They are restated in our own words from Star's *LC-10
Multi-Font User's Manual* (1987) and *LC-10 Colour Printer User's
Manual*. Page numbers are the **printed** ones, not the scan's PDF page
index (the LC-10 scan runs eight pages ahead of the printed numbers in
the body, the LC-10 Colour scan seven). Unprefixed page numbers refer to
the LC-10 manual; "C" marks the LC-10 Colour manual (C 64). The manuals
are copyrighted and are kept, uncommitted, in `docs/local/lc10/` and
`docs/local/lc10-colour/`.

The LC-10 is a nine-pin printer with two personalities chosen by DIP
switch 1-6: Standard mode, which the manual says behaves like the Epson
LX-800 (an FX-80 descendant with NLQ), and IBM mode, like the IBM
Proprinter II (16). Appendix B marks every command Std., IBM or Both.
Most of these notes compare Standard mode against `docs/epson-fx80.md`
and `docs/brother-m1109.md`; IBM mode has its own section.

## DIP switches (14-17, reference card)

Two banks: DSW1 with eight switches and DSW2 with four. ON is towards
the back. They are read only at power-up. The factory setting is every
switch ON.

| Switch | Factory | Meaning |
|---|---|---|
| 1-1 | on | Page length 11 inches (off: 12 inches) |
| 1-2 | on | Auto CR: LF and `ESC LF` also return to the left margin (off: they only feed) |
| 1-3 | on | Orator chosen from the panel prints small capitals for lower case (off: true lower case, without descenders) |
| 1-4 | on | Automatic sheet feeder inactive (off: active) |
| 1-5 | on | Paper-out detector enabled, printing stops about an inch from the end of the paper (off: ignored) |
| 1-6 | on | Standard mode (off: IBM mode) |
| 1-7 | on | Standard mode: italics at 160-254 (off: IBM character set #2 graphics at 128-254). IBM mode: character set #2 (off: set #1) |
| 1-8 | on | CR only (off: CR also feeds a line) |
| 2-1 | on | RAM is a 4K input buffer (off: RAM holds download characters, with a one-line buffer) |
| 2-2..2-4 | on, on, on | Power-on international set; see below |

Switches 2-2, 2-3, 2-4 (on = 0, with 2-2 as the low bit): 0 USA,
1 France, 2 Germany, 3 England, 4 Denmark I, 5 Sweden, 6 Italy,
7 Spain I (17), reading off as 1. This is the same order as `ESC R` 0-7
on page 64 and the FX-80's numbering. In IBM mode with 1-7 on, the Denmark I
setting gives Denmark/Norway instead (17).

Note that the factory 1-2 makes LF also a carriage return, and 1-8 is
the switch that makes CR feed a line. A BBC Micro sending CR only needs
1-8 off. There is no switch for power-on NLQ, condensed, slashed zero,
skip-over-perforation or a beeper; there is no serial interface.

## Power-on state

Draft, pica, upright, Courier as the pending NLQ style (60), 1/6 inch
line spacing (55), page length 11 or 12 inches by 1-1, no top margin
(`ESC c` default 1, 73), no bottom margin, horizontal tabs every eight
columns from column 9 (79), no vertical tabs (VT acts as LF, 75), vertical
tab channel 0, international set by switches, standard or IBM character
set by 1-6 and 1-7, ROM characters, paper-out detection by 1-5,
bidirectional printing (88). Margins are not stated; the full line is
8 inches.

The top of form is where the paper is at power-on (27), and can be moved
from the panel or by `ESC C` (or IBM `ESC 4`). Semiautomatic loading of a
single sheet leaves the paper ready to print about one inch below its
top edge (7).

`ESC @` (89) returns settings to their power-up values and clears the
print buffer, but not the input buffer or the sheet feeder selection. It
does not say whether download characters survive, nor whether it resets
the top of form.

## Control panel (19-29)

Four switches (On Line, Paper Feed, Print Pitch, NLQ Type Style), which
act only when off-line, plus combinations and power-up functions.
Functions that change printer state:

- **Print Pitch** cycles the pitch. Standard mode: pica, elite,
  condensed pica, condensed elite, proportional pica, proportional
  elite. IBM mode: pica, elite, condensed pica, proportional pica,
  proportional elite (21-22). Condensed proportional can be had only by
  command (`SI` then `ESC p 1`).
- **NLQ Type Style** cycles draft, Courier, Courier italic, Sanserif,
  Sanserif italic, Orator, Orator italic (22). Orator here is small caps
  or lower case by switch 1-3. Draft italic and the other Orator variant
  can be had only by command (23).
- **Stay in panel pitch / style**: holding Print Pitch and/or NLQ Type
  Style at power-on locks the panel's choice against software (24). The
  locked commands are each marked "ignored if ... pressed during
  power-up" in Appendix B: pitch lock ignores `ESC P`, `ESC M`, IBM
  `ESC :`, `SI`, `ESC SI`, `DC2`, `ESC p`, IBM `ESC P n` and `ESC !` bits
  0-2; style lock ignores `ESC x`, `ESC k`, IBM `ESC I`, the italic
  commands and `ESC !` bit 6.
- **Hexadecimal dump** (Paper Feed and Print Pitch at power-on): received
  bytes print sixteen to a line as hex on the left and printable
  characters on the right; going off-line prints the last partial line
  (24-25).
- **Short self test** (On Line at power-on): six lines of a sliding
  character pattern, 8 inches wide (12). **Long self test** (Paper Feed
  at power-on): the full set in every style, repeating, and differing by
  mode (13).
- **Top of form** (NLQ Type Style + On Line): makes the current position
  the top of form (27).
- **Forward / reverse micro-feed** (On Line + Paper Feed / Print Pitch):
  small steps; the step size is not given (27-28).
- **Left / right margin** (NLQ Type Style + Print Pitch / Paper Feed):
  the head steps in 1/10 inch from the left (or right) end and the
  margin is set where the switches are released (28).
- **Page feed** (Paper Feed then On Line): eject a sheet or feed to the
  next top of form (27).
- **Paper parking** (Print Pitch + Paper Feed): fanfold is wound back out
  of the paper path so single sheets can be used, and fed back in when
  the bail is opened (11-12, 26-27).
- **Clear buffer** (Print Pitch, On Line, Paper Feed held three seconds)
  discards data waiting in the input buffer (28-29).

## Paper, printable area and interface (7-12, 53-57)

- Friction feed for single sheets 5.5 to 8.5 inches wide; a push tractor
  for fanfold 4 to 10 inches wide; up to three-part forms (55). The
  release lever selects friction (down) or tractor (up) (3), and several
  commands are ignored under friction feed (below).
- The line is 8 inches: 80 pica, 96 elite, 137 condensed pica, 160
  condensed elite columns (32, 55).
- The paper-out detector stops printing about an inch before the end of
  the paper unless 1-5 is off or `ESC 8` is in force (50, 74).
- Centronics parallel only, 7 or 8 bit (53, 56-57). Pins 14 and 15 are
  unconnected, so there is no AUTO FEED XT line; SELECT IN is always
  high; RESET (31) restores the power-up state.
- Data buffer 4K when RAM is not used for download characters, one line
  when it is (53).
- Draft prints bidirectionally (or unidirectionally by command), logic
  seeking; NLQ and graphics always unidirectionally (53). Speeds: 120 cps
  draft pica, 30 cps NLQ pica (53).

## Character formation (4, 22-23, 54-55, 91-94)

Character matrices as given in the specification (54), rows by columns:

| Style | Matrix |
|---|---|
| Draft pica | 9 x 9 |
| Courier and Orator, pica | 18 x 23 |
| Courier and Orator, elite | 18 x 19 |
| Sanserif, pica and elite | 18 x 18 |
| Condensed pica | 18 x 12 |
| Condensed elite | 18 x 10 |
| IBM block graphics, pica | 12 x 11 |

- Draft characters use the FX-80 grid: 11 columns at 1/120 inch in a
  1/10 inch pica cell, eight of the nine pins (ascender or descender),
  with no two horizontally adjacent dots (91-92).
- NLQ characters are printed in two passes with the paper moved **half
  a dot** between them, the dot pitch being 1/72 inch, so 1/144 inch,
  giving 16 or 18 rows; columns are on a 1/240 inch grid, again with no
  adjacent dots in one row (83, 93-94). The column counts fit that grid:
  23 + 1 blank column is 24/240 = 1/10 inch (pica), 19 + 1 = 1/12 inch
  (elite), 12 is close to 1/17 inch and 10 + 2 = 1/20 inch. The M-1109
  instead feeds 1/216 inch between NLQ passes.
- The condensed rows have 18 dots, so condensed apparently exists in
  NLQ too (Open questions).
- Four NLQ type styles: Courier, Sanserif, Orator with small capitals
  and Orator with lower case (4). Orator is one dot taller than the
  others (23), and its lower-case variant has no descenders on g, j, p,
  q, y (16). The small capitals variant prints lower-case codes as small
  capitals.
- Italic exists for draft and all four NLQ styles (5, 54).
- Pitches: pica 10, elite 12, condensed pica 17, condensed elite 20
  (Standard mode only), and proportional spacing for each (55).
- Emphasized affects draft only (61); for bold NLQ the manual
  recommends double-strike. Emphasized cannot combine with condensed
  (51). Double-strike thickens horizontal strokes by a second pass after
  a slight paper movement, and cannot be used with super/subscript (62).
- Extra-large characters: double width, double height, double width and
  height, quadruple width and height (55); see `ESC W`, `ESC w`, `ESC h`
  and `ESC [ @`. Double-height characters are always NLQ (70).
- The IBM block graphics cell is 12 dots high, more than the nine pins
  cover, so block and line-drawing characters must be printed in two
  passes to join between lines at 1/6 inch spacing (inferred from 54
  and the 12-dot download extension on 84).

## Command reference

"Mode" is Std, IBM or Both. "vs FX-80" flags what differs from
`docs/epson-fx80.md` (and from the M-1109 where that is the closer
comparison). Many single-parameter commands accept either the code
(0, 1) or the digit ("0", "1"); the table writes the code. Pages are
LC-10 printed pages; the LC-10 Colour manual has the same commands on
pages within one or two of these.

### Control codes

| Bytes | Mode | Effect | Page | vs FX-80 |
|---|---|---|---|---|
| BEL (7) | Both | Beep | 88 | |
| BS (8) | Both | Back one column; ignored at the left margin | 77 | |
| HT (9) | Both | Next horizontal stop; ignored if none left on the line; the skipped gap is not underlined | 79 | |
| LF (10) | Both | Print the line and feed; with 1-2 on also return to the left margin | 72 | CR by switch |
| VT (11) | Both | Next vertical stop and left margin; LF if no stops; next top of form if past the last stop | 75 | no default stops |
| FF (12) | Both | Feed to the next top of form, left margin; ejects with the ASF | 74 | |
| CR (13) | Both | Print the line, return to the left margin; with 1-8 off also feed | 77 | |
| SO (14), `ESC SO` | Both | Double width for the rest of the line; cancelled by LF, VT, FF, DC4, `ESC W 0` | 67 | |
| SI (15), `ESC SI` | Both | Condensed: pica to 17 cpi, elite to 20 cpi (IBM: always 17) | 66 | condensed elite |
| DC1 (17) | Both | Back on line after DC3 / `ESC Q 3` (not after the panel switch) | 87 | |
| DC2 (18) | Both | Cancel condensed. IBM: also back to pica | 66 | |
| DC3 (19) | Std | Off line: ignore everything until DC1; the lamp stays on | 87 | |
| DC4 (20) | Both | Cancel SO double width, not `ESC W 1` | 67 | |
| CAN (24) | Both | Delete the line in the print buffer | 86 | |
| DEL (127) | Both | Delete the last character received, if not yet printed and not part of a command | 86 | |

### Font and style

| Bytes | Mode | Effect | Page | vs FX-80 |
|---|---|---|---|---|
| `ESC x 0` / `ESC x 1` | Both | Draft / NLQ | 59-60 | FX-80 lacks |
| `ESC k n` | Both | NLQ style: 0 Courier, 1 Sanserif, 2 Orator small caps, 3 Orator lower case; held until NLQ is selected | 60 | new |
| `ESC I n` | IBM | 0 draft, 1 draft elite, 2 Sanserif, 3 or 7 Courier, 4 draft download, 5 draft elite download, 6 NLQ download | 59-61, 84-85 | Proprinter |
| `ESC 4` / `ESC 5` | Std | Italic on / off | 61 | |
| `FS 4` / `FS 5` | IBM | Italic on / off | 61 | |
| `ESC E` / `ESC F` | Both | Emphasized on / off (draft only) | 61 | |
| `ESC G` / `ESC H` | Both | Double-strike on / off | 62 | |
| `ESC - n` | Both | Underline on (1) / off (0); IBM block graphics and tab gaps not underlined | 62 | |
| `ESC _ n` | Both | Overline on (1) / off (0); tab gaps not overlined | 62-63 | new |
| `ESC S n` / `ESC T` | Both | Superscript (0) or subscript (1) / off; pitch unchanged | 63 | |
| `ESC ~ n` | Both | Slashed zero (1) / plain zero (0) | 65 | new (FX-80: switch) |

### Pitch and size

| Bytes | Mode | Effect | Page | vs FX-80 |
|---|---|---|---|---|
| `ESC P` | Std | Pica (condensed elite to condensed pica) | 66 | |
| `ESC M` | Both | Elite (condensed pica to condensed elite in Std; IBM drops condensed) | 66 | |
| `ESC :` | IBM | Elite | 66 | |
| `ESC W n` | Both | Double width on (1) / off (0) | 67 | |
| `ESC p n` | Both | Proportional on (1) / off (0) | 67-68 | |
| `ESC P n` | IBM | Proportional on (1) / off (0) | 67-68 | |
| `ESC ! n` | Both | Master select: 1 elite, 2 proportional, 4 condensed, 8 emphasized, 16 double-strike, 32 double width, 64 italic, 128 underline | 68 | bits 1, 6, 7 new |
| `ESC SP n` | Std | Add n/240 inch (0-127) after each character | 68 | new |
| `ESC h n` | Both | Size: 0 normal, 1 double, 2 quadruple; 3/4 double lower/upper half, 5/6 quadruple lower/upper half | 69 | new |
| `ESC w n` | Both | Double height on (1) / off (0), line spacing unchanged; suspends script and condensed | 69 | new |
| `ESC [ @ 4 0 0 0 n m` | Both | Height and line spacing by n, width by m (below) | 70 | new |

### Character sets

| Bytes | Mode | Effect | Page | vs FX-80 |
|---|---|---|---|---|
| `ESC t n` | Std | Standard set (0) or IBM set (1, #2 unless `ESC 7` was sent) at 128-254 | 63-64 | new |
| `ESC 6` / `ESC 7` | Both | IBM set #2 / #1; held until `ESC t 1` in Std | 64 | different meaning |
| `ESC R n` | Std | International set 0-13 | 64 | four more sets |
| `FS R n` | IBM | International set 0-13 | 64 | |
| `ESC \ n1 n2` | IBM | Print the next n1 + 256 n2 bytes as characters, no controls; codes with no glyph print a space | 65 | Proprinter |
| `ESC ^` | IBM | As `ESC \` for one byte | 65 | Proprinter |

### Vertical position

| Bytes | Mode | Effect | Page | vs FX-80 |
|---|---|---|---|---|
| `ESC 0` | Both | 1/8 inch spacing | 70 | |
| `ESC 1` | Both | 7/72 inch spacing | 71 | |
| `ESC 2` | Std | 1/6 inch spacing | 71 | |
| `ESC 2` | IBM | Bring the last `ESC A` into force (1/6 inch if none) | 71 | Proprinter |
| `ESC 3 n` | Both | n/216 inch, 0-255; n = 0 is zero spacing in Std, ignored in IBM | 71 | |
| `ESC A n` | Both | n/72 inch, 0-85; IBM stores it for `ESC 2` and ignores 0 | 71 | |
| `ESC J n` | Both | Feed n/216 inch once, 1-255; spacing unchanged; no horizontal move with 1-2 off | 72 | |
| `ESC j n` | Both | Reverse feed n/216 inch, 1-255; ignored under friction feed | 72 | |
| `ESC LF` | Both | Reverse line feed; left margin with 1-2 on; ignored under friction feed | 72 | new |
| `ESC f 1 n` | Both | Feed n lines, 0-127 | 72 | new |
| `ESC FF` | Both | Back to the top of the current page; ignored under friction feed | 74 | new |
| `ESC 4` | IBM | Top of page here | 73 | Proprinter |
| `ESC C n` | Both | Page length n lines (Std 1-127, IBM 1-255); this line is the top | 73 | |
| `ESC C 0 n` | Both | Page length n inches (Std 1-22, IBM 1-127); this line is the top | 73 | |
| `ESC c n` | Both | Top margin: printing starts on line n (1-255) | 73 | new |
| `ESC N n` | Both | Bottom margin n lines (Std 0-127, IBM 0-255); reset by a new page length | 73 | |
| `ESC O` | Both | Cancel top and bottom margins | 74 | also top |
| `ESC B n1... 0` | Both | Up to 16 vertical stops, 1-255, in current lines | 74-75 | |
| `ESC e 1 n` | Both | Vertical stops every n lines, 1-127 | 75 | new |
| `ESC b c n1... 0` | Both | Vertical stops in channel c (0-7) | 75 | |
| `ESC / c` | Both | Select vertical tab channel c | 75 | |
| `ESC 8` / `ESC 9` | Both | Ignore / obey paper-out; override switch 1-5 | 74 | |

### Horizontal position

| Bytes | Mode | Effect | Page | vs FX-80 |
|---|---|---|---|---|
| `ESC l n` | Both | Left margin, column n of the current pitch (pica if proportional) | 76 | ranges differ |
| `ESC Q n` | Std | Right margin, column n is the last on the line | 76 | ranges differ |
| `FS Q n` | IBM | Right margin | 76 | |
| `ESC X n1 n2` | Both | Left and right margins together | 77 | new |
| `ESC 5 n` | IBM | CR also feeds (1) / not (0); overrides 1-8 | 77 | Proprinter |
| `ESC a n` | Both | Justify: 0 left, 1 centre, 2 right | 78 | new |
| `ESC D n1... 0` | Both | Horizontal stops, 1-255, up to 32 (IBM 28); `ESC D 0` clears all | 78 | |
| `ESC e 0 n` | Both | Horizontal stops every n columns, 1-127 | 78-79 | new |
| `ESC R` | IBM | Reset tabs: horizontal every 8 from column 9, clear vertical | 79 | Proprinter |
| `ESC \ n1 n2` | Std | Relative move in 1/120 inch: right if n2 0-63, left by (n1 + 256(n2 - 64)) if 64-127; max 6 inches | 79 | new |
| `FS \ n1 n2` | IBM | Relative move, as above | 79 | |
| `ESC $ n1 n2` | Both | Absolute position (n1 + 256 n2)/60 inch from the left margin; max 8 inches | 79 | new |
| `ESC f 0 n` | Both | Absolute position at column n (0-127) from the left margin | 80 | new |

### Graphics

| Bytes | Mode | Effect | Page | vs FX-80 |
|---|---|---|---|---|
| `ESC K n1 n2 d...` | Both | 60 dpi, eight pins, max 480 | 80 | |
| `ESC L n1 n2 d...` | Both | 120 dpi, max 960 | 80 | |
| `ESC Y n1 n2 d...` | Both | 120 dpi, adjacent dots skipped | 80 | |
| `ESC Z n1 n2 d...` | Both | 240 dpi, adjacent dots skipped, max 1920 | 81 | |
| `ESC * m n1 n2 d...` | Both | Mode m 0-6 (table below) | 81 | |
| `ESC ? s m` | Both | Make `ESC` s (K, L, Y or Z) use mode m (0-6) | 81 | |
| `ESC ^ m n1 n2 d...` | Std | Nine-pin graphics, 60 (m 0) or 120 (m 1) dpi, two bytes per column | 82 | |

### Download characters

| Bytes | Mode | Effect | Page | vs FX-80 |
|---|---|---|---|---|
| `ESC : 0 0 0` | Std | Copy ROM characters to download RAM | 82 | |
| `FS : 0 0 0` | IBM | Copy ROM characters to download RAM | 82 | |
| `ESC & 0 n1 n2 a d1..d11 ...` | Both | Define draft characters n1-n2 (draft selected) | 82-83 | code range, attribute |
| `ESC & 0 n1 n2 a d1..d46 ...` | Both | Define NLQ characters n1-n2 (NLQ selected) | 83 | new |
| `ESC = n1 n2 DC4 a0 a1 a2 d1..d11` | IBM | Define draft characters (Proprinter form) | 84 | Proprinter |
| `ESC % n` | Both | Download set (1) / ROM set (0) | 84-85 | |

All are ignored while switch 2-1 is on.

### Macro, data and other

| Bytes | Mode | Effect | Page | vs FX-80 |
|---|---|---|---|---|
| `ESC + ... RS` | Both | Define a macro of up to 16 bytes, any but RS (30) | 85 | new |
| `ESC + 1` | Both | Run the macro | 85 | new |
| `ESC >` | Both | Force bit 7 to 1 | 86 | |
| `ESC =` | Std | Force bit 7 to 0 | 86 | |
| `FS =` | IBM | Force bit 7 to 0 | 86 | |
| `ESC #` | Both | Take bit 7 as sent | 86 | |
| `ESC i n` | Both | Immediate print on (1) / off (0); ignored under friction feed | 87 | |
| `ESC Q 3` | IBM | Off line until DC1 | 87 | Proprinter |
| `ESC U n` | Both | Unidirectional (1) / bidirectional (0) | 88 | |
| `ESC <` | Both | Home the head now; the rest of the line prints left to right | 88 | |
| `ESC EM 0` | Both | Manual feed even with the ASF fitted | 88 | |
| `ESC EM 4` | Both | Automatic sheet feeder | 89 | |
| `ESC EM R` | Both | Eject the sheet from the ASF | 89 | |
| `ESC EM T n` | Both | Skip n/6 inch at the top of each ASF sheet | 89 | |
| `ESC @` | Both | Reset | 89 | |

The four `ESC EM` commands also have a text form, `((0))`, `((4))`,
`((R))` and `((T))` n (bytes 40 40 x 41 41), and all four are ignored
while switch 1-4 is on (88-89). These "double parenthesis" commands
are the same mechanism the LC-10 Colour uses for its embedded commands
(see below).

That is 106 table rows covering about 125 byte forms (counting each
value of `ESC I` and each `ESC EM` command once).

FX-80 features the LC-10 does not document: `ESC I n` in Standard mode
(the FX-80's printable control codes; on the LC-10 `ESC I` is IBM-only
font selection), `ESC 6` and `ESC 7` as "print codes 128-159" (here they
choose IBM character sets), `ESC s` (half speed) and the FX-80's
default vertical tabs. Unknown escape sequences are not discussed.

## Command details

### Line ends and feeds (72-77)

- LF and `ESC LF` move to the left margin when switch 1-2 is on (the
  factory setting); VT and FF always do. `ESC J` and `ESC j` do not
  move horizontally when 1-2 is off, so with 1-2 on they presumably do.
- CR prints and returns; with 1-8 off (or IBM `ESC 5 1`) it also feeds.
- `ESC J`, `ESC j`, `ESC LF`, `ESC FF` and `ESC i` are all marked as
  ignored under friction feed; for `ESC J` this looks like an error
  (Open questions).
- `ESC f 1 n` feeds n lines at the current spacing.

### Forms (73-75)

- `ESC C` stores the length as a distance, so later spacing changes do
  not alter it, and makes the current line the top of form.
- `ESC c n` sets a top margin of n - 1 lines; `ESC N n` a bottom margin
  of n lines (skip-over-perforation); `ESC O` cancels both. A new page
  length cancels the bottom margin.
- `ESC B` and `ESC b`: up to 16 stops, a value not greater than the one
  before ends the list (as on the FX-80, not the M-1109), stops fixed as
  distances.
- VT with no stops is LF; past the last stop it goes to the next top of
  form.

### Horizontal layout (76-80)

- Margin ranges (the right margin must be at least two columns right of
  the left margin):

  | Pitch | `ESC l` | `ESC Q` |
  |---|---|---|
  | Pica | 0-76 | 4-80 |
  | Elite | 0-91 | 5-96 |
  | Condensed pica | 0-130 | 7-137 |
  | Condensed elite | 0-152 | 8-160 |
  | Double-width pica | 0-38 | 2-40 |
  | Double-width elite | 0-45 | 3-48 |
  | Double-width condensed pica | 0-64 | 4-68 |
  | Double-width condensed elite | 0-76 | 4-80 |

  The FX-80 allows pica 0-78 and 2-80. Margins are fixed positions:
  changing pitch later does not move them. The manual does not say
  whether they clear the buffer or reset the tabs, as the FX-80's do.
- Horizontal tab stops are fixed physical positions; changing pitch or
  margins after setting them does not move them (51).
- `ESC $` counts from the left margin in 1/60 inch, `ESC \` moves in
  1/120 inch, and `ESC f 0 n` counts columns from the left margin. Each
  is ignored if the result lies outside the margins.
- `ESC a` justification applies to text that follows: centre between the
  margins or flush right (the manual's demonstration, 44, centres lines
  printed with `ESC SP` spacing).

### Print modes (61-70)

- `ESC !` sets all eight attributes at once, including proportional
  (bit 1), italic (bit 6) and underline (bit 7), which the FX-80's
  master select leaves alone.
- The manual gives no priority table like the FX-80's or M-1109's; it
  says only that emphasized and condensed cannot combine (51) and
  double-strike and super/subscript cannot (62).
- `ESC h n` (69): extra-high characters hang from the cap line of normal
  ones, the base line moving down for them, and the next line feed is
  doubled (n 1, 5, 6) or quadrupled (n 2). For n 3-6 the manual asks for
  1/9 inch spacing (`ESC 3 24`), unidirectional printing, and each line
  sent twice, once for each half.
- `ESC w 1` (69) prints double height without moving the base line and
  without changing line spacing, and suspends super/subscript and
  condensed until `ESC w 0`.
- `ESC [ @` (70) takes the fixed bytes 4 0 0 0, then n and m. n sets line
  spacing (0 unchanged, 16 single, 32 double, added to) and height (0
  unchanged, 1 single, 2 double): 0, 1, 2, 16, 17, 18, 32, 33, 34. m 1 is
  single width, 2 double width (as `ESC W`). Double height is always NLQ.
- Superscript and subscript keep the pitch (63); their vertical size is
  not given.
- Overline (`ESC _`) is new; tab gaps are not overlined.

### Character sets (63-65, 99-106)

- **Standard set** (100-101): ASCII at 32-126; codes 0-31 are controls
  or print nothing; 128-159 mirror the controls with bit 7 set (NUL,
  BEL, BS-SI, DC1-DC4, CAN, EM, ESC) and print nothing otherwise; 160-254
  are italic versions of 32-126; 255 is DEL. With 1-7 off or `ESC t 1`,
  128-254 come from IBM set #2 instead. Unlike the FX-80 there is no way
  to print international characters at 0-31 or 128-159 in Standard mode.
- **IBM character set #2** (102-103): ASCII at 32-126; 0-31 controls,
  except that 3-6 print the card suits and 21 the section sign; 128-254
  the upper half of the IBM PC character set (accented letters, currency,
  block and box drawing, Greek and mathematical signs); 255 blank. The
  same arrangement as the M-1109's Mode II set 2.
- **IBM character set #1** (104): as set #2, but 128-159 are controls
  mirroring 0-31, for 7-bit systems that use `ESC >`.
- **Additional set** (105): 32 glyphs for codes 0-31 (faces, suits,
  bullets, musical notes, arrows and the like, the IBM PC's low glyphs),
  printable only in IBM mode through `ESC \` and `ESC ^`.
- **International sets** (106): 14 sets substituting at codes 35, 36,
  64, 91-94, 96, 123-126 and, in the IBM set, 155 and 157 (cent and yen).

  | n | Set | Notes |
  |---|---|---|
  | 0-8 | USA, France, Germany, England, Denmark I, Sweden, Italy, Spain I, Japan | as the FX-80's 0-8 |
  | 9 | Norway | as the M-1109's 9 |
  | 10 | Denmark II | as the M-1109's 10 |
  | 11 | Spain II | new: a acute, inverted !, N tilde, inverted ?, e acute, i acute, n tilde, o acute, u acute |
  | 12 | Latin America | new: as Spain II with u diaeresis at 96 |
  | 13 | Denmark/Norway | new: no ASCII changes; 155 and 157 become o slash and O slash |

  The M-1109's set 11 is England II; the LC-10's 11 is Spain II.

### User-defined characters (82-85, 91-98)

- Switch 2-1 must be off; RAM then holds the characters and the input
  buffer shrinks to one line (17). At most 192 draft characters (codes
  32-127 and 160-255) or 78 NLQ characters (54, 94).
- `ESC & 0 n1 n2`: n1 and n2 both in 32-127 or both in 160-255; 32 and
  127 are best avoided (82). The FX-80 accepts 0-255.
- Draft: attribute byte then 11 column bytes, bit 7 the top dot. Bit 7
  of the attribute set means an ascender on pins 1-8, clear a descender
  on pins 2-9 (as the FX-80). Bits 4-6 give 0-7 dots of left space and
  bits 0-3 the cell width, 4-15 dots including that space; both matter
  only in proportional spacing (83). The FX-80 reads the same bits as
  first and last printed column.
- NLQ: attribute byte then 46 bytes, a 16 x 23 grid at twice the draft
  density each way. Bytes 1-23 are the first pass, 24-46 the second, the
  paper moving up half a dot between. Within a column, odd rows belong
  to the first pass and even rows to the second (94). The attribute is
  ascender/descender in bit 7, left space in bits 4-6 and right space in
  bits 0-3 (83, Figure C-2).
- Draft must be selected before defining draft characters, NLQ before
  NLQ ones (82-83).
- After `ESC : 0 0 0` any code not redefined prints the ROM character
  (94).
- IBM `ESC = n1 n2 DC4 a0 a1 a2 d1..d11` (84): n1 + 256 n2 counts the
  bytes that follow; a0 the first code; a1 ascender (bottom pin unused)
  or descender (top pin unused), and a downward extension to 12 dots;
  a2 bits 4-6 the first column printed and bits 0-3 the width (at most
  11), followed by a compulsory blank column. Selected by `ESC % 1` or
  `ESC I` 4, 5 or 6.

### Bit image (80-82, 54)

| m | Mode | dpi | Max per line | Adjacent dots | Same as |
|---|---|---|---|---|---|
| 0 | Single density | 60 | 480 | printed | `ESC K` |
| 1 | Double density | 120 | 960 | printed | `ESC L` |
| 2 | Double density, double speed | 120 | 960 | skipped | `ESC Y` |
| 3 | Quadruple density | 240 | 1920 | skipped | `ESC Z` |
| 4 | CRT I | 80 | 640 | printed | |
| 5 | Plotter | 72 | 576 | printed | |
| 6 | CRT II | 90 | 720 | printed | |

These match the FX-80's modes 0-6 exactly; there is no mode 7 (the
M-1109 has one). Dots past the right margin are dropped. Bit images
print unidirectionally. `ESC ^` gives nine-pin images at 60 or 120 dpi,
the ninth pin from bit 7 of the second byte, as on the FX-80; it is
Standard mode only.

## IBM mode (16, 21-22, 45, 59-89)

Proprinter II-style. Most Both-mode commands work as in Standard mode;
the differences:

- `FS` (28) replaces `ESC` for italic (`FS 4`, `FS 5`), international
  set (`FS R`), right margin (`FS Q`), relative move (`FS \`), bit-7
  forcing (`FS =`) and ROM copy (`FS : 0 0 0`).
- Reassigned escapes: `ESC 2` (execute `ESC A`), `ESC 4` (top of page),
  `ESC 5 n` (auto line feed), `ESC :` (elite), `ESC P n` (proportional),
  `ESC Q 3` (off line), `ESC R` (reset tabs), `ESC \` and `ESC ^` (print
  any code), `ESC =` (download), `ESC I n` (fonts).
- Missing: `ESC SP`, `ESC t`, `ESC ^` graphics, `DC3`, Standard `ESC P`
  and condensed elite. DC2 returns to pica from elite or condensed.
- `ESC A` is only stored until `ESC 2`; `ESC A 0` and `ESC 3 0` are
  ignored.
- `ESC C` and `ESC N` take larger values; `ESC D` takes up to 28 stops.
- Character sets #1 or #2 by 1-7 (or `ESC 7`, `ESC 6`); the standard set
  with italics cannot be selected.
- The panel pitch cycle has no condensed elite.
- The manual's BASIC demo needs `DC2` for pica, `FS 4`/`FS 5` for
  italics, `FS Q` for the margin and `ESC A n ESC 2` for spacing (45).

## LC-10 Colour

The LC-10 Colour manual is the LC-10 manual revised; DIP switches,
panel, character sets, matrices, graphics and download characters are
the same (C 14-17, C 53-54, C 97-104). Differences:

- **Colour selection**: `ESC r n` (C 64), Both modes, n 0-6 as code or
  digit: 0 black, 1 red, 2 blue, 3 violet, 4 yellow, 5 orange, 6 green.
  Ignored when a colour ribbon is not fitted. The manual's BASIC sample
  changes colour freely within a line and within double-height text
  (C 41-43).
- **Ribbon**: a four-band black, blue, red and yellow fabric cartridge,
  rated at a million draft characters per colour (C 53). The manual does
  not say how violet, orange and green are produced; overprinting red
  and blue, red and yellow, and blue and yellow is the natural reading.
- **Embedded commands** (C 34-36, C 59-70, C 88): a capital letter in
  doubled parentheses followed by a digit, sent as ordinary text, act as
  commands. Bytes: 40 40 letter 41 41 then the digit character.

  | Command | Effect | Equivalent |
  |---|---|---|
  | `((F))0` .. `((F))3` | Courier, Sanserif, Orator small caps, Orator lower case | `ESC k n` with NLQ |
  | `((F))9` | Draft | `ESC x 0` |
  | `((S))0` .. `((S))3` | Normal, double width, double height, both | new "select character size" (C 70) |
  | `((C))0` .. `((C))6` | Colour | `ESC r n` |
  | `((B))0` / `((B))1` | Double-strike off / on | `ESC H` / `ESC G` |
  | `((I))0` / `((I))1` | Italic off / on | `ESC 5` / `ESC 4` |
  | `((0))`, `((4))`, `((R))`, `((T))` n | Sheet feeder commands | `ESC EM ...` (also on the LC-10) |

  `((F))` and `((I))` obey the panel style lock. A line holding only
  commands prints as a blank line, and the commands take no space on
  the line (C 36). `((S))` does not move the base line; double height is
  NLQ (C 70).
- **Data buffer** 8K instead of 4K (C 53).
- **Short self test** prints seven lines, each in a different colour
  (C 12).
- `ESC x 1` is documented as selecting Courier unless a style was chosen
  earlier (C 60); the LC-10 says the same through `ESC k`'s initial
  value.
- The print sample and printed page numbers differ slightly; the
  command summary (C 118-120) adds `ESC r` and the parenthesis forms.

## For Papyrium

Reusable from the FX-80 and M-1109 work:

- The `escp` interpreter's Standard-mode core: control codes, line
  spacing (`ESC 0 1 2 3 A J`), forms (`ESC C`, `ESC N`, `ESC O`), tabs
  and channels (`ESC D`, `ESC B`, `ESC b`, `ESC /`), margins (with new
  ranges), pica/elite/condensed/proportional pitches, condensed elite
  (already needed for the M-1109), emphasized, double-strike,
  underline, super/subscript, double width (`SO`, `ESC W`), master
  select (extended to bits 1, 6, 7), international sets 0-10, bit image
  modes 0-6 with `ESC ?` and `ESC ^`, MSB control and `ESC @`.
- Mechanism settings: nine-pin head at 1/72 inch, 1/120 inch draft grid
  with the adjacent-dot rule, 1/216 inch feeds, 8-inch line, 11 or
  12-inch forms by switch. The auto CR switch (1-2) is a new model
  option alongside the existing auto line feed one (1-8).

New work:

1. **IBM mode** as an alternative command table on the same model,
   selected by switch 1-6: the FS-prefixed commands, the reassigned
   escapes, deferred `ESC A`, IBM character sets #1 and #2 and the
   additional set, `ESC \`/`ESC ^` print-any-code, the Proprinter
   download form. Much of it is shared with the M-1109's Mode II, so
   building it once for both is the efficient order.
2. **Four NLQ typefaces with italics**, Orator's two variants and its
   extra dot of height, on a 1/240 by 1/144 inch two-pass grid. These
   must be reconstructed from printed output as our own font data.
3. **Character sizes**: `ESC h` double and quadruple size with the
   cap-line alignment and temporary line spacing, `ESC w` double height,
   `ESC [ @`, and the half-character modes 3-6.
4. Star additions: `ESC SP`, `ESC a` justification (needs the whole line
   before placing it), `ESC $`, `ESC \`, `ESC f`, `ESC e`, `ESC c`,
   `ESC X`, `ESC _` overline, `ESC ~`, `ESC LF`, `ESC FF`, `ESC j`,
   macros (`ESC +`), international sets 11-13, `ESC t`.
5. **NLQ download characters** (46-byte form) and the restricted draft
   code range and attribute meaning.
6. **Colour** (LC-10 Colour): a per-dot colour in the page model, `ESC r`,
   and rendering of the four ribbon bands and their mixtures, plus the
   embedded `((X))n` command recogniser, which must sit in front of
   ordinary text handling yet still capture every byte.
7. Model options for friction versus tractor feed (several reverse feeds
   are ignored under friction) and the panel pitch/style locks.

## Open questions

- The international set numbering on page 106 (3 Denmark I, 4 Sweden,
  5 Italy, 6 England) disagrees with `ESC R` on page 64 and the DIP
  switch table (3 England, 4 Denmark I, 5 Sweden, 6 Italy). Page 64
  matches the Epson convention and is presumably right.
- The IBM download command (84) is shown as `ESC =` in the ASCII column
  and the command summary but as 38 (`&`) in the decimal and hex
  columns. The Proprinter uses `ESC =`; which does the LC-10 accept?
- `FS 5` is printed with hex 1C 33 (61); decimal 28 53 is surely right.
- `ESC J` is said to be ignored under friction feed (72), which would
  make it useless on single sheets; probably copied from `ESC j`.
- The NLQ matrices for condensed pica and condensed elite (18 rows)
  suggest NLQ condensed exists; whether NLQ elite and condensed are
  separate designs or derived is not said.
- Whether `ESC w` grows upward from the base line (69-70) while `ESC h`
  hangs from the cap line; the two descriptions of "base line" are hard
  to reconcile without samples.
- Super/subscript size and position, and how they print in NLQ.
- The draft download attribute is described as left space and cell
  width (83), the FX-80 as first and last column; is the LC-10's
  arithmetic really different? The NLQ attribute uses right space.
- Whether `ESC @` erases download characters or resets the top of form.
- Whether margin commands clear the buffer or reset tab stops, and the
  power-on margins.
- What `ESC a` does with tabs, `ESC $` and mixed pitches on a justified
  line.
- Priority among pitch and weight modes is not given.
- What an unknown escape sequence does.
- Whether codes 0-31 that are not controls are swallowed or print as
  spaces in Standard mode.
- How violet, orange and green are made on the Colour, how colour
  passes order on a line, and whether `ESC r` affects graphics and
  download characters (the sample prints download characters in each
  colour, so it does).
- Where `((` sequences that do not form a valid command go: printed as
  text, or swallowed?
- The micro-feed step size and the head's first printing position on
  the paper are not given.
