# Panasonic KX-P1080 family behaviour notes

Facts about the Panasonic KX-P1080 family of 9-pin dot-matrix printers
that a Papyrium model of them relies on, restated in our own words from
Panasonic's manuals and from a dump of a KX-P1080U's firmware. This is the
research for those models; none is built yet.

Sources, kept uncommitted in `docs/local/panasonic-kx-p1080/`, each OCRed
with `tools/manual-ocr/ocr.sh`:

- *KX-P1080 Operating Instructions*, the US edition (120 V), complete,
  106 pages, cited as "M" with its printed page numbers (M 4-31).
- *KX-P1080i Operating Instructions*, the North American edition of the
  later model, from Manualslib, 116 pages at low resolution, cited as "I"
  (I 4-35). Its PDF pages 1-4 are Manualslib's index.
- *KX-P1080U Operating Instructions*, six pages photographed from a
  friend's copy: specifications (1-3), switches and indicators, detectors,
  DIP switches and initialisation (3-1 to 3-4), self test, hex dump and
  buffer (3-5). Cited as "U".
- `KX-P1080U.BIN`, 16 KB, SHA-1 4839aebb1c22222bf43eb4c6de6287909c0d0ce6,
  CRC32 2e40308e: the program EPROM of a KX-P1080U. What it shows is
  under Firmware below.

Tables and numbers have been checked against the page images, not the
OCR, which garbles them.

## The family

- **KX-P1080** (M): the original, Epson-style printer. 100 cps draft,
  20 cps NLQ.
- **KX-P1080U** (U): the UK model, the one whose firmware we have: 240 V
  50 Hz mains, shipped with the England character set. Its six pages agree
  with M wherever they overlap (specifications, switches, DIP switches,
  initialisation, self test, buffer), so M describes it for the rest.
- **KX-P1080i** (I): a later model. 120 cps draft and 24 cps NLQ, and an
  IBM mode on DIP switch 1 with three personalities, IBM Matrix Printer and
  IBM Graphics Printer modes I and II, chosen by switches 5-7 or `ESC m`
  (below). Its Standard mode is M's command set.

None of the manuals names Epson, but the command set is the Epson FX-80's
with Epson's later NLQ commands and some of Panasonic's own (Compatibility).
No manual mentions the IBM Proprinter.

Papyrium's first model should be the KX-P1080U, since its firmware is to
hand; the KX-P1080 differs from it only in its default character set and
mains, and the KX-P1080i is a variant with an IBM mode and faster speeds.

## Specifications (U 1-3, M 1-3, I 1-3)

| | Draft | NLQ |
|---|---|---|
| Matrix (H x V) | 9 x 9 | 18 x 18 |
| Dot pitch | 1/120 in x 1/72 in | 1/240 in x 1/144 in, two passes |
| Speed (KX-P1080, U) | 100 cps pica and elite | 20 cps |
| Speed (KX-P1080i) | 120 cps | 24 cps |

- 9 wires, dots 3/254 in (0.3 mm) across.
- Character cell 0.078 in wide by 0.095 in high; super- and subscript
  0.053 in high.
- Pitches, with columns on the 8-inch line: pica 10 cpi (80), elite 12
  (96), semi-compressed 15 (120), compressed 17 (137), and their elongated
  (double width) forms 5 (40), 6 (48), 7.5 (60) and 8.5 (68); proportional
  spacing besides. Compressed lines are 132 columns at initialisation, 137
  only once `ESC Q` moves the right margin (M 4-8).
- Emphasized prints at half speed.
- Text prints both ways, seeking the next line's start; bit images left to
  right only. A line feed takes about 100 ms at 1/6 in.
- Fanfold paper 4 to 10 in wide on the tractor; single sheets 4 to 9 in
  wide and 5 to 14.3 in long by friction; up to three parts.
- Receive buffer 1 KB. Centronics parallel interface; a serial board is
  mentioned as an option but not described.
- Character set: 96 ASCII, 96 italic ASCII and 32 international
  characters for 11 countries. No block graphics.

