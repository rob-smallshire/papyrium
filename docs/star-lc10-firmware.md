# Star LC-10 firmware

What Papyrium has learnt from the Star LC-10 Colour's firmware, version
1.5: its 64K program EPROM (a 27512 at IC4), read from a friend's printer
in October 2026 (`LC10-NX1P-1.5CL.bin`, CRC32 d0a807ec, SHA-1
d2fc05e55ee2b112d6ea3517cc9e554d996c8156). Star's technical manual lists
the seal labels `NX1P.1*` (monochrome) and `NX1P.1*.CL` (colour) for the
version 1 and 1.5 boards. The dump matches neither of the two the MESS
project listed in 2000, which are not public.

The ROM is Star's. It is kept uncommitted in `docs/local/star-lc10/`;
using it for everything needed to simulate the LC-10 and LC-10 Colour
was Rob's decision (2026-10-27). This document restates what it shows in
our own words. `docs/star-lc-10.md` holds the behaviour from the manuals
and refers here where the firmware settles a question; the tools that
read the ROM are in `tools/lc10-rom/`.

Addresses written `0x....` are file offsets in the ROM; `$....` are CPU
addresses (the program) or zero-page RAM locations.

## What the ROM holds

The upper 32K of the file is the program, at CPU addresses
0x8000-0xFFFF; the lower 32K is data, at 0x8000-0xFFFF of the CPU's
separate data space (below). The data:

| At | Holds |
|---|---|
| 0x0000 | NLQ index: 8 tables of 211 four-byte entries |
| 0x1A60 | Draft characters: 211 ten-byte records |
| 0x229E | IBM block and box drawing (0xB0-0xDF): 48 eleven-byte records |
| 0x24AE | Five eleven-byte pieces: the integral halves and the shades' other phases |
| 0x24E5 | NLQ first-pass columns |
| 0x5108 | NLQ second-pass columns, 0x2C23 after the first |
| 0x7D6E | Motor speed tables |

The international sets are in the program, twelve locations each for the
codes `` # $ @ [ \ ] ^ ` { | } ~ ``: `ESC R` 1 (France) at 0x8040 up to 12
(Latin America) at 0x80C4, in reverse order, then 0 (USA) at 0x80D0.

**Locations.** Draft and every NLQ table hold the same 211 locations:
the slashed zero (0), the IBM PC's low symbols (1-31), ASCII (32-126),
the IBM PC's characters 0x7F-0xAF at the same codes, its 0xE0-0xFF at
0xB0-0xCF, then ø, ¤ and ß (0xD0-0xD2). Within 0xB0-0xCF Star changed
four: 0xBD is Ø (the IBM PC's phi), 0xC4 a degree sign and 0xC5 an acute
accent (its integral halves, which the box drawing table draws), and
0xCF a diaeresis (its blank). 0xC8, the IBM PC's degree sign, repeats
0xC4. No location holds an italic character: the printer slants the
upright ones.

**Draft records** are a header byte, then 9 columns of 8 dots, bit 7 the
top and a 1 bit a dot. Header bit 7 set puts the character on the upper
eight pins, clear on the lower eight. Bits 4-6 and 0-3 are the first and
last columns proportional spacing allows for: the columns of the dots,
except that narrow characters (`` ! " ' ( ) , . : ; ` | ``, ¡, ´ and ∙) are
widened.

**Block graphics records** are 11 columns of 8 dots, no header. IBM
codes 0xB0-0xDF are records 0-0x2F, and the integral halves 0xF4 and 0xF5
are records 0x30 and 0x31, so they print full height from here rather
than from their locations (`$8475`, `$8569`); records 0x32-0x34, three
shade patterns, are not reached from that mapping. The 11 columns fill
a pica cell but its last column, so lines join the next cell.

**NLQ index entries** are a header, a width and the big-endian CPU
address of the first pass's columns (subtract 0x8000 for the file
offset); the second pass's columns are 0x2C23 bytes further on. Tables
0-3 are pica Courier, Orator with small capitals, Orator with lower case
and Sanserif; tables 4-7 the same in elite. The header is bit 7 as for
draft (clear moves the character down a pin, two half-dot rows), the left
space in bits 4-6 and the right space in bits 0-3, in 1/240 inch columns;
left space, width and right space make 23 (pica) or 19 (elite). Columns
are 8 dots, bit 7 the top, a 1 bit a dot; the first pass prints the even
rows and the second, half a dot lower, the odd rows. Most glyphs are
shared between the pica and elite tables and between the two Orators;
elite has narrower forms of the widest characters.

## The CPU and the program

The CPU is a Mitsubishi M50734 (TM 15, 84), a member of the MELPS 740
family: the 6502's instructions plus the T flag, bit set, clear and test
(`SEB`, `CLB`, `BBS`, `BBC`), `LDM`, special-page calls and others. It has
no internal memory, and it is made for printers: Centronics `STBout` and
`BUSYout`, a stepper motor controller driving the carriage motor (phases
`Ha`-`Hd`, on P2) and the paper feed motor (`Va`-`Vd`), timers, a UART,
an A/D converter and clocked serial I/O.

Its pin P05, when selected as `DME` and made an output, strobes a second,
"data" memory space for operand reads and writes, instruction fetches
still coming from program memory. The reset code sets the P0 function
register (`$F5`) to 0x20 and the P0 direction register (`$F7`) to 0x34,
so DME is on from power-up and every ordinary load reads the data space,
where the board puts the ROM's lower half at 0x8000-0xFFFF. That is why
the NLQ index holds addresses from 0x8000 up.

Registers, from MAME's M50734 emulation (`src/devices/cpu/m6502/m50734.cpp`,
BSD-3-Clause, by AJR, written for the Commodore MPS-1200, which has the
same CPU); the M50734 data sheet is not available:

