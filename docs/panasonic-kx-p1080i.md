# Panasonic KX-P1080i: notes from the operating instructions

The KX-P1080i manual restated in full, the groundwork for a KX-P1080i
model. `docs/panasonic-kx-p1080.md` draws on it for the family and records
what the KX-P1080U's firmware shows; this is what the i's manual says,
including its IBM mode, which the KX-P1080U lacks. Where the firmware has
since answered a question the manual leaves open, a note says so.

The KX-P1080U's firmware holds the characters the IBM mode prints, though
nothing in the U reaches them: the code page 437 characters in draft and
italic, 40 of them in NLQ, the box drawing and blocks (double-line pieces
printed single), the Matrix Printer's block graphics built from the code,
and their proportional widths (IBM PC characters, under Firmware, in
`docs/panasonic-kx-p1080.md`). It does not hold the IBM mode's commands:
its dispatch table has no `ESC m`, and none of the IBM-only behaviour
below.

Source: KX-P1080i Operating Instructions (Matsushita Electric of Canada), as
scanned by Manualslib, OCRed with Tesseract
(`docs/local/panasonic-kx-p1080/Panasonic_KX-P1080i_Manual.txt` and `-pages/`).
Everything below is restated in our own words. References are "printed page
(PDF page)", e.g. "4-35 (p50)".

**Checked against page images** (not just OCR): 1-3 (p11) specifications;
3-1 (p17) switches; 3-3 (p19) DIP tables; 4-2 (p23) notes; 4-19 (p34)
Table 4.2; 4-20 (p35) Table 4.3; 4-28 (p43) ESC ! bit table; 4-35 (p50)
Table 4.5 in full, cropped column by column; 4-36 (p51) Table 4.6; 4-40
(p58) Table 4.8; 4-50 (p68) Table 4.10; 4-52 (p70) ESC A range; 4-55 (p73)
ESC N; 4-60 (p78) ESC C 0; 4-63 (p81) ESC Q ranges; 4-70/4-71 (p91, p92)
download characters; 4-75 (p96) Table 4.11; A-1 to A-4 (p103 to p106)
character sets; E-1 (p113) paper and printing area. Everything else comes
from the OCR text, which was clean enough to read in prose passages.

**Page order in the scan.** Manualslib bound the pages out of order. Printed
4-1 to 4-3 are p22 to p24; 4-10 to 4-37 are p25 to p52; 4-4 to 4-6 are p53
to p55; 4-38 to 4-65 are p56 to p83; p84 is the List of Figures (front
matter); 4-7 to 4-9 are p85 to p87; 4-67 to 4-76 are p88 to p97.
**Printed page 4-66 (ESC > "MSB on") is missing from the scan.** Nothing
else in chapter 4 is missing.

---

## 1. Specifications (1-1 p9, 1-3 p11, 3-5 p21, 5-1 p98, E-1 p113)

| Item | Value |
|---|---|
| Print method | Impact dot matrix, 9-pin head; bidirectional, logic seeking (skips leading and trailing blanks and blank lines) |
| Dot diameter | 3/254 in (0.3 mm) |
| Draft (pica) matrix | 9 x 9 (H x V); dot pitch 1/120 in horizontal, 1/72 in vertical |
| NLQ matrix | 18 x 18; dot pitch 1/240 in horizontal, 1/144 in vertical (two head passes); the KX-P1080U's firmware puts the passes 1/216 in apart |
| Other qualities | None besides draft and NLQ (plus emphasised and double-strike variants of draft) |
| Character cell | Ordinary 0.078 in W x 0.095 in H; super/subscript 0.078 W x 0.053 H |
| Pitches | Pica 10 cpi (80 col), Elite 12 cpi (96), Semi-compressed 15 cpi (120), Compressed 17 cpi (137); elongated (double width) halves each: 5 (40), 6 (48), 7.5 (60), 8.5 (68); proportional spacing as a fifth pitch |
| Speed | Draft pica 120 cps, draft elite 120 cps, NLQ 24 cps; emphasised prints at half speed (60 cps at pica) (4-24 p39) |
| Direction | Text bidirectional (draft and NLQ); bit image left to right only |
| New line time | About 100 ms at 1/6 in |
| Line spacing | Default 1/6 in; 1/8, 7/72, n/72, n/216 by command |
| Paper | Fanfold 3 to 10 in wide (tractor); single sheet 4 to 9 in wide, 5 to 14.3 in long (friction); up to 3 parts, total under 0.25 mm |
| Printable width | 8 in (80 columns at pica, 137 at 17 cpi); tear-bar scale shows 0 to 80 (2-4 p15) |
| Printing area (E-1 p113) | B: 0.95 in from sprocket-hole centre to the left edge of the first character with the tractor fully left; C: first print line 3.85 in below the top edge of fanfold paper (as drawn); A: lines within 1 in either side of a perforation may slip; D: paper end detected 1.5 in from the bottom |
| First line | About 1/6 in from the top of the back tension plate (2-5 p16) |
| Buffer | 1 KB receive buffer (3-5 p21) |
| Interface | Centronics-style parallel, TTL, BUSY and ACK handshake, Amphenol 57-30360; optional RS-232C board (XON/XOFF, ETX/ACK, DTR) mentioned only in 1-1 |
| Head life | 100 million characters (draft) |
| Ribbon | KX-P110 cassette, black, about 3 million characters |
| Power | 120 V 60 Hz (this is the North American/Canadian edition) |

Parallel interface (5-1 to 5-3, p98 to p100): pin 1 STROBE (low at least
0.5 us), 2-9 DATA1-8, 10 ACK, 11 BUSY, 12 PE, 13 SLCT, 14 AUTO FEED XT
(input), 16 SG, 17 FG, 18 +5 V, 19-30 returns, 31 PRIME (input, low
resets), 32 ERROR, 33 SG. BUSY high when buffer full, processing, off
line or in error. ERROR low on paper end, off line, overload. SLCT high
on line. The AFXT pin low gives CR+LF; DIP SW3 on forces CR+LF whatever
the pin. Timing (Fig 5.2): data setup and hold 0.5 us minimum, STROBE
1 us minimum, ACK about 5 us, BUSY time 1 ms or less when the buffer is
not full.