## Controls (U 3-1, M 3-1, M 3-2)

- ON LINE switch and lamp: the printer comes up on line if it has paper,
  off line if not. FF feeds to the next top of form and makes it the new
  top of form; LF feeds a line, repeating while held. Both work on or off
  line. POWER and PAPER/ERROR lamps; the latter blinks on an overload,
  when the head is blocked, from which only switching off recovers.
- Paper out, 1.5 in from the end of the paper: the printer goes off line
  but LF and FF still work; loading paper and pressing ON LINE resumes.
- Print mode selector, three positions, read at initialisation:
  - **Std. Pgm.**: draft, and the only position in which commands change
    the print mode (`ESC P` and `ESC M` say so; M 4-11, 4-12).
  - **NLQ**: near letter quality; the manual says commands cannot change
    it.
  - **Comp.**: compressed, 132 columns; DC2 does not cancel it, `ESC E`
    and `ESC p` have no effect.
  The manuals contradict themselves on how far `ESC !` and `ESC w` work in
  the NLQ and Comp. positions (Open questions).

## DIP switches (U 3-3, M 3-3)

One bank of eight, read at initialisation into memory, which commands can
then change.

| Switch | On | Off | KX-P1080U shipped | KX-P1080 shipped |
|---|---|---|---|---|
| 1 | Paper-out detector ignored (printing goes on to the end of a sheet) | Paper-out detector used | Off | Off |
| 2 | 12-inch page | 11-inch page | Off | Off |
| 3 | A line feed with every CR, whatever the interface's AUTO FEED XT | CR feeds only if AUTO FEED XT is low | Off | Off |
| 4 | Skip 1 inch over the perforation (`ESC N 6`) | No skip | Off | Off |
| 5-7 | International set, below | | Off, off, on: England | On, on, on: USA |
| 8 | 7-bit data | 8-bit data | Off | Off |

Switches 5, 6 and 7 give the set number's bits 0, 1 and 2, a switch off
being a 1: USA (all on), France, Germany, England (5 and 6 off), Denmark I,
Sweden, Italy, Spain (all off). Japan, Norway and Denmark II are reached
only by `ESC R`. M gives SW4 both as a 1-inch skip and as three lines
either side of the perforation, the same at 1/6 inch spacing.

On the KX-P1080i, switch 1 is the emulation: on for Standard, off for IBM
mode, the paper-out detector moving to switch 2 and page length losing
its switch. With switch 1 off, switches 5-7 choose the IBM personality
rather than the set: all off, or 7 on, Graphics Printer mode II; 6 on and
7 off, Graphics Printer mode I; 5 on, 6 and 7 off, Matrix Printer (I 3-3).

## Self test, hex dump and initialisation (U 3-4, U 3-5)

- Holding LF while switching on prints the 96 ASCII characters over and
  over until switched off. Holding LF and FF starts the hex dump, printing
  every byte received in hexadecimal and obeying no controls, until
  switched off. Neither layout is described.
- Initialisation, at power on, on the interface's PRIME line or by `ESC @`:
  the head goes home; the line buffer and, except for `ESC @`, the receive
  buffer are cleared; vertical tabs are cleared and horizontal tabs set
  every 8 columns; the DIP switches are read again; the print mode follows
  the selector switch; the current position becomes the top of form; every
  mode set by command is cancelled; the printer goes on line.

## Control codes (M 4-3 to 4-9, M Appendix A)

The manual lists sixteen; BEL is not among them, nor in the code chart.
Codes 128-159 obey the same controls as 0-31 unless `ESC 6` makes them
print, and 255 is DEL.

