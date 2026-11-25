# Schneider NLQ401 firmware

What Papyrium has learnt from the Schneider NLQ401's firmware, its 16K
EPROM Rev 004 (`schneider_nlq401_rev004.bin`, SHA-1
b6374abaebb8e484e573caa21b1cc87f1554c8d6, the image MAME's `nlq401` device
lists), towards a model of the first-edition Centronics GLP (Model 3101),
which the NLQ401 is with Schneider's near letter quality added
(`docs/schneider-nlq401.md`). The ROM is kept uncommitted in
`docs/local/schneider-nlq401/`, beside the NLQ401's technical and service
manuals (English) and user manual (German); this note restates what they
show in our own words. The tools are in `tools/nlq401-rom/`.

Addresses written `$....` are CPU addresses, which here are also offsets in
the ROM.

## The hardware

From the NLQ401 technical manual (Control Electronics, sections 1-9):

- Two logic boards were made. B488013 has a NEC uPD7810 running a
  2764 or 27128 EPROM (8K, expandable to 16K); B488009 has a uPD7809
  running its own 8K masked ROM, with comparator inputs where the 7810 has
  an A/D converter. The NLQ401's is the B488013, with a 16K EPROM filling
  the CPU's 14-bit external addresses. The plain GLP and the Brother M-1009
  may have either.
- An M50780 expansion port (compatible with TI's TMS1025) gives seven
  groups of four lines, chosen by its S0-S2 inputs and written or read on
  R0-R3: it drives the paper feed and carriage motors and the head, and
  reads the switch panel and the limit switches on the B488013.
- Parallel input: each byte is latched with its strobe, which also sets a
  flip-flop driving BUSY and the CPU's INT1; the CPU reads the latch and
  clears the flip-flop, which ends BUSY and sends ACKNLG. BUSY lasts about
  350 µs for a printable character.
- The carriage stepper moves 1/60 inch a step, six steps a pica
  character; the paper feed stepper 1/216 inch a step, 36 to a 1/6 inch
  line.
- AN6 senses the head's temperature (about 60 °C lengthens BUSY by about
  half a second after printing) and AN7 the unregulated 24 V supply, by
  which the head's drive time is adjusted.
- Holding LF at power on prints the self test; LF with ON LINE gives the
  hex dump.

## Memory and vectors

The program runs from $0000; the CPU's 256 bytes of RAM are at
$FF00-$FFFF, with the stack at the top ($0000 less one) and the working
register page (V) at $FF, so `VV:xx` addresses $FFxx.

The timer and external interrupt vectors ($0008, $0018) save the
registers and call through RAM: the timer interrupt's current handler is
at $FF0E and the external interrupt's at $FF10, so the program changes
what each interrupt does by storing an address there.

## The command interpreter

**Control codes** ($0294): codes 0x09 to 0x1B dispatch through a table of
handlers at $02A0; the rest are ignored. In Epson's assignments: HT, LF,
VT (the same handler as LF), FF, CR (which tests port C bit 5 first), SO,
SI, DC2, DC4, CAN and ESC are handled; DC1, DC3 and the others are not.

**ESC** ($044F) sets a flag, and the next byte ($0454) chooses the
command: `x` goes to the near letter quality handler at $141B, and `-`
to `Z` through a table of 46 handlers at $046A, whose top bit marks a
command that takes parameters. Handled:

- without parameters: ESC 0, 1, 2, 6, 7, 8, 9, <, E, F, G, H, O, T;
- with parameters: ESC -, 3, A, C, D, I, J, N, S, U, W, and the bit-image
  commands K, L, Y and Z, which share one handler;
- ESC = and ESC I have handlers beside ESC x ($15E8, $1434), apparently
  Schneider's additions with its near letter quality.

Everything else in `-` to `Z` is ignored, among them ESC @ (there is no
initialise command), ESC M and P (no elite), ESC Q and R, and ESC 4 and 5
(no italics). On/off arguments go by their lowest bit (ESC x n at $141B:
`ANI A,$01`).

## Input

`receive_byte` ($083E) takes a byte only when INT1 has latched one (`SKIT
F1`), reads it inverted from port A and keeps seven bits. ESC = ($15E8)
sets VV:01 bit 3, after which every byte arrives with bit 7 set, a NUL as
0x80; the interpreter takes 0x80 ($0139) as the end of ESC = ($15EE). So
inside ESC = every code, control codes and ESC included, prints a
graphics character, and only a NUL gets out. DEL (0x7F) is ignored
($0134).

## The state

| Where | Bits |
|---|---|
| VV:00 | bit 7 character set 2 (ESC 6, 7), bit 6 paper-out ignored (ESC 8, 9), bit 5 the character being printed is graphics ($0908) |
| VV:01 | bit 0 SO enlarged, bit 1 ESC W enlarged, bit 2 underline, bit 3 ESC = |
| VV:03 | bit 0 double strike, bits 1-2 super/subscript, bit 3 condensed, bit 4 emphasized, bit 5 NLQ |
| VV:05 | bit 5 the character prints a pin lower ($091C) |
| VV:26, VV:27 | the line spacing and the spacing ESC A stored, in 1/216 inch; both 36 at power on, VV:26 27 with switch 2 on |
| $FF22, $FF32 | the form length and the skip over the perforation, in 1/216 inch |
| $FF2E | the position across the line, in 1/720 inch |
| $FF58- | the line buffer |

## Widths and the line

A character's width ($07F9) is 72/720 inch in pica and 42/720 (7/120)
condensed; emphasized and NLQ force pica, so they mask condensed; either
enlarged doubles it. The line ends at $1680 units, 8 inches, or $15A8 in
condensed, 132 characters. A character that would pass the end ($015A)
makes the firmware print the line and return the carriage, feeding a
line with switch 6 on ($037C, which takes the LF path at $038B) and not
with it off (the CR path, $02CF), then take the character again ($02DD).
CR ($02C6) feeds a line too with switch 7 on. The line end ($02D4)
cancels SO; ESC W ($05C7) cancels SO as it sets or clears itself; CAN
($0391) empties the buffer.