## 2. Controls and indicators (1-2 p10, 3-1 p17, 3-5 p21)

- **Power switch** on the right side at the rear; POWER lamp.
- **ON LINE switch** (green, alternate action) and ON LINE lamp. Powers up on
  line if paper is loaded, off line if not. Going on line sends an ACK pulse.
- **FF switch**: works on line and off line; advances to the next top of
  form, and that becomes the new top of form.
- **LF switch**: works on line and off line; one line per press, repeats
  while held.
- **PAPER/ERROR lamp**: lit with less than 1.5 in of paper left or none;
  blinks on head overload (blocked carriage). Overload takes the printer off
  line, disables the panel switches, and needs a power cycle.
- **Print mode selector** (top left; three positions, labelled "Std. Pgm.",
  "NLQ", "Comp."). Takes effect on line or off line.
  - **Std. Pgm.**: draft, 120 cps bidirectional; the only position in which
    software can change the print mode (pitch and quality).
  - **NLQ**: near letter quality, two passes; software cannot change to any
    other mode.
  - **Comp.**: compressed, 137 columns, so 15-inch layouts fit 8.5-inch
    paper; software cannot change to any other mode.
  - Command-level detail: ESC P and ESC M work only at Std. Pgm. (4-11, 4-12);
    ESC : does not work at Comp. (4-13); DC2 does not release compression at
    Comp. (4-5); ESC E is not available at Comp. (4-24); ESC p is ineffective
    at Comp. (4-34). Nothing says the switch blocks ESC x, ESC n, ESC w at
    NLQ; the general rule above says it does.
- **Paper feed selector**: FRICTION or TRACTOR (TRACTOR also releases the
  pinch rollers for aligning a single sheet). Head gap lever.
- **Power-on button functions**: LF held = self test; LF and FF held = hex
  dump (see section 4). No others are described.
- **Paper-out** (3-2 p18): stops accepting data, goes off line, LF and FF
  still work, PE high; reload and press ON LINE to resume. Transparent paper
  is not detected.

Top of form: the line counter is reset at power on and the current line is
line one (2-5 p16).

## 3. DIP switches (3-2 to 3-4 p18 to p20, B-1 p108, 4-76 p97; images checked)

Eight switches, read at power on into a RAM image which commands can
override ("the control command always overrides the switch").

| SW | Function | ON | OFF | Factory |
|---|---|---|---|---|
| 1 | Printer mode | Standard mode | IBM printer mode | ON |
| 2 | Paper-out detector | Ineffective (can print to the end; on single sheets prints in the last 1.5 in) | Effective (stops at paper out) | OFF |
| 3 | AUTO FEED XT | Fixed internally (LF added to every CR) | Not fixed (CR only, unless the AFXT pin is low) | OFF |
| 4 | Skip perforation | 1-inch skip | No skip | OFF |
| 5, 6, 7 | Character set / IBM mode | SW1 ON: international set; SW1 OFF: IBM mode | | ON, ON, ON |
| 8 | Data bits | 7-bit | 8-bit | OFF |

**International set, SW1 ON** (Table 3.2):

| SW5 | SW6 | SW7 | Set |
|---|---|---|---|
| ON | ON | ON | USA (0) |
| OFF | ON | ON | France (1) |
| ON | OFF | ON | Germany (2) |
| OFF | OFF | ON | England (3) |
| ON | ON | OFF | Denmark I (4) |
| OFF | ON | OFF | Sweden (5) |
| ON | OFF | OFF | Italy (6) |
| OFF | OFF | OFF | Spain (7) |

Japan (8), Norway (9), Denmark II (10) only by ESC R.

**IBM mode, SW1 OFF** (Table 3.3; "-" = either):

| SW5 | SW6 | SW7 | Mode |
|---|---|---|---|
| OFF | OFF | OFF | IBM Graphics Printer mode II |
| - | - | ON | IBM Graphics Printer mode II |
| - | ON | OFF | IBM Graphics Printer mode I |
| ON | OFF | OFF | IBM Matrix Printer mode |

So the emulation switch is SW1, and SW5-7 choose which IBM personality.
Character complements per mode (3-3 p19, image): Standard = 96 ASCII + 32
international; IBM Matrix = 96 ASCII + 64 block graphics + 32
international; IBM Graphics I = 96 ASCII + 95 special; IBM Graphics II =
96 ASCII + 132 special. (OCR read the Graphics I figure as 96; the image
says 95.)

Software equivalents (Table 4.12, 4-76 p97): ESC R 0-7 for SW5-7 (Standard);
ESC m 0-3 for SW1/5-7 mode; ESC 8 / ESC 9 for SW2; ESC N 6 / ESC O for SW4
(the table writes "ESC N 6" for the 1-inch skip, i.e. 6 lines at 1/6 in);
ESC = / ESC # for SW8 (7-bit / 8-bit). SW3 has no command; send LF.

## 4. Self test and hex dump (3-5 p21)

- **Self test**: hold LF while switching on. Prints all 96 ASCII
  characters continuously across the full platen width until power off.
  (The manual does not describe the pattern further: no rolling offset,
  mode or quality stated.)
- **Hex dump**: hold LF and FF while switching on. Everything received is
  printed as hex; control codes (CR, LF, HT, ...) are not obeyed. Leave by
  switching off. Layout (bytes per line, ASCII column) not described.

## 5. Control codes and escape sequences

Argument convention: for on/off commands the manual lists n = 1, 49, 129,
177 for on and 0, 48, 128, 176 for off, i.e. binary or ASCII digit, with or
without bit 7. Applies to ESC W, ESC S, ESC -, ESC x, ESC p, ESC s, ESC U,
ESC a (0-3 and 48-51, 128-131, 176-179), ESC w (0-3 likewise).

### 5.1 Single-byte codes (4-3 to 4-9; the manual lists exactly 16)