| At | Register |
|---|---|
| `$DA`-`$DB` | Timer X |
| `$DC`-`$E1` | Timers and prescalers |
| `$E2`-`$E3` | Step counter |
| `$E8` | Serial I/O |
| `$E9`, `$EA` | A/D control, A/D result |
| `$EB` | Port P4 (input) |
| `$EC` | Phase counter |
| `$ED` | P2/P3 function |
| `$EE`-`$EF`, `$F0`-`$F1` | Ports P3 and P2 (data, direction) |
| `$F2` | P1 latch |
| `$F3`-`$F4` | Port P1 (data, direction) |
| `$F5` | P0 function |
| `$F6`-`$F7` | Port P0 (data, direction) |
| `$F8`-`$F9` | Stepper motor control |
| `$FA` | Timer S |
| `$FC` | Timer W |
| `$FD`-`$FF` | Interrupt control |

The vectors:

| Vector | Interrupt | Handler |
|---|---|---|
| `$FFF4` | CNTR | `$F3AA` |
| `$FFF6` | HE/VE (stepper motor controller) | `$F3C5` |
| `$FFF8` | Timers | `$F15F` |
| `$FFFA` | `_INT1` (P00) | `$F3E2` |
| `$FFFC` | `_INT2` (P01) and `BRK` | `$FF7E` |
| `$FFFE` | Reset | `$8100` |

`tools/lc10-rom/disassemble.py` disassembles the program with MAME's
`unidasm` (architecture `m740`), used as a tool only, into
`docs/local/star-lc10/LC10-NX1P-1.5CL.dis`. Build `unidasm` from a MAME
checkout with `make EMULATOR=0 TOOLS=1 NOWERROR=1`; the script looks for
it in `docs/local/m50734/`.

https://www.m50734.org is a community site about the M50734SP on a
development board. Its summary of register addresses disagrees with
MAME's and with itself, and most of its pages and downloads were missing
in October 2026, so MAME is the reference here.

## Navigating the program

`tools/lc10-rom/lc10-map.txt` is the map of the program: where it keeps
data rather than code, and a name and a line of description for every
routine, entry point and RAM location traced so far, every command
handler among them. `disassemble.py` reads it, disassembles only the
code, so the listing stays on instruction boundaries after the tables in
the program, prints the command tables as decoded entries (`'I' ->
$9513  ibm_esc_i`), heads each named routine with its description, and
notes the name of each address an instruction refers to:

```
; ibm_esc_m: ESC M in IBM mode: elite, dropping condensed, NLQ again if asked for
9490: 07 39 f9  bbs 0, $39, $948c       ; panel_state
```

To find a command, look up its handler in the map or the decoded
tables (search the listing for `; ibm_esc_x:`); to follow a RAM bit, search
for its name. When tracing finds something, give it a name in the map and
run the script again, and write up here what it shows.

