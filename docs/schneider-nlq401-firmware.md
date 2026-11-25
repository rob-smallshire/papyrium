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
(no italics). The meaning of each handler is still to be traced; the
Epson names above are where the dispatch puts them.

## Draft characters

The draft characters are at $16FD, codes 0x20 to 0x82, eleven bytes
each: one byte per column across the character's eleven half-dot
columns, the top pin in bit 7 and eight pins in all, so a character's
address is $159D plus eleven times its code ($0925). Eight more precede
them at $16A5, codes 0x18 to 0x1F, which the national character
conversion at $01B5 (through a table at $15F4) maps characters to; and
patterned data, perhaps block graphics, follows at $1B3E. Six characters print a pin lower: `;`, `_`, `g`, `p`, `q` and `y`,
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