| Code | Dec / hex | Effect | Page |
|---|---|---|---|
| NUL | 0 / 00 | Terminator of ESC D and ESC B lists; no other function stated | 4-7 (p85) |
| BS | 8 / 08 | Prints the buffer, then moves back one character width of the current mode. Ineffective in auto-justify mode | 4-3 (p24) |
| HT | 9 / 09 | Next horizontal tab. Ignored if the tab is left of the current position. If the tab lies beyond the printable width, prints what fits and does one line feed. Skipped space is not underlined. Tabs every 8 columns at power on | 4-7 (p85) |
| LF | 10 / 0A | Prints the buffer, feeds one line at the current spacing; cancels SO/ESC SO double width; landing in the skip-perforation zone goes to the next top of form. Blank or space-only lines just feed | 4-7 (p85) |
| VT | 11 / 0B | Next vertical tab. With tabs set but none below the current line: acts as FF. With no tabs set: acts as LF. Cancels one-line double width | 4-9 (p87) |
| FF | 12 / 0C | Prints the buffer, feeds to the next top of form (per page length); cancels one-line double width | 4-6 (p55) |
| CR | 13 / 0D | Prints the buffer and returns (overprinting is possible: the example overprints "0000" with "////"). Adds LF when SW3 is ON or AFXT is low | 4-4 (p53) |
| SO | 14 / 0E | One-line double width. Cancelled by LF, FF, VT, ESC W 0, DC4, initialisation. Not cancelled by ESC J or ESC f 1 | 4-9 (p87) |
| SI | 15 / 0F | Compressed (17 cpi). Ignored in elite or proportional mode. Emphasised beats it (it comes back when emphasis ends) | 4-8 (p86) |
| DC1 | 17 / 11 | Reselects after DC3 (or ESC Q 3); the manual adds that print-buffer data received before is lost | 4-5 (p54) |
| DC2 | 18 / 12 | Cancels SI compression (back to pica); not at the Comp. switch position. In IBM mode also cancels ESC : elite | 4-5 (p54) |
| DC3 | 19 / 13 | Deselects: everything received until DC1 is discarded | 4-5 (p54) |
| DC4 | 20 / 14 | Cancels SO / ESC SO double width (not ESC W 1) | 4-6 (p55) |
| CAN | 24 / 18 | Clears the line (the example shows the text before CAN vanishing). The heading says "receive buffer" | 4-4 (p53) |
| ESC | 27 / 1B | Escape prefix | 4-6 (p55) |
| DEL | 127 / 7F | Deletes the last text character in the buffer (not bit image, tab space or mode changes). Ineffective in auto-justify mode. **Absent in the IBM Graphics modes** | 4-4 (p53) |

No BEL is listed anywhere (manual, appendix A, Appendix D). Character-set
charts show 0x80-0x9F as the same control codes as 0x00-0x1F (BS, HT, LF,
VT, FF, CR, SO, SI, DC1-DC4, CAN, ESC at their +0x80 positions) in every
mode, and 0xFF as DEL in Standard mode (A-1 to A-4).

### 5.2 Escape sequences (Standard mode unless noted)

Pitch and size

| Bytes | Dec | Effect | Notes | Page |
|---|---|---|---|---|
| ESC P | 27 80 | Pica 10 cpi, draft font | Cancels NLQ. The page does not say whether it cancels SI compression or proportional mode (it only says other commands change pitch away from pica). Only at Std. Pgm. | 4-11 (p26) |
| ESC M | 27 77 | Elite 12 cpi, draft font | Cancels compressed and proportional; compressed is ignored while elite. Cancels NLQ. Only at Std. Pgm. | 4-12 (p27) |
| ESC : | 27 58 | Elite 12 cpi (IBM mode only) | Does not change draft/NLQ font; not at Comp.; not in Standard mode; DC2 cancels | 4-13 (p28) |
| ESC w n | 27 119 n | Pitch: 0 = 10, 1 = 12, 2 = 15, 3 = 17 cpi (also 48-51, 128-131, 176-179) | Overrides ESC P, ESC M, SI etc.; keeps the font (draft or NLQ); at 17 cpi emphasis is ineffective. The only way to 15 cpi | 4-32 (p47) |
| ESC W n | 27 87 n | Double width on (1) / off (0) | ESC W 1 survives LF and DC4; ESC W 0 also cancels SO | 4-14 (p29) |
| ESC SO | 27 14 | Same as SO | | 4-15 (p30) |
| ESC SI | 27 15 | Same as SI | | 4-15 (p30) |
| ESC S n | 27 83 n | 0 = superscript, 1 = subscript | Half height, normal width; not in NLQ; printed as two unidirectional passes 1/216 in apart, line count compensated | 4-16, 4-17 (p31, p32) |
| ESC T | 27 84 | Cancel super/subscript | | 4-16 |
| ESC p n | 27 112 n | Proportional on (1) / off (0) | Draft proportional prints emphasised; draft and NLQ share widths; ineffective in elite and at Comp. | 4-34 (p49) |

Fonts and emphasis

| Bytes | Dec | Effect | Notes | Page |
|---|---|---|---|---|
| ESC 4 | 27 52 | Italic on | Draft and NLQ. Italic glyphs are those of 0xA0-0xFE substituted for 0x20-0x7E | 4-18 (p33) |
| ESC 5 | 27 53 | Italic off | | 4-18 |
| ESC 6 | 27 54 | Standard: put italic international characters at 128-159 and 255 | Standard mode only | 4-19 (p34) |
| ESC 7 | 27 55 | Standard: cancel ESC 6 | | 4-19 |
| ESC R n | 27 82 n | International set 0-10 | Not in IBM Graphics modes (always USA there) | 4-20 (p35) |
| ESC E | 27 69 | Emphasised on | Half speed; beats compressed (compression resumes when emphasis ends); pica, elite, NLQ; not at Comp. | 4-24 (p39) |
| ESC F | 27 70 | Emphasised off | | 4-24 |
| ESC G | 27 71 | Double strike on: two passes, paper fed 1/216 in between | No effect in NLQ or super/subscript; pica, elite, compressed | 4-25 (p40) |
| ESC H | 27 72 | Double strike off | | 4-25 |
| ESC - n | 27 45 n | Underline on (1) / off (0) | Continuous; uses pin 9; not under bit image, HT space, IBM block graphics, IBM "12-dot special characters"; descenders touch it; ESC f 0 spaces are underlined | 4-26 (p41) |
| ESC ! n | 27 33 n | Mode byte, 0-63 | See bit table below; works in draft and NLQ | 4-27, 4-28 (p42, p43) |
| ESC n | 27 110 | NLQ at pica | Super/subscript and ESC G ineffective in NLQ | 4-30 (p45) |
| ESC o | 27 111 | NLQ at elite | | 4-31 (p46) |
| ESC x n | 27 120 n | 1 = NLQ font, 0 = draft font | Keeps the current pitch (example: draft compressed stays compressed) | 4-33 (p48) |