| Code | Effect |
|---|---|
| BS | Prints the line so far, then moves back one character of the current width; nothing under justification |
| HT | Next horizontal stop; a stop behind the head is skipped, one past the line end prints the line and feeds; the gap is not underlined |
| LF | Prints the line and feeds; ends SO's double width; feeding into the skip zone goes to the next top of form |
| VT | Prints and feeds to the next vertical stop; as LF with no stops, as FF with none below |
| FF | Prints and feeds to the next top of form |
| CR | Prints and returns; feeds too with SW3 on or AUTO FEED XT low |
| SO, ESC SO | Double width to the end of the line, ended by LF, VT, FF, DC4, `ESC W 0` or initialisation, not by `ESC J` or `ESC f 1` |
| SI, ESC SI | Compressed, 17 cpi; ignored in elite and proportional; emphasized masks it without cancelling it |
| DC1, DC3 | Select, deselect; while deselected everything is discarded |
| DC2 | Cancels compressed (not the selector's Comp.) |
| DC4 | Cancels SO's double width (not `ESC W 1`) |
| CAN | Discards the line not yet printed |
| DEL | Deletes the last text character in the line buffer; nothing under justification |

## Escape commands (M 4-10 to 4-68)

Arguments that switch something on or off, or choose among a few values,
accept the code, the digit, and either with bit 7 set: 0, 48, 128 or 176
for 0, and so on.

| Bytes | Effect | Notes |
|---|---|---|
| `ESC !` n | Master select | bit 0 elite, 2 compressed, 3 emphasized, 4 double strike, 5 double width; bit 1 has no meaning and bits 6-7 must be 0: Epson's layout without its proportional, italic and underline bits |
| `ESC #`, `ESC =`, `ESC >` | Bit 7 as received, forced clear, forced set | not applied to bit-image data; `ESC >` with `ESC 6` makes every control printable, recoverable only by switching off |
| `ESC *` m n1 n2 | Bit image, density m 0-6 | 60, 120, 120 at double speed, 240, 80, 72, 90 dpi, as Epson's |
| `ESC K`, `L`, `Y`, `Z` | Bit image at 60, 120, 120 double speed, 240 dpi | Y and Z print no dot in the column after a printed one |
| `ESC ^` m n1 n2 | 9-pin bit image, two bytes a column | the second byte's bit 7 is pin 9; n counts columns |
| `ESC ?` c m | Make `ESC K`, `L`, `Y` or `Z` use density m | |
| `ESC -` n | Underline on, off | pin 9; not under HT gaps or bit images |
| `ESC 0`, `1`, `2` | 1/8, 7/72, 1/6 inch spacing | |
| `ESC 3` n, `ESC A` n | n/216, n/72 (0-85) inch spacing | |
| `ESC J` n | Print and feed n/216 inch once | the head does not return |
| `ESC 4`, `ESC 5` | Italic on, off | draft and NLQ |
| `ESC 6`, `ESC 7` | Codes 128-159 and 255 print italic international characters; cancel | |
| `ESC 8`, `ESC 9` | Paper-out detector off, on | as SW1 |
| `ESC <` | Head home for the next line | |
| `ESC @` | Initialise | keeps the receive buffer |
| `ESC B` n... 0 | Up to 16 vertical stops, in lines from the top of form | kept as distances; cleared by a page length |
| `ESC C` n, `ESC C 0` n | Page length in lines (1-127) or inches (1-22) | this line becomes the top of form; clears vertical stops and the skip |
| `ESC D` n... 0 | Up to 32 horizontal stops, in columns of the current pitch from the left margin | pica columns in proportional spacing |
| `ESC E`, `F`, `G`, `H` | Emphasized on, off; double strike on, off | double strike is a second pass 1/216 inch lower, with no effect in NLQ or scripts |
| `ESC M`, `ESC P` | Elite, pica, in draft | cancel compressed, proportional and NLQ |
| `ESC N` n, `ESC O` | Skip n lines over the perforation; cancel | |
| `ESC Q` n, `ESC l` n | Right, left margin in columns | clear the line buffer |
| `ESC R` n | International set 0-10 | |
| `ESC S` n, `ESC T` | Superscript (0), subscript (1); cancel | draft only, two passes |
| `ESC U` n, `ESC s` n | Unidirectional; half speed | |
| `ESC W` n | Double width on, off | not ended by LF or DC4; `ESC W 0` also ends SO's |
| `ESC a` n | Align left, centre, right, or justify (0-3) | when the line ends; a line ending with "." is not justified |
| `ESC e 0` n, `ESC e 1` n | Horizontal stops every n columns; vertical every n lines | |
| `ESC f 0` n, `ESC f 1` n | Skip n spaces; feed n lines without returning | |
| `ESC n`, `ESC o` | NLQ in pica, in elite | Panasonic's |
| `ESC p` n | Proportional on, off | ignored in elite and Comp.; draft proportional prints emphasized |
| `ESC w` n | Pitch 0 10, 1 12, 2 15, 3 17 cpi | Panasonic's; Epson's `ESC w` is double height |
| `ESC x` n | NLQ (1) or draft (0), keeping the pitch | Epson's |
| `ESC y` c d1...d9, `ESC z` c | Define, release a download character | below |

Not in M: `ESC $`, `ESC \`, `ESC &`, `ESC %`, `ESC :`, `ESC j`, `ESC SP`,
`ESC t`, `ESC I`, `ESC i`, `ESC k`, `ESC b`, `ESC /`, `ESC m` and BEL.

The KX-P1080i adds `ESC m` n (0 Standard, 1 Matrix, 2 Graphics I, 3
Graphics II, kept through `ESC @`) and, in IBM mode, `ESC :` (elite,
cancelled by DC2), `ESC Q 3` (deselect), `ESC 6` and `ESC 7` (IBM
graphics sets II and I) and `ESC 2` bringing in `ESC A`'s spacing; in the
Graphics modes DEL and `ESC R` do nothing (I 4-18, 4-76).

## Mixing print modes (M 4-69, M Table 4.4)

- The pitches exclude one another but may change along a line.
- Compressed by SI and emphasized: emphasized prints, compressed returning
  when it ends. 17 cpi by `ESC w 3` instead makes emphasized ineffective.
  Semi-compressed and emphasized: whichever came last.
- Elite and compressed: elite; SI in elite is ignored.
- Proportional: ignored in elite; draft proportional prints emphasized.
- NLQ: two passes, so double strike does nothing, and scripts are draft
  only. Italic, underline, double width and emphasized all print in NLQ.
- Superscript and subscript exclude each other; double strike does nothing
  to them.

## Character sets (M Appendix A, M 4-18, M 4-19)

- 32-126 ASCII; 127 DEL; 128-159 controls (or italic international
  characters after `ESC 6`); 160-254 italic copies of 32-126; 255 DEL (or an
  italic slashed zero after `ESC 6`). `ESC 4` prints 32-126 from the italics.
- The 32 international characters are the Epson FX's, in its order: à è ù
  ò ì ° £ ¡ ¿ Ñ ñ ¤ Pt Å å ç § ß Æ æ Ø ø ¨ Ä Ö Ü ä ö ü É é ¥.
- `ESC R` 0-10 replaces `` # $ @ [ \ ] ^ ` { | } ~ `` as the FX-80's sets
  do, with the FX-80's numbering: USA, France, Germany, England, Denmark I,
  Sweden, Italy, Spain, Japan, Norway, Denmark II. Papyrium's
  `CharacterSet` already has them all.
- The KX-P1080i adds IBM character sets for its IBM mode (I Appendix A).

## Proportional widths (M Table 4.5, I Table 4.5)

In 1/120 inch, the same in draft and NLQ. Codes 0-31 here are the 32
international characters (printed upright by `ESC R`, italic at 128-159
under `ESC 6`); the italic column gives codes 160-254, and for 0-31 the
italic international characters. Both manuals' tables were transcribed
from their images independently and agree, except that M prints the
italic semicolon as 9 and I as 7, and only I gives 127, a slashed zero.
Both print "w" as 13, wider than the 12-column pica cell.

| Code | Char | Upright | Italic | Code | Char | Upright | Italic | Code | Char | Upright | Italic | Code | Char | Upright | Italic |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | à | 12 | 11 | 32 | space | 12 | 12 | 64 | @ | 12 | 12 | 96 | `` ` `` | 5 | 5 |
| 1 | è | 12 | 11 | 33 | ! | 5 | 10 | 65 | A | 12 | 12 | 97 | a | 12 | 11 |
| 2 | ù | 11 | 11 | 34 | " | 8 | 10 | 66 | B | 12 | 12 | 98 | b | 11 | 11 |
| 3 | ò | 10 | 11 | 35 | # | 12 | 12 | 67 | C | 12 | 12 | 99 | c | 11 | 11 |
| 4 | ì | 8 | 8 | 36 | $ | 12 | 11 | 68 | D | 12 | 12 | 100 | d | 11 | 12 |
| 5 | ° | 8 | 8 | 37 | % | 12 | 12 | 69 | E | 12 | 12 | 101 | e | 12 | 11 |
| 6 | £ | 12 | 12 | 38 | & | 12 | 12 | 70 | F | 12 | 12 | 102 | f | 10 | 12 |
| 7 | ¡ | 5 | 10 | 39 | ' | 5 | 6 | 71 | G | 12 | 12 | 103 | g | 11 | 11 |
| 8 | ¿ | 12 | 11 | 40 | ( | 7 | 8 | 72 | H | 12 | 12 | 104 | h | 11 | 11 |
| 9 | Ñ | 12 | 12 | 41 | ) | 7 | 8 | 73 | I | 8 | 10 | 105 | i | 8 | 9 |
| 10 | ñ | 11 | 12 | 42 | * | 12 | 12 | 74 | J | 11 | 12 | 106 | j | 9 | 10 |
| 11 | ¤ | 12 | 12 | 43 | + | 12 | 12 | 75 | K | 12 | 12 | 107 | k | 10 | 11 |
| 12 | Pt | 12 | 12 | 44 | , | 6 | 7 | 76 | L | 12 | 10 | 108 | l | 8 | 9 |
| 13 | Å | 12 | 12 | 45 | - | 12 | 12 | 77 | M | 12 | 12 | 109 | m | 12 | 11 |
| 14 | å | 12 | 11 | 46 | . | 6 | 7 | 78 | N | 12 | 12 | 110 | n | 11 | 10 |
| 15 | ç | 11 | 11 | 47 | / | 10 | 10 | 79 | O | 12 | 12 | 111 | o | 12 | 11 |
| 16 | § | 10 | 12 | 48 | 0 | 12 | 12 | 80 | P | 12 | 12 | 112 | p | 11 | 11 |
| 17 | ß | 11 | 11 | 49 | 1 | 12 | 12 | 81 | Q | 12 | 12 | 113 | q | 11 | 11 |
| 18 | Æ | 12 | 12 | 50 | 2 | 12 | 12 | 82 | R | 12 | 12 | 114 | r | 11 | 10 |
| 19 | æ | 12 | 12 | 51 | 3 | 12 | 12 | 83 | S | 12 | 12 | 115 | s | 12 | 11 |
| 20 | Ø | 12 | 12 | 52 | 4 | 12 | 12 | 84 | T | 12 | 12 | 116 | t | 11 | 10 |
| 21 | ø | 12 | 11 | 53 | 5 | 12 | 12 | 85 | U | 12 | 12 | 117 | u | 12 | 11 |
| 22 | ¨ | 8 | 9 | 54 | 6 | 12 | 12 | 86 | V | 12 | 12 | 118 | v | 12 | 10 |
| 23 | Ä | 12 | 12 | 55 | 7 | 12 | 12 | 87 | W | 12 | 12 | 119 | w | 13 | 13 |
| 24 | Ö | 12 | 12 | 56 | 8 | 12 | 12 | 88 | X | 10 | 12 | 120 | x | 10 | 12 |
| 25 | Ü | 12 | 12 | 57 | 9 | 12 | 12 | 89 | Y | 12 | 12 | 121 | y | 12 | 12 |
| 26 | ä | 12 | 11 | 58 | : | 6 | 7 | 90 | Z | 10 | 12 | 122 | z | 10 | 12 |
| 27 | ö | 10 | 11 | 59 | ; | 6 | 7 | 91 | [ | 8 | 11 | 123 | { | 9 | 10 |
| 28 | ü | 11 | 12 | 60 | < | 10 | 10 | 92 | \ | 10 | 7 | 124 | \| | 5 | 9 |
| 29 | É | 12 | 12 | 61 | = | 12 | 11 | 93 | ] | 8 | 11 | 125 | } | 9 | 10 |
| 30 | é | 12 | 11 | 62 | > | 10 | 9 | 94 | ^ | 12 | 10 | 126 | ~ | 12 | 12 |
| 31 | ¥ | 12 | 12 | 63 | ? | 12 | 11 | 95 | _ | 12 | 12 | 127 | slashed 0 | 12 | 12 |

## Download characters (M 4-64, M 4-65)

Not Epson's: `ESC y` c and exactly nine column bytes define the character
at code c, bit 7 the top of the eight rows used; `ESC z` c gives back the
ROM's character. There is no attribute byte and no selection command: a
download replaces the character at its code, up to 40 at once, at codes
32-126 and 128-255 (32-126 with 7-bit data). The character is nine columns
and three of space, and a dot following one in its row is not printed.
Nothing says how downloads print in NLQ, italic or proportional spacing,
or which eight of the nine pins they use.

## Firmware

The KX-P1080U's EPROM, as far as read so far. Rob decided (2026-11-10)
that anything in it may be used, its characters included.

- **CPU.** IC2, a Matsushita MN1276 in a 64-pin shrink DIP: a µPD7811
  equivalent with Panasonic's own mask ROM, of the NEC µPD7810 family.
  MAME's `unidasm` (architecture `upd7810`) disassembles it cleanly, with
  the family's CALL (0x44), JMP (0x54), RET (0xB8) and its internal RAM at
  0xFF00-0xFFFF. The EPROM is IC3, an NEC D27128D labelled `PJWIXP1080U`,
  `IC3 U160B`, `61201`.
- **Memory map.** Call targets fall into 0x2000-0x3FFF and 0x4000-0x4FFF
  and land on subroutine entries there, either way taking the address
  modulo 0x4000 as the file offset; calls into 0x0000-0x1FFF never do,
  being data read as code. So the EPROM answers at 0x0000-0x3FFF and again
  at 0x4000-0x7FFF, and its first 4 KB is reached only through the second
  copy: the CPU's 4 KB internal mask ROM occupies 0x0000-0x0FFF.
- **The internal ROM** (how it was recovered: `docs/panasonic-kx-p1080-rom-recovery.md`) was read out (2026-11-10) by an EPROM patched with
  `tools/kx-p1080-rom/dump_patch.py`, whose self test prints it as a hex
  dump with a checksum on each line, and transcribed from a 300 dpi scan
  of the printout: by template matching on the fixed character grid,
  trained on the line addresses, each line kept only if its checksum
  held, and every cell confirmed by a nearest-neighbour vote from the
  other lines; 35 lines the matcher could not read were read by eye. The
  scan holds 255 of the 256 lines, the printer having stopped after
  0x0FE0 for a reason not found; 0x0FF0-0x0FFF is taken to be 0xFF like
  the 64 bytes before it (Rob's decision, 2026-11-10), since nothing
  traced reads it: the EPROM's code names no address in 0x0D00-0x0FFF,
  and the draft path's last base, `$0BB8`, ends at 0x0DAF. The image and its transcript are
  `KX-P1080U-internal.bin` (SHA-1 `06cf7011e56efb96d840ff4862cb7888d9dc5ba4`
  with that assumption) and `KX-P1080U-internal.txt` beside the EPROM in
  `docs/local/panasonic-kx-p1080/`. It holds:
  - Reset, at 0x0000: `DI`, a jump over the vectors to 0x0063, `V` set
    to 0xFF in both register banks, 0x0F into the memory mapping register
    `MM`, then `JMP $2000`, the first of the EPROM's jumps. The interrupt
    vectors at 0x0004, 0x0008, 0x0010, 0x0018 and 0x0028 and the software
    interrupt's at 0x0060 jump to the rest of that table (`$2003`, `$2006`,
    `$2009`, `$200C`, `$200F`, `$2012`). The rest of the internal ROM looks
    like data, not code.
  - 0x0080-0x00BF: the CALT table, every entry an address in the EPROM's
    jump table (0x2015 on).
  - 0x00C0-0x053F: the draft characters, codes 0-127, nine column bytes
    each; 0x0540-0x09BF the draft italics; 0x09C0 and 0x0BB8 the IBM PC
    characters' draft forms, 56 each, in code page 437's order from
    0x80 (Ç ü é â ä à å ç ê ë è ï ...), the second set apparently their
    italics. `$4302` copies a character's nine bytes to the column buffer
    unchanged, and `$46CE` turns each into pins as it prints: with
    `VV:C4` 0, as for draft, a byte with bit 0 clear fires pins 1-8 from
    bits 7-0, and one with bit 0 set is lowered two pins, bits 7-1 firing
    pins 3-9. The lowering is column by column: g, p, q and y lower every
    column, j only its hook, ç only its cedilla. (`VV:C4` 1 lowers every
    column one pin, bit 0 firing pin 9, as NLQ does for its descenders;
    2 lowers two; 3 none.) Codes 0-31 are the international characters
    (à è ù ò ì ° £ ¡ ¿ Ñ ñ ¤ ₧ Å å ç § ß Æ æ Ø ø ¨ Ä Ö Ü ä ö ü É é ¥), in
    the Epson FX's order, and 127 the slashed zero. Draft is a half-dot
    design, dots mostly in alternate columns; 13 characters have a dot in
    two adjacent columns, which the head cannot fire twice so soon.
  - 0x0DB0-0x0FAF: further tables not yet traced (bytes 0x0A, 0x05,
    0xAA, 0x55: shading patterns, perhaps); 0x0FB0-0x0FFF unused (0xFF).
- **National sets** at 0x286E: twelve bytes for each of eleven sets, in
  `ESC R`'s order, each giving the character location for `` # $ @ [ \ ] ^
  ` { | } ~ ``, the international characters being locations 0-31 in the
  Epson FX's order. They match M's table exactly.
- **NLQ characters** (`$44DE` on; `tools/kx-p1080-rom/kx-p1080-map.txt`
  names the routines). An index at `$4B00` (ROM 0x0B00) has four bytes
  for each code 0-127: the column the character starts at, its byte
  count, and a 12-bit offset from `$4B00` to its data, with a kind in bits
  4-6 of the last byte and a descender in bit 7. Codes 0-31 are the 32
  international characters and 127 a slashed zero. The data, in
  0x0D00-0x1BFF, is the character's two passes one after the other, bit 7
  the top pin, on a grid of 1/240 inch columns. Built into a 24-column
  buffer (`$FFA8`), each column loses any dot the column before fired; in
  kinds 1, 3 and 5 a byte with bit 0 set spreads over two columns, the
  first firing what it can and the second the dots it could not (`$45CA`);
  kinds 2-5 are half a character, completed by copying the columns back
  out in reverse from one or two before the end (`$45E7`). The first pass
  prints the even rows and the second the odd rows, 1/144 inch apart: a
  serifed face 16 rows high, as the manual's NLQ samples show. A
  character with the descender bit prints a pin lower (`VV:C4` 1,
  `$4501`).
- **Draft characters are in the internal ROM**, not the EPROM. The draft path (`$4302`)
  copies nine column bytes for the character from a base chosen by the
  attribute byte (`$4348`): `$00C0` upright, `$0540` italic, `$09C0` and
  `$0BB8` the IBM PC characters. Those addresses are in the CPU's own 4 KB
  at 0x0000-0x0FFF, which they fill from just after its CALT table
  (0x0080-0x00BF): 128 characters of nine bytes upright, as many italic,
  and 56 and 56 more (above). Download characters
  are nine bytes each in RAM at `$819D` (`$43DA`).
- **NLQ italics** are not stored: `$4534` slants the built columns,
  taking each column's pins from it and the three columns before it, two
  pins from each, the top two from furthest left, so that each pair of a
  pass's pins leans one 1/240 inch column further right than the pair
  below (the LC-10 moves each pin a column, not each pair). Pins slanted
  past the 24th column are lost. Draft italics are stored, in the CPU.
- **IBM PC characters.** With bits 2-3 of the character's attribute byte
  set, the NLQ index is taken from `$56C8` instead: 41 of code page 437's
  characters that Epson's international set lacks, ç ê ë ï î ô û ÿ ¢ ƒ á
  í ó ú, ½ ¼ « », α ß Γ π Σ σ µ τ Φ Θ Ω δ ∞ φ ε ∩ ≡ and others, in NLQ;
  their draft forms are in the CPU. No KX-P1080 manual mentions them and
  no command in this firmware selects them (there is no `ESC m`): the
  firmware evidently shares its character code with the KX-P1080i's IBM
  mode.
- **Proportional widths** are at `$5C00` (ROM 0x1C00, upright) and
  `$5C80` (italic), one byte a code 0-127, the width in 1/120 inch in the
  low nibble and another value, probably an offset, in the high one;
  `$5D70` and `$5DF0` repeat the widths with other high nibbles. The
  attribute byte's bits 3-5 choose among eight tables (`$43C6`), bit 5
  the italic one. `$2A13` makes a character's advance from them, doubled
  for double width. The ROM's widths are the manuals' but for seven: the
  comma is 7 (italic 8) where both manuals print 6 (7); "1" 9, not 12, in
  both; "w" 12, not 13, in both; and the italic "6" and "9" 11, ":" 8 and
  ";" 9 (as M has it; I prints 7). Papyrium follows the ROM.
- **Graphics.** `$369D` gives each `ESC *` density its column pitch in
  1/1440 inch, 24, 12, 12, 6, 18, 20 and 16 for 60, 120, 120, 240, 80,
  72 and 90 dpi, and its line-buffer attribute byte, 0xE0-0xE6.
- **The line buffer** (external RAM at `$8000`) holds the characters of
  the line, with two attribute bytes before any character whose modes
  differ from the last, the first marked by bit 7 (`$2A88` on); the
  printing side reads it forwards or backwards by the head's direction.
- **Escapes** are dispatched through a table at `$32FA` of a handler
  address for each command byte 0-127, `$3B7B` (ignore) for those the
  printer lacks. Its commands are exactly the KX-P1080 manual's: there is
  no `ESC m`, so this firmware has no IBM mode, whatever the IBM PC
  characters above are for. The map names every handler.
- **A table of 37 jumps at 0x2000**, which nothing in the EPROM jumps
  into: the EPROM's entry points, reached from the internal ROM's
  vectors and CALT table.
- 0x1F00-0x1FFF is unused (0xFF).

## Open questions

- Why the dump stopped after 0x0FE0, missing the last line and its
  second pass; a second printout would confirm the assumed 0xFF there.
- What 0x0DB0-0x0FAF of the internal ROM holds.
- What, if anything, reaches the IBM PC characters.
- How far commands change the print mode in the selector's NLQ and Comp.
  positions: M says they cannot, yet says `ESC !` works in every mode.
- Which pins download characters use, and how they print in NLQ.
- The self test's and hex dump's printed layout.
- Undefined escape sequences and the unlisted control codes.
- The `ESC l` range; graphics past the right margin.
- M says CAN clears the receive buffer, but its example shows only the
  line being dropped.

## For Papyrium

- The ESC/P interpreter and `EscpMechanism` cover most of this; what is
  new is `ESC w` as pitch (clashing with the LC-10's double height), the
  semi-compressed 15 cpi pitch, `ESC n` and `ESC o`, `ESC y` and `ESC z`
  downloads, `ESC !`'s narrower layout, the selector switch's three
  positions, the half-speed and emphasized-proportional rules, and the
  width table above.
- The KX-P1080i's IBM mode is three IBM printers, Matrix and Graphics I and
  II, none of them the Proprinter: a separate language or languages, built
  per the emulation rule from those printers' own documents.
