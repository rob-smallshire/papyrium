# Commodore MPS-803 behaviour notes

What Papyrium takes from the Commodore MPS-803's manuals, restated in our
own words. The manuals are copyrighted and kept, uncommitted, in
`docs/local/commodore-mps-803/`, with the printer's ROM images:

- **UG**: *A Friendly Introduction to Your MPS-803 Dot Matrix Printer*
  (user's guide, (c) 1984, printed in Japan), 56 numbered pages scanned as 32
  two-page spreads. References are to the booklet's own page numbers
  ("UG p. 38"). The scan's own text layer is poor; it was re-OCRed per half
  spread, and anything numeric was checked against the page images.
- **SM**: *Service Manual MPS-803*, PN 314003-05, June 1987, 90 PDF pages.
  References are to the printed page numbers ("SM p. 1-5", "SM p. 3-12").
  The full schematic is an unnumbered fold-out in chapter 5, cited as
  "SM schematic (PDF p. 71)".

The SM's opening line calls the MPS-803 a **Brother** personal computer
printer (SM p. 1-1). That fits the belief that the mechanism is Brother's,
as in the first Centronics GLP. The SM is written for **ROM revision U32053A**
(SM p. 1-4).

Where the two manuals disagree, both readings are given. The SM is the more
precise of the two, and the more likely to match the firmware.

---

## 1. Summary

| Item | Value | Source |
|---|---|---|
| CPU | NEC µPD7811 (78xx family, 64-pin), internal 4 KB mask ROM, 256 B RAM | SM p. 1-11, 3-6 |
| Clock | 11 MHz crystal on X1/X2 | SM schematic (PDF p. 71) |
| Control program and character generator | both in the 4 KB internal ROM | SM p. 3-6 |
| External ROM | **optional, not fitted** ("OPTION: 2732/64 and 74LS373"), for a ROM-controlled variant | SM p. 3-10, 3-11, schematic note |
| Head | 8 wires, 8 solenoids (P8 head); characters and graphics use 7 vertical dots | SM p. 1-2, 3-1, 3-13 |
| Dot pitch | 1/60 in horizontal, 1/72 in vertical; wire diameter 0.3 mm | UG p. 49, SM p. 1-2 |
| Character cell | 6 dots wide (1/10 in) × 7 high; glyph body 5 × 7 | UG p. 27, 49; SM p. 1-2, 3-1, 3-12 |
| Pitch, line | 10 cpi, 80 columns, 480 dot columns per line | UG p. 42, 49; SM p. 1-2, 1-6 |
| Line spacing | 1/6 or 1/8 in by rear switch (characters); 7/72 in in bit-image mode | SM p. 1-2, 1-8 |
| Speed | 60 cps; line feed 4 lines/s (text, 6 lpi), 5.6 lines/s (bit image) | UG p. 49, SM p. 1-2 |
| Bus | CBM serial bus, listener only, device 4 or 5 by rear switch | SM p. 1-12 |
| Secondary address | 0 (or none) = graphic (upper case/graphics); 7 = business (lower/upper case) | SM p. 1-8, 1-12 |

---

## 2. Device number, secondary addresses, bus protocol

### 2.1 Device (listener) number

- A rear slide switch, SW1 ("device number select" / "DEVICE"), sets the
  listener address to 4 or 5; it ships at 4 (UG p. 5, 17; SM p. 1-3, 2-3, 3-9).
- On the bus the printer accepts LISTEN bytes $24 (device 4) or $25
  (device 5): listener address + $20 (SM p. 1-8, 1-12).
- The SM's troubleshooting table blames "DEVICE NOT PRESENT" on the SW1
  setting, SW1 itself or the CPU port it is read on (SM p. 7-2).

### 2.2 Secondary address (SM p. 1-8, 1-12; UG p. 21-24)

- The secondary byte the printer receives is SA + $60. So $60 means SA 0 and
  $67 means SA 7.
- SA 0 selects **graphic mode** (upper case and PETSCII graphics). It is the
  default when no secondary address is sent, and the SM states that $60 is
  assumed then.
- SA 7 selects **business mode** (lower case and upper case).
- Any other SA is "invalid" (SM p. 1-8). The SM does not say what the
  printer then does: it may ignore the SA or treat it as 0. **Uncertain**;
  check the firmware.
- Data sent with ATN high and no secondary address is taken as SA 0
  (timing diagram note, SM p. 3-7).
- The character set chosen by SA lasts for the "ON LINE range", from the
  LISTEN to the UNLISTEN. Within that range CHR$(17) and CHR$(145) can
  change it (§3.8).

  Received with no CR or LF in between, the same SA keeps a set changed by
  $11/$91; a different SA replaces it with the set the new SA selects
  (SM p. 1-8, item 9).
- Function codes are acted on only while the printer is on line. The modes,
  values and data they set are kept while it is off line (SM p. 1-8, item 9).

### 2.3 Serial bus behaviour (SM p. 1-10 to 1-12, 3-6 to 3-8)

- Connector: 6-pin DIN, two in parallel (J1, J2) for daisy-chaining. Pin 1 is
  SRQ, 2 GND, 3 ATN, 4 CLK, 5 DATA, 6 RESET. A Faston terminal grounds the
  cable shield to frame ground (UG p. 53; SM p. 1-10, 2-3, 3-7).
- The printer is a listener only. It never drives SRQ or CLK
  (SM p. 1-12, 4a). It drives only DATA.
- Frame: LISTEN, an optional secondary byte and the data bytes are sent, the
  last data byte with the EOI handshake, then UNLISTEN with ATN low.
  Bytes are 8 bits, sent LSB first and sampled on the rising edge of CLK
  (SM p. 1-12).
- Bytes sent with ATN low are the listener address, the secondary address
  and UNL (SM p. 3-7).
- **Not our address**: if the LISTEN byte is not ours, the printer performs a
  "system line release". It pulls DATA low for 60 to 80 µs, whatever CLK is
  doing, then releases the bus (SM p. 1-12, 3-7).
- **Timing** (SM p. 3-7, 3-8):
  - On a falling ATN, the printer answers by pulling DATA low within
    TAT ≤ 1 ms. The diagram also marks "33 ms max" in this region, and it
    is unclear which interval that applies to. **Uncertain.**
  - Per byte: the talker releases CLK, and the printer releases DATA once it
    sees CLK released. If the talker then holds CLK released for 200 µs or
    more before the first bit, that is the EOI handshake.
  - After each byte the printer holds DATA low for TH. TH is the printer's
    BUSY time and can be long, for example while a line prints. To ask for
    the next byte, the printer waits for CLK to be released, then releases
    DATA. TF is 20 to 1000 µs.
  - At least 20 µs (TPR) separates the listener address and the secondary
    address.
  - After ATN rises at the end of a LISTEN or UNLISTEN sequence, the printer
    waits at least **3.3 ms** for CLK to be released, then releases DATA
    (SM p. 3-7; the flowchart also shows a 3.3 ms delay, SM p. 1-13).
- **While printing**, the printer holds DATA low, so the computer cannot send
  (UG p. 53; SM p. 2-3).

  A byte's handshake does not finish until the printer's internal BUSY ends
  (SM p. 1-12, 4d).
- **On an internal error** (for example a motor error) the printer stops
  responding on the bus altogether (UG p. 53; SM p. 1-12, 4e).
- RESET (pin 6) resets the printer exactly as power-on does (SM p. 3-7).
- UG p. 16: a logical file number above 127 gives double-spaced lines. That
  is the computer's KERNAL appending an LF after each CR, not a printer
  feature.

---

## 3. Control codes

Table of codes (UG p. 26, 48, 51, 52; SM p. 1-5 to 1-7, 1-16, 1-17):

| Code | Name | Function |
|---|---|---|
| $08 (8) | BS | Enter bit-image ("mark print") mode |
| $0A (10) | LF / NL | Print the buffer, then line feed |
| $0D (13) | CR | Print the buffer, then line feed; also ends RVS and quote mode |
| $0E (14) | SO / EN ON | Double-width ("enhanced") character mode |
| $0F (15) | SI / EN OFF | Standard-width character mode (the power-on mode) |
| $10 (16) | POS | Print position in character columns: two ASCII digits follow |
| $11 (17) | "cursor down" / BUS | Business (lower/upper case) character set, until $91 or CR/LF |
| $12 (18) | RVS ON | Reverse field on |
| $1A (26) | SUB | Repeat one bit-image byte n times |
| $1B (27) | ESC | Only used as ESC POS, a print position in dots |
| $22 (34) | quote | Printed as `"`; toggles quote mode (§3.10) |
| $91 (145) | "cursor up" / GRAPH | Graphic (upper case/graphics) character set, until $11 or CR/LF |
| $92 (146) | RVS OFF | Reverse field off |

Other codes in $00-$1F and $80-$9F are not defined and are ignored
(SM p. 1-7). In bit-image mode every code except POS, ESC POS, SUB, NL and
CR is ignored (SM p. 1-7). However, SI and SO still end bit-image mode, as
their own entries state (SM p. 1-5).

The UG data-buffer table names BS, LF, CR, SO, SI, POS, $11, $12, SUB, ESC
POS, $91 and $92 as the codes that take room in the buffer (UG p. 48).

### 3.1 Print modes (SM p. 1-4, 1-5)

The printer has three print modes:

- **STANDARD CHR**, set by SI. Prints bidirectionally.
- **DOUBLE-WIDTH CHR**, set by SO. Prints bidirectionally.
- **MARK PRINT** (bit image), set by BS. Prints unidirectionally, left to
  right.

Each mode lasts until another mode code arrives. CR and LF do not cancel
it, so it carries on to the next line (SM p. 1-5; UG p. 27). The UG also
says that SO and SI cancel bit-image mode (UG p. 27).

Within a mode, only certain codes are valid (SM p. 1-5):

- In standard and double-width modes: POS, ESC POS, GRAPH ($91),
  BUSINESS ($11), RVS ON, RVS OFF, NL and CR.
- In bit-image mode: BS, POS, ESC POS, SUB, NL and CR.

The SM says three times that a POS or ESC POS "right before" BS, SO or SI is
invalid. One reading is that a position set immediately before a mode
change is discarded. **Uncertain**: the firmware will settle it.

Reverse field printing is always unidirectional, to protect the head
(SM p. 1-5).

### 3.2 Standard and double width: SI $0F, SO $0E (UG p. 27; SM p. 1-5)

- A standard character is 6 dot columns wide by 7 dots high (UG p. 27, 49).
- After SO, characters are doubled horizontally: 12 columns by 7 dots, so
  each character takes two character columns (UG p. 27). The SM's POS
  example puts a double-width character in columns 40 and 41 (SM p. 1-5).
- SI ends double width and is the power-on mode.
- Both SO and SI end bit-image mode. The text line that follows gets a
  1/6 in line feed (UG p. 27, 29).
- UG p. 27 calls this "enhanced" printing. It means double width only, not
  emphasis.

### 3.3 Bit image: BS $08 (UG p. 28-31; SM p. 1-5)

- After BS, each byte with **bit 7 set** is one 7-dot vertical column printed
  at 1/60 in pitch (SM p. 1-2; UG p. 49).

  **Bit order**: bit 0 (weight 1) is the top dot and bit 6 (weight 64) the
  bottom dot. The user adds 128 to every column value (UG p. 28-29). In the
  UG's worked example, 152 = 128 + 16 + 8 sets the dots in rows 8 and 16.
- A byte with **bit 7 clear** is taken as a control code, not graphic data
  (SM p. 1-5: the 8th bit decides whether a byte is data or a function code).
  The flowchart's print interrupt clears the MSB before sending a column to
  the head (SM p. 1-15).
- The head prints only 7 of its 8 wires. Which wire is idle is not stated
  (§7.6).
- Bit-image mode prints left to right only (SM p. 1-2, 1-4).
- A line feed in bit-image mode is 7/72 in (SM p. 1-8), which is
  72/7 ≈ 10.3 lpi (UG p. 49; SM p. 1-2). Consecutive 7-dot bands therefore
  touch.

  **Conflict**: UG p. 44 gives 9 lpi for bit-image line feeds, but its own
  specification gives 72/7 lpi, and so does the SM. Take 7/72 in.
- The 1/6 or 1/8 in switch does not apply in bit-image mode (SM p. 1-3).
- Bit-image mode lasts until SI or SO (SM p. 1-5).

  UG p. 30, "all bit patterns": sends CHR$(128) to CHR$(255) after BS and
  says this prints every pattern.

### 3.4 Repeat bit image: SUB $1A n d (UG p. 37; SM p. 1-6, 1-7)

- Takes effect only in bit-image mode. In the character modes the SUB byte
  alone is ignored (SM p. 1-6). It takes 4 bytes of buffer (SM p. 1-9;
  UG p. 48).
- n is a binary count from 0 to 255, and 0 means 256. For more than 256
  repeats, send the sequence again (UG p. 37; SM p. 1-6).
- d is one bit-image byte. If d is below 128, the whole command is
  ignored (SM p. 1-7).
- If the repeated data runs past the right margin, printing goes on at the
  start of the next line after an automatic line feed (SM p. 1-7).

  The SM also gives a garbled condition, "(479-239) n (475-239)", for the
  line-end rule. Plausibly it is the same 475/469 margin rule as for
  ESC POS (§3.6), restated for SUB. **Uncertain.**

### 3.5 Print position in characters: POS $10 "nn" (UG p. 36-37; SM p. 1-5, 1-6)

- POS is followed by **two ASCII decimal digits**, "00" to "79". They give
  an absolute start column, counted in standard character widths from 0
  (SM p. 1-5).
- A value of 80 or more is invalid. Non-digit bytes give an undefined result
  (SM p. 1-5).
- The position is absolute, so moving left is possible.

  If the text placed at the new column runs past column 79, it wraps as
  overprint: an automatic line feed, then the excess prints from column 0.
  The SM's example: a 2-column double-width character placed at 79 prints
  at columns 0 and 1 of the next line (SM p. 1-6).
- If POS commands follow one another, only the last is used (SM p. 1-6).
- POS takes 4 bytes of buffer (UG p. 48; SM p. 1-9).
- UG p. 54 (screen hardcopy) uses POS "00" at the start of each line.

### 3.6 Print position in dots: ESC POS nH nL (UG p. 38-39; SM p. 1-6)

- Sequence: $1B $10 nH nL, a binary dot-column number with nH carrying the
  top two bits (P10, P9) and nL the low 8 bits (UG p. 38; SM p. 1-6).
- **Range conflict**: the UG gives 0 to 639 and says a larger value prints
  from the start of the next line. The SM gives 0 to 479 and says
  480 or more is invalid (SM p. 1-6).

  The line is 480 dots (80 × 6, UG p. 42), so 0 to 479 fits the hardware.
  The UG's 639 looks like a leftover from an 8-dot cell or a different
  printer. Check the firmware.
- After a position of 475 to 479, the next standard character goes to the
  start of the next line, with a line feed. For double width the threshold
  is 469 to 479 (SM p. 1-6).
- Overstriking: positioning onto dots already set prints over them
  (UG p. 38).
- If ESC POS commands follow one another, only the last is used. ESC is
  defined only together with POS; anything else after ESC gives an
  undefined result (SM p. 1-6).
- UG p. 39 shows a sine curve plotted with ESC POS in bit-image mode.

### 3.7 Reverse field: RVS ON $12, RVS OFF $92 (UG p. 32-34; SM p. 1-7)

- Prints white characters on a black ground: the character cell is
  inverted (UG p. 32).
- Takes effect in the standard and double-width modes (SM p. 1-7).
- Cancelled by RVS OFF and by CR or LF, the "print commands" (SM p. 1-7).
  UG p. 41 says CR turns reverse field off; SM p. 1-5 says both NL and CR
  do.
- **Not** cancelled by the automatic line feed that comes from overflow
  (SM p. 1-7).
- Reverse printing is unidirectional (SM p. 1-5).

### 3.8 Character set inside a line: $11 and $91 (UG p. 34-35; SM p. 1-7, 1-8)

- $11 (CHR$(17), "cursor down") switches to the business set. $91
  (CHR$(145), "cursor up") switches to the graphic set.
- The switch lasts until the other code or until CR or LF (the UG mentions
  only CR). Both sets can therefore appear on one line (UG p. 34;
  SM p. 1-7).
- Like RVS, the switch survives the automatic line feed from overflow
  (SM p. 1-7).
- For how this interacts with the secondary address, see §2.2.

### 3.9 Line feed and carriage return: LF $0A, CR $0D (UG p. 41, 44; SM p. 1-5, 1-8)

- Both are "print commands": each prints the buffered line, then feeds the
  paper one line. Either one alone gives a plain line feed. There is no
  CR-only return to the start of the same line (UG p. 41; SM p. 1-5).

  The SM notes that a CR always does a carriage return (SM p. 1-4, 1-7).
- Neither one cancels the print mode set by SI, SO or BS.
- Both cancel RVS ON and the $11/$91 character set.
- CR also ends quote mode (§3.10). The SM says LF does not (SM p. 1-5),
  but UG p. 51-52 says quote mode lasts "until the end of the line".
  **Uncertain** for LF.
- **Feed amount** comes from the print mode in effect just before the print
  command (UG p. 44; SM p. 1-8):
  - text modes (standard and double width): 1/6 or 1/8 in, by the rear
    switch;
  - bit-image mode: 7/72 in.
- The amount of a manual (button) feed follows the print mode in effect just
  before the last UNL (SM p. 1-8).
- **Switch SW2** ("LF" / "paper feed pitch select") chooses 6 or 8 lpi.
  It is labelled "6" and "8" and ships at 6 (UG p. 5; SM p. 1-3, 2-3, 3-9).

  UG p. 49 calls 6 lpi the USA setting and 8 lpi the European one.
- Line feed motor: 1/216 in per step, 36 steps for 1/6 in (§7.5). That
  gives 27 steps for 1/8 in and 21 steps for 7/72 in.

### 3.10 Quote mode: $22 (UG p. 45-47, 51-52; SM p. 1-4, 1-7)

- After an odd number of `"` characters on a line, control codes become
  visible. Each byte in $00-$1F prints as the **reverse-field form of the
  character 64 higher** ($40-$5F). Each byte in $80-$9F prints as the
  reverse-field form of $C0-$DF (SM p. 1-4, 1-7).
- This lasts until the next `"`. CR ends it (SM p. 1-7). The UG says it
  ends at an even number of quotes or "the end of the line" (UG p. 51-52).
- **CR is never shown**, even in quote mode. It always returns the carriage,
  so a reversed "M" cannot be printed this way (SM p. 1-7).
- RVS ON/OFF state and quote mode are separate (diagram, SM p. 1-7):
  - With RVS off: inside quotes the control codes print reversed and
    ordinary characters print normally.
  - With RVS on: everything prints reversed, and CR (or a closing quote)
    ends the quote function. CR also ends RVS ON. The automatic line feed
    ends neither.

  The exact cancellation rules drawn in this diagram are partly illegible.
  **Uncertain**; check the firmware.
- UG p. 46-47 shows this with program listings containing cursor and colour
  codes. Appendix D's hardcopy program cannot print what follows a reversed
  quote (UG p. 54).

### 3.11 Mixed modes (UG p. 43-44; SM p. 1-4)

Standard characters, double-width characters and bit image can be mixed on
one line. The UG's example on p. 44 sends BS, a bit-image run, SO with text,
and SUB with a repeated column on the same line.

---

## 4. Buffer and automatic printing

- **Buffer size conflict**: the UG says the print-line buffer holds up to
  90 bytes, with at least one used for the character mode (UG p. 48). The SM
  says 152 bytes (SM p. 1-9).
- Buffer cost per code (UG p. 48; SM p. 1-9):
  - 4 bytes each: POS + 2 digits, ESC POS + 2 bytes, SUB + n + data;
  - 1 byte each: BS, LF, CR, SO, SI, $11, $12, $91, $92 (the SM's 1-byte
    list is SI, SO, BS, NL, CR, RVS and GRAPH/BUSINESS).
- Automatic printing happens in two cases (SM p. 1-9; UG p. 41-42 describes
  three, the third being both at once):
  1. **The buffer fills.** Whatever is buffered is printed without a line
     feed, and the head's dot position stays where printing stopped. Further
     data continues from that point on the same line.

     Output is the same as if the buffer had not filled. Printing triggered
     this way is always unidirectional, in every mode (SM p. 1-9).
  2. **Data passes the right margin** (480 dots). The line prints to the last
     column, the paper feeds a line, and the excess prints from the start of
     the next line.

     The SM adds that printing does not start merely because column 480 has
     been reached. It is unclear whether this means the wrap is lazy, waiting
     for the next printable byte. **Uncertain.**
- No data is lost through overflow (UG p. 48).
- The automatic line feed does **not** cancel RVS ON, $11/$91 or quote mode
  (SM p. 1-7).
- **Head temperature** (SM p. 3-13): a PTC thermistor near the head drive
  transistor feeds analogue input AN1. When AN1 reaches about 2.5 V (about
  60 °C), the printer adds roughly 0.5 s of BUSY after each printed line, to
  let the head cool.

---

## 5. Character sets

### 5.1 Matrix and geometry

- Each character occupies a cell 6 dots wide (6 × 1/60 in = 1/10 in) and
  7 dots high (7 × 1/72 in ≈ 0.097 in).

  Ordinary characters use a 5 × 7 body plus a blank column (SM p. 1-2:
  "horizontal 5 dots (2.0 mm)"; SM p. 3-1: "7 × 5"; UG p. 29: zodiac signs
  "7 × 5").

  Graphics characters use the full 6 columns so they join across cells: the
  UG and SM tables show block and line graphics reaching both sides of the
  cell (UG p. 27, 49, 51; SM p. 1-16).
- The table grids in SM p. 1-16 and 1-17 are drawn 6 wide by 8 high, with the
  8th (bottom) row always empty. That is consistent with 7 rows used on an
  8-wire head.
- **No descenders.** Lower-case g, j, p, q and y are drawn within the same
  7 rows as capitals (SM p. 1-16).
- The zero is drawn slashed (SM p. 1-16, 1-17; UG p. 51).
- Lines are 80 columns (480 dots) at 10 cpi.

  Paper: cut sheet A4 or letter, or continuous paper 4 to 10 in wide with
  the optional tractor. Friction feed is standard. The printer takes an
  original plus 2 copies (UG p. 49; SM p. 1-2).

### 5.2 Graphic mode, SA 0 (UG p. 51; SM p. 1-17)

| Codes | Prints |
|---|---|
| $00-$1F | control codes (table above); nothing printed except in quote mode |
| $20-$3F | space, punctuation, digits (as PETSCII/ASCII) |
| $40-$5F | @, A-Z (upper case), [, £, ], ↑, ← |
| $60-$7F | PETSCII graphics, the same glyphs as $C0-$DF (shifted-letter graphics: ─, ♠, │, …, ♥, ╭, ╮, ●, ○, ♣, ♦, ┼, π-like, etc.) |
| $80-$9F | control codes ($91 GRAPH/cursor up, $92 RVS OFF); otherwise nothing |
| $A0-$BF | PETSCII block graphics (Commodore-key graphics) |
| $C0-$DF | PETSCII graphics, the same as $60-$7F |
| $E0-$FF | the same as $A0-$BF |

$FF prints the π-like character, as it does on screen.

### 5.3 Business mode, SA 7 (UG p. 52; SM p. 1-16)

| Codes | Prints |
|---|---|
| $20-$3F | the same as in graphic mode |
| $40 | @ |
| $41-$5A | **lower case** a-z |
| $5B-$5F | [, £, ], ↑, ← |
| $60 | ─ (horizontal line) |
| $61-$7A | **upper case** A-Z |
| $7B-$7F | graphics (┼, checkerboard, │, and others) |
| $A0-$BF | block graphics (as in graphic mode, with some differences at $BA and $BF) |
| $C0 | ─ |
| $C1-$DA | upper case A-Z (the same as $61-$7A) |
| $DB-$DF | graphics |
| $E0-$FF | the same as $A0-$BF |

This is the usual PETSCII lower/upper case arrangement. The two sets
differ only in $41-$5A, $61-$7A, $C1-$DA and a handful of graphics such as
the ✓ at $BA and $FA.

The bitmaps are in UG p. 51-52 and SM p. 1-16 and 1-17. The scans are too
coarse to transcribe dot for dot with confidence; the ROM is the authority.

### 5.4 User-defined characters

The UG mentions "a custom user-defined character" (UG p. 1). There is no
download command; this means bit-image graphics (UG p. 29-32, zodiac
example).

---

## 6. Front panel, switches, power-on, self test, errors

### 6.1 Controls

- **Power switch**: rocker on the right side. It doubles as a circuit
  breaker. If the breaker trips, the switch still shows on, and you turn it
  off and on again to reset it (UG p. 3; SM p. 3-16).
- **POWER/error lamp** (red LED) beside the paper advance button
  (UG p. 4; SM p. 1-3, 2-2):
  - lit steadily when the printer is on;
  - flashes about 2.5 times a second on paper empty, until cancelled;
  - flashes about 10 times a second on a motor error (SM p. 1-9, 3-8).
- **Paper advance (LF) button** (SM p. 1-9, 3-8; UG p. 4):
  - Off line (no data being received), a press feeds one line. Holding it
    for about 0.5 s or more gives continuous line feeds until release.

    It feeds whether or not paper is loaded. The flowchart shows one LF,
    then a 0.5 s delay, then repeated LFs (SM p. 1-14).
  - After paper empty, load paper and press it to cancel the error. That
    press does not feed paper.
  - On line it does nothing, except that it can still cancel paper empty
    until the first print command or buffer-full. After that it does
    nothing until UNL (SM p. 1-9, 13(1)(c)).
  - It is read on an interrupt (flowchart "LF SW INTERRUPT", SM p. 1-14).
  - Holding it at power-on starts the self test (§6.3).
  - The manual feed amount follows the mode before the last UNL (§3.9).
- **Rear switches**: SW1, device 4 or 5; SW2, 1/6 or 1/8 in line feed
  (UG p. 5; SM p. 2-3, 3-9). Both are read through analogue inputs (§7.3).
- **Platen knob**: the UG says it moves paper forward only (UG p. 4). The SM
  says it turns both ways (SM p. 2-2).
- **Paper release lever**: frees the paper so it can be squared up. Leave it
  open when the tractor is fitted (SM p. 2-8, 2-10).
- **Top cover** with a paper cutter (UG p. 4).

### 6.2 Power-on and reset (SM p. 1-9, 1-13, 3-9, 3-15)

1. On power-on or reset, the ports and memory are initialised and the
   internal ROM is checked (a "ROM CHECK" happens: SM p. 3-9, 7-1).
2. If the ROM check passes, the carriage moves left to the home switch, then
   out to the middle of the line, and stops there.

   - If reaching the home switch takes too long, that is a MOTOR ERROR.
   - If the home switch is still made after moving away, that is also a
     MOTOR ERROR (SM p. 3-9).
   - Accounts of the move differ: SM p. 1-9 and UG p. 12 say left, then the
     middle. SM p. 2-10 says all the way right, then home at the far left.
     The SM chapter 1 and chapter 3 accounts agree on left then middle.
3. The paper-empty flag is set (flowchart "PE FLAG SETTING", SM p. 1-13).
   If the LF button is held, the self test runs. Otherwise the listener
   address is read and the printer waits for data.
4. If the ROM check fails, the lamp lights but does not flash and the
   carriage does not move (troubleshooting, SM p. 7-1).
5. Reset hardware: the RESET pulse at power-on is about 60 ms. RESET is also
   held low while +5 V is below about 4.0 V, and while bus RESET (INIT) is
   low (SM p. 3-15).

   The manuals say to wait at least 2 s (SM p. 2-1) or one minute (UG p. 15)
   before turning the printer back on.

### 6.3 Self test (SM p. 1-9; UG p. 4, 12-13)

- Hold the paper advance button while switching on. The printer tests
  everything except the interface.
- Pattern: a rolling ASCII pattern, 80 characters a line, each line starting
  one character later. The UG's photographed sample begins `ABCDEFGHIJ…`,
  then `BCDEFGHI…`, running through the alphabet, symbols and graphics
  (UG p. 13). Use full-width paper.
- Manual line feed does not work during the self test. The only way to stop
  it is to switch off (SM p. 1-9).
- The SM measures noise "in rolling ASCII printing" (SM p. 1-4).

### 6.4 Paper empty (SM p. 1-3, 1-8, 1-9, 3-4, 3-9)

- A lever switch (PESW) under the paper path detects paper. With no paper
  the actuator rises and PESW goes high.
- The error is not acted on at once. It takes effect **3 lines after** the
  switch first sees no paper, so the bottom of the sheet can still be
  printed.

  The check happens just before each line feed and each print start
  (SM p. 3-9).
- Off line: data is still accepted. When the mechanism starts to move, BUSY
  is set, the paper-empty check runs and the lamp flashes.
- On line: the check runs on data input and the lamp flashes. BUSY is
  asserted on the last data byte.

  The SM's diagram (SM p. 1-8) shows BUSY held through CR, LF or
  buffer-full until the error is cleared.
- The error is cleared by loading paper and pressing LF.

### 6.5 Motor error

The motor error is raised by the home-position check at power-on
(SM p. 3-9). It is also raised if the home switch is made while printing:
the printer goes into the error state, stops printing, and stops answering
the bus (SM p. 1-3, 1-12).

The lamp flashes about 10 times a second. Missing +24 V is a common cause
(SM p. 7-1).

---

## 7. Hardware (service manual)

### 7.1 Block structure (SM p. 1-1, 3-5)

The printer has four sections:

- **Logic card**: CPU, interface, panel, limit switches, the optional
  external ROM socket, and the driver circuits for the head, carriage and
  paper feed, plus reset.
- **Mechanism**: an 8-pin head, the carriage (CR) stepper on a timing belt,
  the paper feed (LF) stepper, the home-position and paper-empty switches,
  and the ribbon, which is driven by carriage travel.
- **Panel**: LED and LF button.
- **Power supply**: transformer, noise filter, breaker switch.

### 7.2 CPU (SM p. 1-11, 3-6; schematic PDF p. 71)

- **NEC µPD7811**, labelled "7811G" on the board drawing (SM p. 3-11), with
  4 KB of internal mask ROM and 256 bytes of internal RAM (SM p. 3-6).
- **11 MHz** crystal between X1 (pin 31) and X2 (pin 30) (schematic).
- "The control program and the CG ROM are masked in the 4K byte ROM in the
  CPU" (SM p. 3-6): **the character generator is inside the internal ROM.**
- MODE1 is tied high and MODE0 low for internal-ROM operation (SM p. 3-6,
  3-10). Jumpers JW1/JW2 and R39 (4.7 k to +5 V) set the MODE pins.
- The A/D converter is used: 8 bits over 0 to 5 V, with VAREF = AVCC = +5 V
  (SM p. 3-6).
- NMI (pin 25) is held high through 4.7 k (R36) with a capacitor to 0 V.
  It is not used beyond that.

### 7.3 Port assignment (from SM p. 3-6 to 3-13 and the schematic)

| Pin | Port | Direction | Use |
|---|---|---|---|
| PA0-PA3 | Port A | out | Carriage stepper phases A, B, /A, /B through M54567 #6 (CR A, CR B, CR /A, CR /B) (SM p. 3-12) |
| PA4-PA7 | Port A | out | Line feed stepper phases A, B, /A, /B through M54567 #1 (SM p. 3-11) |
| PB0-PB7 | Port B | out | Head wires 1-8, **active low** ("negative logic"), through M54567 #8 (PB0-3 → wires 1-4) and #7 (PB4-7 → wires 5-8) (SM p. 3-13) |
| PC0 | Port C | in | /LFSW, the paper advance button; low = pressed (SM p. 3-8) |
| PC1/RxD | Port C | in | Bus DATA (read), through 1.2 k (SM p. 3-6) |
| PC2/SCK | Port C | in | Bus CLK, buffered through two 7406 inverters, so true polarity: the serial shift clock (SM p. 1-11, 3-6) |
| PC3/INT2 | Port C | in | Bus ATN, through 1.2 k, read directly (SM p. 1-11) |
| PC4 | Port C | out | POWER LED, driven through a transistor; high = lit, normally high, toggled to flash (SM p. 3-8) |
| PC5 | Port C | in | Bus CLK **inverted** (after one 7406), the same node as INT1 (SM p. 1-11) |
| INT1 (pin 26) | — | in | Bus CLK inverted (the same as PC5); interrupt on clock edges (SM p. 1-11) |
| PC6 | Port C | out | /CRPLS: low = carriage motor on +24 V (running), high = held on +9 V (stopped) (SM p. 3-12) |
| PC7 | Port C | out | /HPLS: head pulse; low for the solenoid on-time, which switches the drivers' supply through Q11/Q12/Q10 (SM p. 3-13) |
| PF0-PF4 | Port F | out | Address A8-A12 to the optional external ROM (SM p. 3-10) |
| PF5 | Port F | out | Drives bus DATA through a 7406 open-collector inverter: PF5 = 1 pulls DATA low (SM p. 1-11) |
| PF6 | Port F | in | HPSW, carriage home switch; low at the left end (SM p. 3-9) |
| PF7 | Port F | in | PESW, paper-empty switch; high = no paper (SM p. 3-9) |
| PD0-PD7 | Port D | bus | Multiplexed AD0-AD7 to the optional external ROM, latched by a 74LS373 on ALE (SM p. 3-10) |
| AN0 (pin 34) | analogue | in | +24 V supply, divided down; used to set the head pulse width (SM p. 3-14) |
| AN1 (pin 35) | analogue | in | Head-drive thermistor (PTC); about 2.5 V at about 60 °C starts the cooling pause (SM p. 3-13) |
| AN2 (pin 36) | analogue | in | SW1, device 4 or 5 (schematic: SW1 between AN2 and 0 V, with a 4.7 k pull-up) |
| AN3 (pin 37) | analogue | in | SW2, 1/6 or 1/8 in (schematic: SW2 between AN3 and 0 V, with a 4.7 k pull-up) |
| RD (pin 44), ALE (pin 46) | control | out | External ROM /OE and address latch |
| RESET (pin 28) | — | in | From the reset circuit (power-on, low +5 V, bus RESET) |

Notes:

- The SM text says the two DIP switches are "SW1" and "SW2" (SM p. 3-9). The
  schematic draws them on AN2 and AN3 rather than on digital port pins, so
  they are read with the A/D converter. The exact sense (on = 0 V) and
  which position is 4 or 6 are not stated. **Uncertain.**
- Bus DATA is read on PC1 and pulled low by PF5 through the inverter. The
  CPU's serial receiver (RxD and SCK) can shift in bus bytes in hardware.
- CLK reaches the CPU both true (PC2/SCK) and inverted (INT1 and PC5).
- ATN goes only to PC3/INT2. Nothing in hardware acknowledges ATN: the
  firmware must pull DATA low itself when ATN falls.
- SRQ (pin 1) is not connected (schematic).

### 7.4 Head (SM p. 1-2, 3-1, 3-13 to 3-15, 7-1)

- 8 wires driven by 8 solenoids arranged in a circle, with guides at the
  nose. Each solenoid is about 33 Ω.

  Head connector J8: pins 8, 11, 3, 10 carry wires 1-4; pins 1, 9, 2, 7
  carry wires 5-8; pins 5 and 6 are the common HDRV (SM p. 3-13, 7-1).
- A wire fires when its PB bit is 0 while /HPLS (PC7) is low. HPLS also
  switches the driver ICs' supply, so the supply and ground sides of the
  solenoids are switched together (SM p. 3-13).
- **Pulse width** depends on the +24 V rail, measured on AN0. The SM's graph
  gives about 570 µs at +20 V, a standard 500 µs at +24 V, and about 430 µs
  at +28 V. The graph axis is labelled "MS", but the values must be µs
  (SM p. 3-14).

  The firing timing chart shows the head pulse about 2.8 ms into each
  motor-phase step, typically 500 µs long. **2.8 ms** is one step at
  360 pps (SM p. 3-15).
- Print timing is locked to the carriage stepper's drive pulses
  (SM p. 3-1).
- The print routine's interrupt does the following for each column
  (SM p. 1-15): read the column, clear its MSB, output it to the head, turn
  the head on, start a pulse-width timer, then turn the head off and clear
  the data.

### 7.5 Carriage and paper feed (SM p. 3-2 to 3-4, 3-11, 3-12)

- **Carriage (CR) motor**:
  - PM-type stepper with 2-2 phase excitation, driven by PA0-PA3.
  - **1/60 in per step**, at **360 pps**. At 6 steps per character that
    is 60 cps.
  - A character (pica, 1/10 in) is **6 steps**.
  - It runs on +24 V. When stopped it is held on +9 V, under /CRPLS (PC6).
  - It ramps over 8 pulses ("8-pulse slew up/down").
  - The carriage reverses when the phase sequence is run backwards.
  - Belt: MM310-3.2 timing belt, about 106 Ω per winding, red common.
- **Home position switch**: at the left end. Printing begins at the
  **24th pulse (dot) after the switch opens** (SM p. 1-3). The left margin
  is therefore 24 steps (0.4 in) after the switch releases.

  A home-switch closure during printing is an error, and the printer
  releases the bus.
- **Line feed (LF) motor**:
  - PM-type stepper with 2-2 phase excitation, driven by PA4-PA7.
  - **1/216 in per step**, at **200 pps**; **36 steps for 1/6 in**.
  - It ramps over 8 pulses ("8-pulse slew up/down") and holds by detent
    torque alone.
  - About 106 Ω per winding, green common.
  - Phase sequence for forward feed, in (B, A, /B, /A) order:
    1100 → 0110 → 0011 → 1001, each energising two adjacent phases
    (SM p. 3-11).
  - At 200 pps, 36 steps take 0.18 s plus ramping, which fits 4 lines/s.
    Bit-image feeds of 21 steps fit 5.6 lines/s.
- **Driver ICs**: Mitsubishi M54567 (or the second source Toshiba TD62308AP),
  a 4-channel driver with clamp diodes (SM p. 3-11, 3-12).
- **Ribbon**: driven by carriage travel through a spring clutch, advancing
  only on left-to-right moves (SM p. 3-4). Ribbon: cassette, 8 mm × 10 m,
  black fabric.
- **Printing direction** (SM p. 1-2): characters print bidirectionally by
  the shortest path. Bit image ("mark") printing is unidirectional,
  left to right, by the shortest path.

### 7.6 Which wire is idle

Characters and bit image use 7 dots vertically (UG p. 49; SM p. 1-2), and
the head has 8 wires on PB0-PB7. The manuals do not say which wire is
unused. The tables' empty 8th row (SM p. 1-16, 1-17) suggests the bottom
wire (wire 8, PB7) is idle. The flowchart's "MSB clear" step (SM p. 1-15)
fits that: bit 7 of a bit-image byte is cleared before the byte goes to
PB, so wire 8 never fires, and bits 0-6 drive wires 1-7, with bit 0 at the
top.

**Inference, not stated.** Confirm from the firmware.

### 7.7 Optional external ROM (SM p. 3-10, 3-11; schematic note)

- The board has an unpopulated footprint for a **2732 or 2764 EPROM (#3)**
  and a **74LS373 latch (#2)**. The schematic marks them
  "OPTION: 2732/64 and 74LS373".
- To fit them, add the two chips and change the jumpers. With the external
  ROM in use, MODE1 is pulled low (SM p. 3-10).
- The text says the external ROM can be "14K byte". That is probably a typo
  for 4K (a 2732) or 8K (a 2764). The address lines from the CPU reach A12,
  so at most 8 KB is addressed (SM p. 3-10).
- Wiring:
  - EPROM /CE is tied to 0 V, so the chip is always selected.
  - /OE comes from the CPU's RD.
  - A0-A7 come from the '373 latching PD0-PD7 on ALE.
  - A8-A12 come from PF0-PF4.
  - D0-D7 go to PD0-PD7.
- The text describes the external ROM as an alternative store for the
  control program ("can be used for the control"). It does not describe it
  as a character ROM.
- **No external ROM is fitted on the production board** described in this
  manual.
- On the µPD7811, MODE1 = 0 and MODE0 = 0 selects a mode with external
  memory. Which addresses then come from outside is a 7811 datasheet
  matter; the SM does not say. **Uncertain.**

### 7.8 What the 3,584-byte file (mps803.bin) is

Nothing in either manual describes a 3,584-byte ROM. Evidence from the SM
and from the file itself:

- The SM puts the character generator **inside** the µPD7811's 4 KB ROM
  (SM p. 3-6). The only external ROM is an unpopulated 2732/2764 option for
  program code.
- 3,584 = 512 × 7. Inspection of the file shows exactly that shape:
  - **512 glyphs of 7 bytes each**, one byte per row, top row first;
  - **bit 7 is the leftmost dot**, and only the top 5 or 6 bits are used,
    with bits 1-0 always zero;
  - glyphs 0-255 are the graphic set and 256-511 the business set, each
    indexed by the PETSCII code.

  For example, glyph $41 is 'A' and glyph $141 is 'a'. Glyph $61 is the
  spade, the same as glyph $C1, and glyph $1C1 is 'A'. $00-$20 and $80-$A0
  in each half are empty.
- That is **row-major**. A print-head character generator for a vertical
  7-wire head would naturally be stored **column-major**, one byte per dot
  column.
- Its '0' is unslashed, but the manuals' tables show a slashed zero.

  Together these suggest mps803.bin is **not a dump of a chip on the
  printer**. It looks like a software emulator's character file, laid out
  for screen-style rendering; VICE's MPS-803 emulation uses a 7 × 512
  table of this kind. Treat it as derived data, not ground truth.
- The 4 KB internal-ROM dump (mps803_78c11.bin) visibly contains
  column-style glyph data. There are runs like `xxxxxx`, `@@@@@@` and
  `U*U*U*`; the last is $55/$2A alternating, a checkerboard drawn column by
  column. That matches the SM: the real CG is in the internal ROM.

  This is from a quick look at the bytes only; the firmware analysis should
  confirm it.

### 7.9 Power supply and electrical details (SM p. 1-3, 3-16)

- The transformer gives AC 19 V and AC 9.5 V.
- **+24 V** comes from a bridge rectifier and 3300 µF capacitor and is
  unregulated: about 27 V with no load, about 24 V while self-testing.
- **+9 V** comes from a bridge and 3300 µF capacitor; it is the regulator's
  input and also the carriage holding supply.
- **+5 V** comes from a 7805 regulator.
- Fuses: 2.5 A on the 19 V winding and 1.0 A on the 9.5 V winding.
- Power use: 25 W or less while self-testing (SM p. 1-3). The UG gives
  30 W maximum and 8 W idle (UG p. 50).
- Specifications:
  - head life 20 million characters;
  - MTBF 4,000 hours;
  - line feed accuracy 4.23 ± 1.0 mm per 1/6 in, 42.33 ± 1.5 mm over
    10 lines (SM p. 1-4);
  - size 334 × 206 × 94 mm and about 3 kg (SM). The UG says
    330 × 190 × 70 mm and 2 kg.

---

## 8. Conflicts and points to check in the firmware

1. ESC POS range: 0-639 (UG p. 38) or 0-479 (SM p. 1-6).
2. Line spacing in bit-image mode: 9 lpi (UG p. 44) or 7/72 in (SM p. 1-8,
   UG p. 49, SM p. 1-2).
3. Buffer size: 90 bytes (UG p. 48) or 152 bytes (SM p. 1-9).
4. Whether LF ends quote mode. The SM says only CR does; the UG says end of
   line.
5. What happens to an SA other than 0 or 7.
6. What "POS/ESC POS right before BS, SO or SI is invalid" means.
7. Whether the margin wrap happens at once or waits for the next
   character, and the exact thresholds (475 for standard, 469 for double
   width, and SUB's garbled rule).
8. Which head wire (PB bit) is idle, and the bit-to-wire order.
9. The sense of the SW1 and SW2 switches as read on AN2 and AN3, and their
   voltage thresholds.
10. Power-on carriage moves: left then middle (SM p. 1-9, 3-9; UG p. 12), or
    right then left (SM p. 2-10).
11. The "33 ms max" interval in the ATN timing diagram (SM p. 3-7).
12. How the double-width glyph is made: each column doubled to 12 columns
    (UG p. 27), or each dot printed twice at a half step. The SM gives
    1/60 in steps only, so column doubling is the likely reading.