ESC ! bits (image of 4-28 checked; **not the Epson layout**):

| Bit | 1 means | 0 means |
|---|---|---|
| 0 | Elite | Pica |
| 1 | no meaning | |
| 2 | Compressed | normal |
| 3 | Emphasised | normal |
| 4 | Double strike | normal |
| 5 | Double width | normal |
| 6, 7 | must be 0 | |

Emphasised beats compressed when both are set. Table 4.4 (4-29 p44) only
tabulates these bits for n = 0-63. No proportional, italic or underline
bits.

Graphics

| Bytes | Dec | Effect | Page |
|---|---|---|---|
| ESC K n1 n2 | 27 75 | 60 dpi (480 dots/line), 12 in/s | 4-44 (p62) |
| ESC L n1 n2 | 27 76 | 120 dpi (960), 6 in/s | 4-44 |
| ESC Y n1 n2 | 27 89 | 120 dpi double speed (960), 12 in/s, no adjacent dots | 4-45 (p63) |
| ESC Z n1 n2 | 27 90 | 240 dpi (1920), 6 in/s, no adjacent dots | 4-45 |
| ESC * m n1 n2 | 27 42 | 8-pin, mode m 0-6 | 4-46 (p64) |
| ESC ^ m n1 n2 | 27 94 | 9-pin, mode m 0-6, two bytes per column | 4-48 (p66) |
| ESC ? c m | 27 63 c m | Reassign K/L/Y/Z (c = 75, 76, 89, 90) to mode m 0-6 | 4-49 (p67) |

Line spacing and paper feed

| Bytes | Dec | Effect | Notes | Page |
|---|---|---|---|---|
| ESC 0 | 27 48 | 1/8 in | All modes | 4-50 (p68) |
| ESC 1 | 27 49 | 7/72 in | All modes | 4-51 (p69) |
| ESC 2 | 27 50 | Standard: 1/6 in. IBM: apply the ESC A value | IBM default 1/6 | 4-51 |
| ESC A n | 27 65 n | n/72 in, 0 <= n <= 85 | In IBM modes only takes effect after ESC 2 | 4-52 (p70) |
| ESC 3 n | 27 51 n | n/216 in, 0-255 | All modes | 4-53 (p71) |
| ESC J n | 27 74 n | Print buffer and feed n/216 in once, 0-255 | No carriage return: printing continues where it left off; does not cancel one-line double width | 4-54 (p72) |
| ESC N n | 27 78 n | Skip n lines over the perforation, 1-127 (n >= 128 taken as n-128) | Fixed in length once set; cancelled by page-length commands | 4-55 (p73) |
| ESC O | 27 79 | Cancel skip-over-perforation | | 4-55 |

Page format

| Bytes | Dec | Effect | Notes | Page |
|---|---|---|---|---|
| ESC D n1 ... nk 0 | 27 68 | Horizontal tabs, ascending, up to 32 | Counted from the left margin (column 0); fixed in place when pitch changes; in proportional mode set in pica units; move with the left margin | 4-56 (p74) |
| ESC D 0 | 27 68 0 | Clear horizontal tabs | | 4-56 |
| ESC e 0 n | 27 101 0 n | Tab every n columns from the left margin | n = 0 cancels; default every 8 | 4-57 (p75) |
| ESC B n1 ... nk 0 | 27 66 | Vertical tabs, ascending, up to 16, from top of form | Fixed when line spacing changes; cleared by page-length commands | 4-58 (p76) |
| ESC B 0 | 27 66 0 | Clear vertical tabs | | 4-58 |
| ESC e 1 n | 27 101 1 n | Vertical tab every n lines from top of form | n = 1 cancels; n beyond the form length ignored; n = 0 prints without feeding; cleared by page-length commands | 4-59 (p77) |
| ESC C 0 n | 27 67 0 n | Page length n inches, 1-22 | n = 0 or >= 23 ignored; current line becomes top of form; clears VT and skip | 4-60 (p78) |
| ESC C n | 27 67 n | Page length n lines, 1-127 (>= 128 taken as n-128) | n = 0 "returns to the inch designation"; current line becomes top of form; clears VT and skip | 4-61 (p79) |
| ESC l n | 27 108 n | Left margin at column n | Ignored if beyond the right margin; clears the print buffer; set in pica in proportional mode; stays put when pitch changes | 4-62 (p80) |
| ESC Q n | 27 81 n | Right margin (Standard mode only) | Ranges: pica 2-80, compressed 4-137, elongated 1-40, elongated compressed 2-68; left of the left margin ignored; clears the buffer; pica in proportional | 4-63 (p81) |
| ESC f 0 n | 27 102 0 n | Skip n character spaces, 0-127 (>= 128 taken as n-128) | Current pitch; underlined in underline mode; excess past the right margin ignored | 4-64 (p82) |
| ESC f 1 n | 27 102 1 n | Print, then feed n lines, 0-127 (>= 128 taken as n-128) | No carriage return: next print starts in the next column; does not cancel double width | 4-65 (p83) |

Word processing (4-37 to 4-39, p52, p56, p57)

| Bytes | Dec | Effect |
|---|---|---|
| ESC a 0 | 27 97 0 | Left alignment (default) |
| ESC a 1 | 27 97 1 | Centre between margins |
| ESC a 2 | 27 97 2 | Right alignment |
| ESC a 3 | 27 97 3 | Full justification: applied when text overruns the right margin or on CR, LF, FF; not applied to a line ending in "."; BS and DEL ineffective; very short or long lines may not justify |

Works in draft and NLQ, all modes. The examples need ESC Q, so they run only
in Standard mode (IBM modes have no ESC Q margin).

Data control, downloads, miscellaneous