The commands that change how the head prints (SI, DC2, ESC E, F, G, H,
S, T, -, x, I) first print what the buffer holds ($0818), when the mode
really changes, so a line prints in segments, and each segment's head
travel runs from its first printing character to its last.

## Commands

- Line spacing ($04C6-$04EB): ESC 0 stores 27/216 inch and ESC 1 21/216,
  without feeding a line (the manual's examples suggest otherwise); ESC 3 n
  stores n/216, ignoring 0; ESC A n stores 3n/216 in VV:27, for 1 to 85,
  and only ESC 2 ($04D3) selects it, as on the Epson MX-80.
- ESC C n ($04EC) sets the form length to n lines at the current spacing
  and makes the current position the top of form; ESC C NUL n takes 1 to
  22 inches ($051C) and ignores anything else, changing nothing. Either
  way it runs on into ESC O ($0508) and cancels the skip over the
  perforation. ESC N n ($050A) is taken only if n lines are less than the
  form length.
- ESC D ($0529) stores at most 28 tab stops, from VV:28's count 2 to $1D.
- ESC I n ($1434) selects NLQ for 3 and draft for 1, and ignores other
  values; ESC x n for odd and even n.
- Bit image ($05E2): K, L, Y and Z share a handler. The count is n1 plus
  256 times the low three bits of n2, and 0 ignores the command. An image
  that would run past the end of the line ($0608) makes the line print and
  the carriage return first, as for a character that does not fit, and an
  image wider than the line loses its columns past the end ($063E). For Y
  and Z a dot that follows one in the previous column is left out
  ($0647). The data, seven bits a byte, fall on pins 2 to 8.
- Underline is printed on the ninth pin ($12C7, $1558), in every other
  column, and never for a graphics character or inside ESC =. With the
  segments above, the spaces at either end of an underlined run go
  unlined.
- Graphics characters (codes 128 and up) set VV:00 bit 5 and print in
  one direction; under NLQ they print in draft, struck twice.

- Printing a line ($0CCB): each character is a run of slots, 1/120 inch
  apart in draft and 1/480 in NLQ, through the print loops at $1000
  (rightwards) and $0D9E (leftwards), which take a glyph's columns one a
  slot. Enlarged (C bit 0, from VV:06) alternates the slots: in draft
  ($10A3) a column prints, then the next slot repeats it, VV:20 keeping
  its pins, so every dot is struck twice 1/120 inch apart; in NLQ
  ($10C9) the OR of a pair of columns, read as one word, prints in place
  of the even one and the slots between are blank, so enlarged NLQ is
  each pair of columns as one, 1/120 inch apart. Graphics characters
  print a column every other slot ($10F2), on the even ones.

Still to trace: the self test and hex dump, and the head's timing.

## Draft characters

The characters are eleven-byte entries from $159D plus eleven times the
location, for locations 0x18 to 0xFF: 0x18-0x1F character set 2's German
characters § Ä Ö Ü ä ö ü ß, which @ [ \ ] { | } ~ are converted to in set
2 ($01B5, through the table at $15F4), 0x20-0x7E ASCII and 0x80-0xFF the
Amstrad CPC's graphics. The firmware prints a character's eleven columns
from its entry's second byte ($0925 points at $159E), the top pin in bit
7, so the last column is the next entry's first byte, which text leaves
blank. Text columns are half-dots, 1/120 inch apart, no pin firing in
two successive ones; a graphics character's six columns are the even
ones, full dots 1/60 inch apart that join their neighbours.
`tools/nlq401-rom/extract.py` writes them as `glp-draft` and
`glp-graphics` (`papyrium.font.glp`).

Near letter quality characters, Schneider's, are two passes of 39
columns, 78 bytes from $194E plus 78 times the location, for 0x18 to
0x7E, ending at the ROM's last byte ($143E). The columns are 1/480 inch
apart, 48 to the pica cell, as the print loops count them (`LXI DE,$3027`
at $14F0: 48 slots, 39 columns; draft's are $0C0B, 12 and 11), eight to
the carriage's 1/60 inch step, as the NLQ timing table at $1463 has
eight phases; the second
pass falls 1/216 inch below the first, one step of the paper feed. They
are `glp-nlq`. Six characters print a pin lower: `;`, `_`, `g`, `p`, `q` and `y`,
which the routine at $08FD tests for by code, marking the character in
VV:05 bit 5. Every other character prints on the eight top pins as
stored.

Compared with `m1109-draft`, the second edition's draft characters as
reconstructed from the M-1109 manual's printed pages: 73 of the 95
printable characters were identical, 7 more identical a pin lower, and
15 differed. Most of the 15 (the apostrophe, full stop, `<`, grave accent,
`f`, `h`, `l`, `s` and `u`) were the same shapes one column to the side,
the descenders of `g` and `q` differed, and `$`, `4`, `N` and `t` by a dot
or two: errors in fitting dots to scans in which they merge. The printable
ASCII characters of `m1109-draft` now take their dots from this table
(`tools/nlq401-rom/correct_m1109_draft.py`).

The heights differ in three characters. The M-1109's printed output has
`,`, `:` and `j` a pin lower, as descenders, where the NLQ401's firmware
prints them as stored, leaving its colon above the baseline and out of
line with its semicolon, and its `j`'s dot a row above its `i`'s: the
NLQ401's list of characters to lower is the shorter. `m1109-draft` keeps
the heights the M-1109 prints at.
