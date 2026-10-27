# lc10-rom

`extract.py` builds the Star LC-10's fonts, `papyrium-font-lc10`, from the
printer's firmware: the 64K program EPROM (a 27512 at IC4) of an LC-10
Colour, version 1.5, read from a friend's printer in October 2026
(`LC10-NX1P-1.5CL.bin`, CRC32 d0a807ec, SHA-1
d2fc05e55ee2b112d6ea3517cc9e554d996c8156). Star's technical manual lists
the seal labels `NX1P.1*` (monochrome) and `NX1P.1*.CL` (colour) for the
version 1 and 1.5 boards. The dump matches neither of the two the MESS
project listed in 2000, which are not public. The ROM is Star's; it is
kept uncommitted in `docs/local/star-lc10/`, and using it for everything
needed to simulate the LC-10 and LC-10 Colour was Rob's decision
(2026-10-27).

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

**Box drawing records** are 11 columns of 8 dots, no header, joining the
neighbouring cells. The printer's cell for them is 12 dots high; how it
extends them below the eighth dot is in the program, not yet read.

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

`disassemble.sh` disassembles the program with MAME's `unidasm`
(architecture `m740`), used as a tool only, into
`docs/local/star-lc10/LC10-NX1P-1.5CL.dis`. Build `unidasm` from a MAME
checkout with `make EMULATOR=0 TOOLS=1 NOWERROR=1`; the script looks for
it in `docs/local/m50734/`.

https://www.m50734.org is a community site about the M50734SP on a
development board. Its summary of register addresses disagrees with
MAME's and with itself, and most of its pages and downloads were missing
in October 2026, so MAME is the reference here.

## Not yet decoded

These are in the program and need reading it:

- how italics are slanted, in draft and NLQ;
- NLQ proportional spacing (the index gives no proportional widths);
- the block graphics' 12-dot cell;
- the paper movement between NLQ passes (half a dot, 1/144 inch, by the
  user manual; the technical manual gives a 1/216 inch minimum feed);
- colour: the order of the ribbon bands and the passes for the mixed
  colours.