| Bytes | Dec | Effect | Page |
|---|---|---|---|
| ESC > | 27 62 | Force bit 7 to 1 ("MSB on"); page missing from scan | 4-66 (missing) |
| ESC = | 27 61 | Force bit 7 to 0; no effect on bit image data | 4-67 (p88) |
| ESC # | 27 35 | Take bit 7 as received | 4-68 (p89) |
| ESC Q 3 | 27 81 3 | Deselect (IBM mode only; Standard mode uses ESC Q as right margin); DC1 reselects | 4-69 (p90) |
| ESC y c D1..D9 | 27 121 c + 9 bytes | Define download character at code c | 4-71 (p92) |
| ESC z c | 27 122 c | Release download at c (original character returns) | 4-71 |
| ESC < | 27 60 | Return head home (left) | 4-72 (p93) |
| ESC @ | 27 64 | Initialise; clears print buffer, not the receive buffer | 4-72 |
| ESC s n | 27 115 n | Half speed on (1) / off (0); only pica, elite, 60 dpi, double-speed 120 dpi and 72 dpi graphics | 4-73 (p94) |
| ESC U n | 27 85 n | Unidirectional on (1) / off (0) | 4-73 |
| ESC 9 | 27 57 | Paper-end detector on (stops 1.5 in from the bottom, PE status) | 4-74 (p95) |
| ESC 8 | 27 56 | Paper-end detector off (PE held low) | 4-74 |
| ESC m n | 27 109 n | Printer mode: 0 Standard, 1 IBM Matrix, 2 IBM Graphics I, 3 IBM Graphics II; **not reset by ESC @** | 4-23 (p38) |