Where to start:

| At | Is |
|---|---|
| `$8100` | Power on |
| `$83B8` | `next_byte`: the main loop's next byte; every handler ends here |
| `$8423` | Control codes: `standard_controls` (`$B175`) or `ibm_controls` (`$B1A6`) by IBM mode |
| `$B1D7`, `$B2DC` | ESC: `standard_escapes` (`$B1F4`) or `ibm_escapes` (`$B2F9`) |
| `$B3E1`, `$B3F8` | FS: `standard_fs` (`$B3F7`, empty) or `ibm_fs` (`$B40E`) |
| `$B424` | `find_command`: the search all the tables share |
| `$C9A7` | The line sequencer, which prints a line |
| `$E5A9`, `$FB88` | The character setup and column builders |

The state the commands change is in a few zero-page bytes, named in the
map: `$37` and `$38` the DIP switches, `$3A` and `$3B` the modes set from
them, `$41` the pitch, `$42` and `$5C` the print attributes and mode.

## What the program settles

Addresses are CPU addresses in the program; RAM names are zero-page
locations.

**Escape commands** are looked up in tables of three-byte entries, the
command byte and the handler's address, ending with 0x00: Standard mode
at `$B1F4`, IBM mode at `$B2F9`. `ESC 4` and `ESC 5` set and clear bit 1
of `$42` (unless the panel's style lock, bit 1 of `$39`, is on); `ESC p`
is bit 5, `ESC _` bit 7. `$5C` bit 2 is NLQ (`ESC x 1` also sets bit 4 and
clears emphasized, bit 7), bit 1 double-strike. `$41` is the pitch: bit 0
pica, bit 1 elite, bit 2 condensed. `ESC k n` puts n in bits 4-5 of
`$A1`. Each character in the line buffer carries its attributes, ORed
with `$42` into `$30` when the line is printed.

**NLQ typefaces.** The index table for each typeface is found through a
table at `$E810`: pica `$8000` (Courier, `ESC k 0`), `$89E4` (Sanserif,
1), `$834C` (Orator with small capitals, 2), `$8698` (Orator with lower
case, 3); elite, at `$E818`, `$8D30`, `$9714`, `$907C`, `$93C8`. The
second pass's columns are the first pass's address plus `$2C23`
(`$E705`).

**Italics** are slanted as the character's columns are built
(`$FD03`): each column's dots are moved right by an amount that grows
up the column, into a buffer wider than the character.

- Draft: the two lowest dots of the byte (bits 1-0) stay, bits 3-2 move
  one column right, bits 5-4 two, bits 7-6 (the top pins) three.
- NLQ: each bit moves one column (1/240 inch) right for each pin above
  the lowest, bit 0 not at all and bit 7 seven columns, for each pass
  alike, so a second-pass row moves as far as the first-pass row above
  it.

The slant is counted within the column byte, so a descender character
(pins 2-9) slants about its own lowest pin. The advance does not change:
after the columns are sent, the output backs up over the overhang
(`$F6BC`), so it overlaps the next character.

**NLQ passes and paper movement.** The paper motor is half-stepped,
each step 1/432 inch: `ESC 0`, `ESC 1` and `ESC 2` set 54, 42 and 72
steps, and `ESC 3 n` sets 2n. An NLQ line is printed (`$CA94`) as the
first pass, a feed of 3 steps (1/144 inch, `$CEA9`), and the second
pass. The ninth pin prints in both passes, so its rows fall at 48 and 51
steps: every NLQ row is 1/144 inch below the last, as the user manual
says. The technical manual's 1/216 inch is only the finest feed a
command can ask for.

**Which characters each pitch prints.** The character setup (`$E5A9`)
and the column builders (`$FB88`) choose by pitch:

| Pitch | Draft | NLQ |
|---|---|---|
| Pica | Sanserif's second pass at half width: 12 columns at 1/120 inch | The typeface's pica table: 24 columns at 1/240 inch |
| Elite | The draft table: 9 + 1 columns at 1/120 inch | The typeface's elite table: 19 + 1 columns at 1/240 inch |
| Condensed pica | Sanserif's second pass at half width: 14 columns at 1/240 inch | Each pass at half width: 14 columns at 1/240 inch |
| Condensed elite | As condensed pica: 12 columns at 1/240 inch | As condensed pica: 12 columns at 1/240 inch |
| Proportional | Sanserif's second pass at half width, its width + 2 columns at 1/120 inch | The pica table, its width + 4 columns at 1/240 inch |

Proportional spacing works in elite too, unlike the FX-80's, where
elite masks it: draft is the same in either pitch, and NLQ takes the
typeface's elite table. Nor does proportional spacing force emphasized
printing, as the FX-80's does: the column builders test emphasized
(`$5C` bit 7) alone.

Proportional draft does not use the draft table's first and last
columns for ROM characters: like pica, it is made from Sanserif at half
width, its advance half Sanserif's width plus 2 columns (`$FAD7`). The
draft table's header bytes matter only for characters copied into RAM
with `ESC :`, which keep them as their attribute bytes.

"At half width" (`$FBBB`) ORs each pair of columns into one and removes
any dot the column before printed, so no pin fires in successive
columns; the left and right spaces are halved too. Every Sanserif entry
has an even width, an even left space and an odd right space, so the
halved pica cell is always exactly 12 columns: the Sanserif table is laid
out for this. The draft table, which `ESC :` also copies into RAM for
download characters, serves only elite at fixed pitch.

**The block graphics' 12-dot cell.** The input code marks a block
graphics character in its attribute byte (bit 4), and a line holding one
(`$3D` bit 7) is printed with an extra pass. After the line's pass or
passes the paper is fed so that the head's pins 5-8 fall on rows 8-11 of
the cell, 24 steps (1/18 inch) after the first pass, and only the block
graphics print, each column's two lowest dots (bits 1 and 0) repeated
twice (`$FC50`). Rows 8-11 thus repeat rows 6 and 7, and a cell is 12
dots, 1/6 inch, high: at 1/6 inch line spacing vertical lines join. In
NLQ both passes print the block graphics, the second 1/144 inch lower,
and the extension pass is repeated 1/144 inch lower too. The movement is
taken off the next line feed (`$8D1D`). Elite prints 9 of the 11
columns, in a 10-column cell.

**The line sequencer** (`$C9A7`) prints a line by its mode: plain draft
in one pass (`$CA37`); draft double-strike, superscript and subscript as
two passes 3 steps (1/144 inch) apart (`$CA94`); NLQ (`$CADD`) as its
first pass, 3 steps, its second pass. The other branches, for double
height (`$5D`) and the like, are not yet traced.

**NLQ spacing** (`$F971`, `$FBFF`). A character's columns are its left
space as blanks, its glyph, then its right space and a further gap as
blanks. In fixed pitch the gap is one column, so the cell is 24 columns
in pica (23 + 1). In proportional spacing the left and right spaces are
dropped and the gap is 4 columns: the advance is the glyph's width plus
4/240 inch.

## IBM mode

IBM mode is bit 5 of `$37`, which holds DIP switch 1-6 off; besides the
switch, two commands the manual does not mention change it: `ESC 0x01`
(`$B167`) clears it, Standard mode, and `ESC 0x02` (`$B16E`) sets it, IBM
mode, each also switching the IBM table (`$3A` bit 2). `ESC @` sets `$3A`
and `$3B` from `$37` and `$38` again (`$9957`).

Control codes (`$8423`), escapes and the commands after FS each have a
table for each mode. Of the escapes, IBM mode's table shares most
handlers with Standard mode's, and those test the mode where they differ;
it has its own for SI, `ESC 2`, `4`, `5`, `:`, `=`, `E`, `F`, `M`, `P`,
`Q`, `R`, `S`, `T`, `\`, `^` and `x`, adds `ESC I`, leaves out `ESC SP`,
and gives `ESC t` to the unknown command routine, which drops the
letter. Of the control codes, SI and DC2 have IBM handlers and DC3 is
unknown, so ignored. FS gives Star's commands: `FS 4`, `5`, `:`, `=`,
`Q`, `R` and `\` run Standard mode's `ESC` handlers.

**NLQ.** `$5C` bit 4 is NLQ asked for and bit 2 NLQ printing. IBM mode
suspends NLQ as the Proprinter does: `ESC x 1` and `ESC I 2`, `3`, `7` ask
for it (`$94D3`), and it prints unless emphasized, a script or condensed
is on; `ESC E`, `ESC S` and SI stop it printing, and `ESC F`, `ESC T`,
DC2 and `ESC M` start it again if it was asked for. Standard mode's
`ESC x 1` instead clears emphasized, and its `ESC E` is ignored in NLQ.

**`ESC I`** (`$9513`) takes 0-7 or the digits: 0 and 1 draft from the ROM
(`$94FA`, and `$42` bit 3, the download set, cleared), 1 then running
`ESC M`; 2 Sanserif and 3 or 7 Courier, asked for as by `ESC x 1`, the
download set left as it was; 4 and 5 the download set in draft
(`$959E`), emphasized off, 5 then `ESC M`; 6 the download set in NLQ
(`$95B6`) whatever the other modes, emphasized and condensed off, and
Sanserif. None changes the pitch but 1 and 5. 4, 5 and 6 do nothing to
the set or quality while the RAM is a buffer (`$3B` bit 4, switch 2-1),
though 5 still chooses elite and 6 Sanserif.

**Pitch.** SI (`$94A4`) is 17 cpi from pica or elite; DC2 (`$9472`)
returns to pica from elite or condensed; `ESC M` and `ESC :` (`$9490`,
`ESC :` entering one byte earlier, on a NOP) choose elite and drop
condensed. IBM mode's `ESC E` (`$95F8`) works at any pitch, where
Standard mode's (`$95D9`) works only at pica. `ESC !` (`$92F8`) calls each
mode's own SI, DC2, `ESC M`, `ESC E` and `ESC F`: in IBM mode condensed
(bit 2) leaves elite (bit 0) unread, and emphasized (bit 3) takes effect
only at pica, in either mode.

**Commands whose argument may be another byte.** `ESC P` (`$96D9`) and
`ESC 5` (`$9165`) read their argument raw: 0 and 1 set proportional and
the CR line feed (`$3A` bit 7); any other byte is taken as received, after
`ESC P` has chosen pica, so Standard mode's `ESC P` still works.

**Spacing and feeds.** `ESC A` (`$97EB`) keeps its spacing in `$0112`
in IBM mode, for `ESC 2` (`$97CD`) to bring in, 72 steps (1/6 inch) after
`ESC @`; it and `ESC 3` (`$97D5`) ignore 0 in IBM mode. `ESC J` (`$A0ED`)
and `ESC j` (`$A12A`) return the carriage first in IBM mode when a line
feed does (`$3A` bit 6, switch 1-2 on).

**Tabs.** `ESC D` (`$A501`) keeps up to 32 stops, 28 in IBM mode, as
column numbers, and HT (`$A562`) moves that many columns of the pitch
they were set in, in either mode. The power-on stops (`$8A6B`, also IBM
`ESC R`) are columns 8, 16, ... in Standard mode and 9, 17, ... in IBM
mode: Star read the Proprinter's "every eight from column 9" as nine
columns in. `ESC B` and `ESC b` (`$A6C3`) keep up to 16 vertical stops;
in IBM mode each line n but 1 counts as n - 1 (`$A757`).

**Character sets.** `$3A` bit 2 is the IBM table and bit 3 set #2, from
switch 1-7 at power on (`$9060`): in Standard mode 1-7 off sets both, on
clears both; in IBM mode bit 2 is always set and 1-7 on sets bit 3.
`ESC t` changes only bit 2, and `ESC 6` and `ESC 7` (`$939E`, `$93A6`)
change bit 3 only while bit 2 is set. So in Standard mode with 1-7 on,
`ESC t 1` gives set #1, whatever `ESC 6` sent before it; the user manual
says set #2 unless `ESC 7` was sent. With set #2 the low codes 3-6 and 21
print, the card suits and §, in either mode (`$8445`).

**Not modelled by Papyrium:** the mode switching commands `ESC 0x01` and
`ESC 0x02`, which would change the language part way through a job, and
the control panel's locks.

## Download characters

`ESC %` takes one argument (`$AC19`) and `ESC &` (`$A8FD`) defines draft
characters, or NLQ ones when NLQ is selected (`$A980`); both are ignored
while switch 2-1 keeps the RAM as a buffer. Defining one kind erases the
other, the RAM holding one or the other. A range given high to low is
swapped, and codes 0-31 and 128-159 have their data read but are not
defined. In proportional spacing a draft download character prints its
columns from the attribute's first to its last, plus one unless the
last is 11, and the two-column gap (`$E560`).

## Underline and overline

The column builder (`$F818`-`$F853`) adds the lines after a lowered
character's byte has been shifted down a pin. Overline sets the byte's
top bit, so it is always pin 1, and in NLQ prints in the first pass
only. Underline fires the ninth pin, and in NLQ prints in the second
pass only, half a dot lower than draft's.

## Character sizes

`ESC h n` sets one bit of `$5D` (`$9A92`): 1 double (0x08), 2 quadruple
(0x80), 3 and 4 the lower and upper halves of double (0x02, 0x04), 5 and
6 the lower and upper halves of quadruple (0x20, 0x40), 0 none. `ESC w 1`
(double height on the base line) is bit 3 of `$BC` (`$9B1E`). Each
change first prints the line waiting in the buffer and cancels
superscript and subscript. The line sequencer has a branch for each
(`$CA01`-`$CA25`): `$BC` bit 3 and double to `$CB65`, quadruple to
`$CC7A`, its upper and lower halves to `$CC54` and `$CC46`, double's
upper and lower halves to `$CB4E` and `$CB19`.

Papyrium follows this: double size turns each 1/144 inch NLQ row into
a 1/72 inch pin row, two passes 8 pins apart covering the character,
and repeats each 1/240 inch column's dots two columns on to fill the
widened gap (`$FC7D`). Quadruple size is taken to do the same twice
over, two pins a row and three columns a column; that is inferred, not
traced. A line holding enlarged characters feeds as far as the largest
asks, even after normal size returns, as the sequencer's deferred feed
does.

Superscript and subscript appear to be made by keeping every other row
of the character's columns, the pass choosing which (`$E2F8`); this is
not yet confirmed.

## Colour

**Colours are ribbon bands.** `ESC r n` (`$9828`) keeps a four-bit code
in bits 0-3 of `$A1`, one bit for each band of the ribbon, from the table
at `$9865`:

| n | Colour | Code | Bands |
|---|---|---|---|
| 0 | Black | 1 | black |
| 1 | Red | 4 | magenta |
| 2 | Blue | 8 | cyan |
| 3 | Violet | 4 + 8 | magenta and cyan |
| 4 | Yellow | 2 | yellow |
| 5 | Orange | 2 + 4 | yellow and magenta |
| 6 | Green | 2 + 8 | yellow and cyan |

Each character in the line buffer keeps its code, and the line keeps a
summary of the colours it uses in `$A0` (from the table at `$86A6`): bit
0 yellow, 1 green, 2 orange, 3 cyan, 4 magenta, 5 violet, 6 black, and
bit 7 whenever a mixed colour is present.

**One pass per band.** A line is printed once for each band its colours
use (`$CF28`): `$CFBD` black, `$CFCF` yellow, `$CFE1` magenta, `$CFF3`
cyan. A pass prints every character whose code includes its band
(`$D04A`), so a mixed colour prints the same dots twice, once from each
band. Every pass of the line's mode (both NLQ passes, the block graphics'
extension and so on) is made in each band.

**Order of the passes.** The ribbon can only be advanced, one band at a
time, in the cycle black, yellow, magenta, cyan, black (below), so
without mixed colours the bands are printed in that cycle starting from
the band the ribbon is on (`$9E`). With a mixed colour (`$A0` bit 7) the
order is lightest first: black only if the ribbon is already on it, then
yellow, magenta and cyan, then black. Green is thus yellow then cyan,
violet magenta then cyan, orange yellow then magenta, as the 1989
review of the NX-1000 Rainbow describes.

**Changing band** (`$EEBB`). When the band wanted (`$9F`: 0x01 black,
0x04 yellow, 0x10 magenta, 0x40 cyan) is not the one in place (`$9E`),
the carriage runs to the left end and makes a short stroke there (`$EFBC`,
46 steps out and back) for each band it must advance, `$9E` rotating two
bits each time. This is the lift cam and ribbon change levers of the
technical manual, worked by the carriage at the home position.

## Not yet decoded

- How the enlarged sizes build their columns and which rows each pass
  prints (the routines around `$E2F8` and `$D2B5`-`$D4A3`), and the
  feeds between their passes.
- Superscript and subscript, to confirm.
- The three shade records 0x32-0x34, which nothing found so far reads.