Unknown or unsupported sequences: the manual never says what happens.
FX-80 commands absent from the manual: BEL, ESC SP, ESC $, ESC \, ESC j,
ESC k, ESC i, ESC %, ESC &, ESC / and ESC b (and ESC : is used for IBM elite,
not Epson's ROM copy). ESC 6/7 keep the Epson meaning only loosely: here
they map the italic international characters into 0x80-0x9F rather than
enabling printable upper control codes.
Download uses ESC y / ESC z instead of Epson's ESC & / ESC %. ESC e and
ESC f are the Star Gemini-style tab-unit and skip commands; ESC a, ESC w, ESC
x, ESC n/o, ESC m, ESC y/z are Panasonic's own.

### 5.3 Initialisation (3-4 p20)

On power on, PRIME, or ESC @: head home; print buffer cleared; receive
buffer cleared except by ESC @; vertical tabs cleared; horizontal tabs every
8 columns; DIP switches re-read; quality follows the mode selector; current
position becomes top of form; all command-set modes cleared; on line. ESC m
survives ESC @. Default page length is not stated anywhere.

### 5.4 IBM mode commands, separately

The manual has no separate IBM command chapter. IBM mode is the same
command set with these differences:

- ESC : elite (IBM only), cancelled by DC2; DC2 also cancels compression.
- ESC Q 3 deselects (IBM only); ESC Q n right margin is Standard only.
- ESC 7 selects IBM Graphics set I, ESC 6 set II (only when an IBM Graphics
  mode is selected). In Standard mode the same bytes mean italic
  international on/off.
- ESC 2 activates the ESC A n/72 value; ESC A alone does not change spacing.
  Default 1/6 in.
- ESC R does not work in the IBM Graphics modes (USA fixed); the IBM
  Matrix mode has 32 international characters, so presumably ESC R works
  there (not stated).
- DEL does nothing in the IBM Graphics modes; 0x7F is blank in sets G1 and
  G2.
- ESC m switches mode in either direction.

## 6. Print-mode interactions (Table 4.11 at 4-75 p96, image checked, and comments)

- Pica, elite, semi-compressed, compressed (SI) and proportional exclude one
  another, but may be mixed on one line (each command replaces the last).
- Elite: SI is ignored; ESC M cancels compressed and proportional; ESC p is
  ineffective in elite.
- Emphasised with compressed (SI): only emphasised prints; compression
  returns when emphasis ends. Emphasised with semi-compressed (ESC w 2):
  whichever came last wins. ESC w 3 makes emphasis ineffective.
- NLQ: combines with every pitch, proportional, double width, emphasised,
  underline; double strike is meaningless (already two passes);
  super/subscript cannot be printed in NLQ.
- Super/subscript: double strike meaningless (already two passes);
  superscript and subscript exclude each other; small type comes from
  super/subscript plus compressed.
- Double width combines with everything, including NLQ and proportional.
- Underline combines with everything.
- Proportional in draft is forced emphasised.
- Italic: draft and NLQ; italic tables exist for proportional (4-35, 4-36).
- Double height: none on this printer.
- Print mode selector at NLQ or Comp. locks out software changes of pitch and
  quality.

## 7. Character sets

### 7.1 International sets (Table 4.3, 4-20 p35, image checked; same as A-5 p107)

| n | Set | 23 | 24 | 40 | 5B | 5C | 5D | 5E | 60 | 7B | 7C | 7D | 7E |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | USA | # | $ | @ | [ | \ | ] | ^ | ` | { | \| | } | ~ |
| 1 | France | # | $ | à | ° | ç | § | ^ | ` | é | ù | è | ¨ |
| 2 | Germany | # | $ | § | Ä | Ö | Ü | ^ | ` | ä | ö | ü | ß |
| 3 | England | £ | $ | @ | [ | \ | ] | ^ | ` | { | \| | } | ~ |
| 4 | Denmark I | # | $ | @ | Æ | Ø | Å | ^ | ` | æ | ø | å | ~ |
| 5 | Sweden | # | ¤ | É | Ä | Ö | Å | Ü | é | ä | ö | å | ü |
| 6 | Italy | # | $ | @ | ° | \ | é | ^ | ù | à | ò | è | ì |
| 7 | Spain | Pt | $ | @ | ¡ | Ñ | ¿ | ^ | ` | ¨ | ñ | } | ~ |
| 8 | Japan | # | $ | @ | [ | ¥ | ] | ^ | ` | { | \| | } | ~ |
| 9 | Norway | # | ¤ | É | Æ | Ø | Å | Ü | é | æ | ø | å | ü |
| 10 | Denmark II | # | $ | É | Æ | Ø | Å | Ü | é | æ | ø | å | ü |

These are the Epson FX-style eleven sets. 8-10 by software only.

### 7.2 Standard mode chart (A-1 p103, image checked)

- 0x00-0x1F: control codes (only those listed in 5.1 are named; the rest
  blank).
- 0x20-0x7E: ASCII; 0x7F DEL.
- 0x80-0x9F: control codes again (mirror of 0x00-0x1F).
- 0xA0-0xFE: italic ASCII (same order as 0x20-0x7E); 0xFF DEL.
- With ESC 6, 0x80-0x9F and 0xFF print the italic international
  characters instead (Table 4.2, 4-19 p34, image checked): 80 à, 81 è, 82 ù,
  83 ò, 84 ì, 85 °, 86 £, 87 ¡, 88 ¿, 89 Ñ, 8A ñ, 8B ¤, 8C Pt, 8D Å, 8E å,
  8F ç, 90 §, 91 ß, 92 Æ, 93 æ, 94 Ø, 95 ø, 96 ¨, 97 Ä, 98 Ö, 99 Ü, 9A ä,
  9B ö, 9C ü, 9D É, 9E é, 9F ¥, FF slashed zero (italic).
- With SW8 7-bit, the italic half is out of reach (troubleshooting 6-2).

### 7.3 IBM Matrix set (A-2 p104, image checked)

0x00-0x7F as Standard (with DEL at 0x7F); 0x80-0x9F control mirror;
0xA0-0xDF the 64 block-graphics characters (each a 2-wide by 3-high mosaic
of solid blocks, all 64 combinations, laid out in a regular binary pattern
in the chart); 0xE0-0xFF blank.

### 7.4 IBM Graphics set G1 (A-3 p105, image checked)

0x00-0x7F as ASCII (no DEL; 0x7F blank); 0x80-0x9F control mirror;
0xA0-0xFE the IBM PC code page 437 characters at their usual codes (á í ó ú
ñ Ñ ª º ¿ ⌐ ¬ ½ ¼ ¡ « » at A0-AF; shades, box drawing and blocks B0-DF;
Greek and maths E0-FE); 0xFF space.

### 7.5 IBM Graphics set G2 (A-4 p106, image checked)

As G1 plus: 0x03-0x06 heart, diamond, club, spade; 0x15 §; 0x80-0x9F the
CP437 accented letters (Ç ü é â ä à å ç ê ë è ï î ì Ä Å É æ Æ ô ö ò û ù ÿ Ö
Ü ¢ £ ¥ Pt ƒ) in place of the control mirror. Control codes still work at
0x00-0x1F; 0x7F blank.

### 7.6 Proportional widths, Table 4.5 (4-35 p50), transcribed from the image

Unit 1/120 in. The table is titled "Standard ASCII and Italic ASCII". Its
rows 0-31 list the 32 international glyphs in the order of Table 4.2 (à è ù
ò ì ° £ ¡ ¿ Ñ ñ ¤ Pt Å å ç § ß Æ æ Ø ø ¨ Ä Ö Ü ä ö ü É é ¥), not control
codes: read 0-31 as an internal glyph index. Row 127 is a slashed zero.

| Code | Char | Std | Ital | | Code | Char | Std | Ital |
|---|---|---|---|---|---|---|---|---|
| 0 | à | 12 | 11 | | 64 | @ | 12 | 12 |
| 1 | è | 12 | 11 | | 65 | A | 12 | 12 |
| 2 | ù | 11 | 11 | | 66 | B | 12 | 12 |
| 3 | ò | 10 | 11 | | 67 | C | 12 | 12 |
| 4 | ì | 8 | 8 | | 68 | D | 12 | 12 |
| 5 | ° | 8 | 8 | | 69 | E | 12 | 12 |
| 6 | £ | 12 | 12 | | 70 | F | 12 | 12 |
| 7 | ¡ | 5 | 10 | | 71 | G | 12 | 12 |
| 8 | ¿ | 12 | 11 | | 72 | H | 12 | 12 |
| 9 | Ñ | 12 | 12 | | 73 | I | 8 | 10 |
| 10 | ñ | 11 | 12 | | 74 | J | 11 | 12 |
| 11 | ¤ | 12 | 12 | | 75 | K | 12 | 12 |
| 12 | Pt | 12 | 12 | | 76 | L | 12 | 10 |
| 13 | Å | 12 | 12 | | 77 | M | 12 | 12 |
| 14 | å | 12 | 11 | | 78 | N | 12 | 12 |
| 15 | ç | 11 | 11 | | 79 | O | 12 | 12 |
| 16 | § | 10 | 12 | | 80 | P | 12 | 12 |
| 17 | ß | 11 | 11 | | 81 | Q | 12 | 12 |
| 18 | Æ | 12 | 12 | | 82 | R | 12 | 12 |
| 19 | æ | 12 | 12 | | 83 | S | 12 | 12 |
| 20 | Ø | 12 | 12 | | 84 | T | 12 | 12 |
| 21 | ø | 12 | 11 | | 85 | U | 12 | 12 |
| 22 | ¨ | 8 | 9 | | 86 | V | 12 | 12 |
| 23 | Ä | 12 | 12 | | 87 | W | 12 | 12 |
| 24 | Ö | 12 | 12 | | 88 | X | 10 | 12 |
| 25 | Ü | 12 | 12 | | 89 | Y | 12 | 12 |
| 26 | ä | 12 | 11 | | 90 | Z | 10 | 12 |
| 27 | ö | 10 | 11 | | 91 | [ | 8 | 11 |
| 28 | ü | 11 | 12 | | 92 | \ | 10 | 7 |
| 29 | É | 12 | 12 | | 93 | ] | 8 | 11 |
| 30 | é | 12 | 11 | | 94 | ^ | 12 | 10 |
| 31 | ¥ | 12 | 12 | | 95 | _ | 12 | 12 |
| 32 | space | 12 | 12 | | 96 | ` | 5 | 5 |
| 33 | ! | 5 | 10 | | 97 | a | 12 | 11 |
| 34 | " | 8 | 10 | | 98 | b | 11 | 11 |
| 35 | # | 12 | 12 | | 99 | c | 11 | 11 |
| 36 | $ | 12 | 11 | | 100 | d | 11 | 12 |
| 37 | % | 12 | 12 | | 101 | e | 12 | 11 |
| 38 | & | 12 | 12 | | 102 | f | 10 | 12 |
| 39 | ' | 5 | 6 | | 103 | g | 11 | 11 |
| 40 | ( | 7 | 8 | | 104 | h | 11 | 11 |
| 41 | ) | 7 | 8 | | 105 | i | 8 | 9 |
| 42 | * | 12 | 12 | | 106 | j | 9 | 10 |
| 43 | + | 12 | 12 | | 107 | k | 10 | 11 |
| 44 | , | 6 | 7 | | 108 | l | 8 | 9 |
| 45 | - | 12 | 12 | | 109 | m | 12 | 11 |
| 46 | . | 6 | 7 | | 110 | n | 11 | 10 |
| 47 | / | 10 | 10 | | 111 | o | 12 | 11 |
| 48 | 0 | 12 | 12 | | 112 | p | 11 | 11 |
| 49 | 1 | 12 | 12 | | 113 | q | 11 | 11 |
| 50 | 2 | 12 | 12 | | 114 | r | 11 | 10 |
| 51 | 3 | 12 | 12 | | 115 | s | 12 | 11 |
| 52 | 4 | 12 | 12 | | 116 | t | 11 | 10 |
| 53 | 5 | 12 | 12 | | 117 | u | 12 | 11 |
| 54 | 6 | 12 | 12 | | 118 | v | 12 | 10 |
| 55 | 7 | 12 | 12 | | 119 | w | 13 | 13 |
| 56 | 8 | 12 | 12 | | 120 | x | 10 | 12 |
| 57 | 9 | 12 | 12 | | 121 | y | 12 | 12 |
| 58 | : | 6 | 7 | | 122 | z | 10 | 12 |
| 59 | ; | 6 | 7 | | 123 | { | 9 | 10 |
| 60 | < | 10 | 10 | | 124 | \| | 5 | 9 |
| 61 | = | 12 | 11 | | 125 | } | 9 | 10 |
| 62 | > | 10 | 9 | | 126 | ~ | 12 | 12 |
| 63 | ? | 12 | 11 | | 127 | 0-slash | 12 | 12 |

Notes on the transcription: code 74 is printed "G" in the standard column
(a misprint for J; the italic column shows J). "w" is 13 units, wider than
the 12-unit pica cell, in both columns: read carefully, not an OCR error.

### 7.7 Proportional widths for IBM Graphics characters, Table 4.6 (4-36 p51, image)

Unit 1/120 in. Only the codes below are listed (codes 176-223, the line and
block graphics, and 244-245, the integral halves, are absent: presumably
fixed at 12). Normal / italic:

| Code | Char | N | I | | Code | Char | N | I |
|---|---|---|---|---|---|---|---|---|
| 3 | ♥ | 12 | 12 | | 156 | £ | 12 | 12 |
| 4 | ♦ | 12 | 12 | | 157 | ¥ | 12 | 12 |
| 5 | ♣ | 12 | 12 | | 158 | Pt | 12 | 12 |
| 6 | ♠ | 12 | 12 | | 159 | ƒ | 12 | 12 |
| 21 | § | 10 | 12 | | 160 | á | 12 | 11 |
| 128 | Ç | 12 | 12 | | 161 | í | 8 | 8 |
| 129 | ü | 11 | 12 | | 162 | ó | 10 | 11 |
| 130 | é | 12 | 11 | | 163 | ú | 11 | 11 |
| 131 | â | 12 | 11 | | 164 | ñ | 11 | 12 |
| 132 | ä | 12 | 11 | | 165 | Ñ | 12 | 12 |
| 133 | à | 12 | 11 | | 166 | ª | 12 | 12 |
| 134 | å | 12 | 11 | | 167 | º | 12 | 12 |
| 135 | ç | 11 | 11 | | 168 | ¿ | 12 | 11 |
| 136 | ê | 12 | 11 | | 169 | ⌐ | 12 | 12 |
| 137 | ë | 12 | 11 | | 170 | ¬ | 12 | 12 |
| 138 | è | 12 | 11 | | 171 | ½ | 12 | 12 |
| 139 | ï | 8 | 8 | | 172 | ¼ | 12 | 12 |
| 140 | î | 8 | 10 | | 173 | ¡ | 5 | 10 |
| 141 | ì | 8 | 8 | | 174 | « | 12 | 12 |
| 142 | Ä | 12 | 12 | | 175 | » | 12 | 12 |
| 143 | Å | 12 | 12 | | 224-239 | α β Γ π Σ σ µ γ Φ θ Ω δ ∞ φ ε ∩ | 12 | 12 |
| 144 | É | 12 | 12 | | 240 | ≡ | 12 | 12 |
| 145 | æ | 12 | 12 | | 241 | ± | 12 | 12 |
| 146 | Æ | 12 | 12 | | 242 | ≥ | 12 | 12 |
| 147 | ô | 10 | 11 | | 243 | ≤ | 12 | 12 |
| 148 | ö | 10 | 11 | | 246 | ÷ | 12 | 12 |
| 149 | ò | 10 | 11 | | 247 | ≈ | 12 | 12 |
| 150 | û | 11 | 11 | | 248 | ° | 8 | 8 |
| 151 | ù | 11 | 11 | | 249 | ■ (small) | 12 | 12 |
| 152 | ÿ | 11 | 11 | | 250 | • | 12 | 12 |
| 153 | Ö | 12 | 12 | | 251 | √ | 12 | 12 |
| 154 | Ü | 12 | 12 | | 252 | ⁿ | 8 | 8 |
| 155 | ¢ | 11 | 11 | | 253 | ² | 8 | 8 |
| | | | | | 254 | ■ | 12 | 12 |
| | | | | | 255 | space | 12 | 12 |

The italic column implies italics apply to the IBM special characters in IBM
Graphics mode (the specification lists "82 italic IBM-PC special
characters").

## 8. Download characters (4-70, 4-71 p91, p92, images checked)

- `ESC y c D1 ... D9`: exactly nine column bytes, no attribute byte.
  Bit 7 = top pin (pin 1) down to bit 0 = pin 8; pin 9 not available, so no
  descender control. The character is 9 dots wide plus a 3-dot gap (a
  12-dot pica cell at 120 dpi).
- No two horizontally adjacent dots in a row; the second of a pair is not
  fired.
- Codes usable: 32-126 and 128-255 in 8-bit mode; 32-126 in 7-bit mode.
  The new glyph replaces the ROM character at that code until `ESC z c`.
- The introduction says "up to 40 characters", which does not square with
  any code in 32-126 and 128-255 being usable: probably 40 slots, any codes.
- Nothing on NLQ downloads, on a separate download-set select/deselect, or
  on copying ROM to RAM. Downloads are presumably draft only. (The
  KX-P1080U's firmware confirms it and more: Downloads, under Firmware, in
  `docs/panasonic-kx-p1080.md`.)
- Worked example (gamma at code 67): bytes 0, 12, 146, 65, 34, 28, 64, 0, 128.

## 9. Bit-image graphics (4-40 to 4-49, p58 to p67; Table 4.8, 4.9)

| m | Mode | dpi | dots/line | Head speed | Adjacent dots |
|---|---|---|---|---|---|
| 0 | Standard (ESC K) | 60 | 480 | 12 in/s | allowed |
| 1 | Double (ESC L) | 120 | 960 | 6 in/s | allowed |
| 2 | Double speed double density (ESC Y) | 120 | 960 | 12 in/s | not allowed |
| 3 | Quadruple (ESC Z) | 240 | 1920 | 6 in/s | not allowed |
| 4 | | 80 | 640 | 9 in/s | not stated |
| 5 | | 72 | 576 | 10 in/s | not stated (1:1 aspect with 1/72 rows) |
| 6 | | 90 | 720 | 7.89 in/s | not stated |

- Count n1 + 256 n2 columns.
- 8-pin (ESC K/L/Y/Z, ESC *): one byte per column, bit 7 = pin 1 (top) to
  bit 0 = pin 8; pin 9 unused. With a 7-bit interface bit 7 (pin 1) is
  lost.
- 9-pin (ESC ^ m n1 n2): two bytes per column: first byte pins 1-8 as above;
  second byte bit 7 = pin 9, other bits unused. n counts columns.
- ESC ? c m reassigns ESC K, L, Y or Z (c = 'K', 'L', 'Y', 'Z') to mode m.
- Graphics always print left to right; the graphics mode ends with its data;
  MSB commands (ESC = / > / #) do not touch graphics data.
- Half speed (ESC s) works only with m = 0, 2 and 5.

## 10. Emulations named

- The manual names **IBM Matrix Printer** and **IBM Graphics Printer**
  (modes I and II) as emulated (4-18 p33), selected by DIP SW1 OFF and
  SW5-7, or ESC m 1-3.
- It names **no Epson model** and never uses the word Epson. The Standard
  mode command set is plainly Epson FX-80-like (ESC K/L/Y/Z, ESC *, ESC ^,
  ESC ?, ESC R with the eleven Epson sets, ESC 4/5, ESC 6/7, ESC S/T,
  ESC E/F/G/H, ESC W, ESC -, ESC D, ESC B, ESC C, ESC N/O, ESC l/Q, ESC J,
  ESC 3/A/0/1/2, ESC =/>/#, ESC </U/s/8/9, ESC @), with Panasonic and
  Star-style additions and an incompatible ESC ! and download format.
- The IBM-PC trademark appears only in the trademark notice and examples.
- The **IBM Proprinter is not mentioned**.

## 11. Oddities, contradictions, gaps

1. Printed page 4-66 (ESC > MSB on) is missing from the scan.
2. Table 4.5 numbers its first 32 rows 0-31 although those codes are
   control codes in every chart: they are the 32 international glyphs in
   Table 4.2 order.
3. Table 4.5 gives "w" 13 units, wider than a pica cell, upright and italic.
4. Table 4.5 standard column prints "G" for code 74 (J).
5. Code 127 has a width (slashed zero) in Table 4.5 but is DEL in A-1;
   ESC 6 puts italic slashed zero at 255.
6. ESC ! uses bit 0 elite, 2 compressed, 3 emphasised, 4 double strike,
   5 double width; bit 1 unused, bits 6-7 zero. Not Epson's layout (no
   proportional, italic, underline bits).
7. The specification says 132 IBM-PC special characters and 82 italic ones;
   3-3 says Graphics mode I has 95 and mode II 132 specials.
8. Table 4.12 lists IBM Matrix as SW1 OFF, SW5 ON, SW6 OFF, SW7 OFF, and
   Graphics I as SW6 ON, SW7 OFF, consistent with Table 3.3.
9. ESC C n with n = 0 is said to "return to the inch designation", but no
   default page length is ever stated.
10. ESC e 0 n is cancelled by n = 0, ESC e 1 n by n = 1 (with n = 0 doing a
    print without feed).
11. DC1 is said to lose the print buffer data received before it.
12. CAN is described as clearing the receive buffer, though its example
    shows only the pending line text being dropped.
13. Downloads: "up to 40 characters" versus "any location 32-126, 128-255".
    (The KX-P1080U's firmware: 40 slots, at any of those codes.)
14. The ESC P and ESC M descriptions say they work only at Std. Pgm.; ESC w,
    ESC x, ESC n, ESC o, ESC ! do not say, though 3-1 says software cannot
    change the mode at NLQ or Comp.
15. Underline is not drawn under "IBM 12-dot special characters", a phrase
    not explained anywhere; perhaps the CP437 line-drawing characters, which
    must span the full 12-dot cell.
16. Self test and hex dump layouts are not described.
17. The 1-1 page says 11 international sets and 96 ASCII; the italic upper
    half and DEL at 0xFF match Epson's FX layout.
18. The single-sheet first line, top margin, and bottom margin for single
    sheets are not given; only fanfold dimensions in E-1.
19. The KX-P1080U's CPU ROM holds draft forms of the IBM PC characters and
    block graphics (internal ROM 0x0DB0 on), which nothing in the U
    reaches: the U's firmware evidently shares its character code with the
    i's (`docs/panasonic-kx-p1080.md`).
