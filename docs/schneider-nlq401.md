# Schneider NLQ401 and relatives: notes for a possible future model

Not modelled. These notes record what is known, from the CPCWiki page
<https://www.cpcwiki.eu/index.php/NLQ401>, in case Papyrium adds it later.

## The printer

The NLQ401 was Schneider's near letter quality printer for German
Schneider CPC computers, advertised in the CPC6128 manual; a tractor feed,
the SFT401, was sold separately. The hardware was made by Centronics
(the label reads Centronics Data Computer Corp., Model No. 3101) and sold
under other names.

## The Great Little Printer

The page "The Great Little Printer"
(<http://manuale-archive.keep.pl/files/The_Great_Little_Printer.html>)
says Centronics and Brother, working closely together, each sold two
editions of one printer under different names, and licensed it to
others:

- **Great Little Printer (GLP)**, Centronics model 3101: also the Brother
  M-1009 (with the M-1009X for MSX computers), the Commodore MPS-803 (a
  CBM serial interface and reworked controls), the **Schneider NLQ401
  ("with NLQ added")** and the Yamaha PN-101.
- **Great Little Printer II (GLP II)**, Centronics model 3102, with NLQ
  and an RS-232 interface as standard: also the **Brother M-1109**, the
  Sony PRN-M09 and the RCA VP2100.

The page's author owns a GLP II, "the Brother M-1109", and its DIP switch
tables agree with the M-1109's manual (`docs/brother-m1109.md`).

So the NLQ401 is a first-edition GLP, like the M-1009, not the M-1109,
which is the second edition. CPCWiki's page agrees on the first edition:

- **Centronics GLP 500**, reportedly the same printer.
- **Brother M1009**, the same hardware in a different case and colour,
  but without NLQ: Schneider's own EPROM is what added it.
- **Commodore MPS-803**, apparently from the same maker, with a CBM serial
  port instead of Centronics and only 7 pins used for text and graphics,
  though the head is the same 9-pin one.
- **Robotron 6313** (East German), different hardware with an
  NLQ401-compatible mode selected by DIP switch.

The two editions are different printers, the second adding NLQ and a
standard RS-232 interface: the M-1009 and the M-1109 are distinct models. Papyrium models only the
second edition, as `centronics-glp-ii`, with the M-1109, PRN-M09 and
VP2100 as its other badges. The first would be `centronics-glp` (Model
3101), with the M-1009 and the others as its badges; the NLQ401, with
Schneider's own firmware, would be a variant of it rather than a badge.

MAME's `nlq401` device takes this ROM. Its notes call the printer an OEM
version of a Centronics product, with the M1009's hardware "but not the
firmware", and the device is a skeleton: it does not yet print.

## Hardware

- A NEC uPD7811G processor with its internal ROM disabled, so it runs as a
  ROM-less uPD7810; the service manual allows either part.
- A 16K EPROM at 0000h-3FFFh; the CPU uses 14-bit external addresses, the
  top two bits of port F serving as I/O.
- An optional RS-232 interface (25-pin D-sub, 75188/75189 line drivers),
  which may need different firmware.

## Sources on CPCWiki

- German user and service manuals, and the uPD7811G and uPD78C11A data
  sheets.
- A ROM image of the 16K EPROM (Rev 004). It does not include the 4K ROM
  inside the CPU, which may hold part of the firmware or character data.
- A 1985 review in CPC Schneider International (March, page 24, German),
  which the wiki notes is partly misleading.

## If Papyrium models it

- Its character set would come from the ROM image unless reconstructed from
  printed output; `CLAUDE.md` allows only the latter, so using the ROM
  needs Rob's decision.
- It would be built on an M-1009 (first-edition GLP) model, which needs
  a source of its own: no M-1009 manual is to hand.
- Its draft characters may be the first edition's, shared with the
  M-1009, and so perhaps the M-1109's too; its NLQ is Schneider's own. A
  local comparison against `m1109-draft` and `m1109-nlq` would show how
  far they agree.
- Its command set is unknown here; the user manual would be the reference.

## Behaviour, from the German user manual

Restated in English from the Schneider NLQ 401 Bedienungshandbuch (German).
Page numbers are the manual's printed page numbers ("p. 21"), not PDF pages.
Printed page p corresponds to PDF page ⌊p/2⌋+4 (e.g. pp. 13/14 are PDF page 10).
"Uncertain" marks readings the scan does not settle, or places where the
manual contradicts itself or is ambiguous. Facts already gathered elsewhere
(command summary p. 12, DIP switch table, code tables pp. 54-57, technical
data p. 58) are only repeated where needed for a cross-reference.

### 1. General rules for codes (pp. 13-14)

- The command list (pp. 12-13) frames the commands as data sent from the host, e.g. BASIC `PRINT #8` (p. 13).
- An ESC followed by an undefined code: the printer discards both the ESC and that code (p. 13).
- ESC is never used to extend the control characters themselves; ESC prefixes
  only printable codes (p. 13). (This note doesn't say what ESC plus a control
  code does. The "undefined code" rule above presumably applies.)
- In the summary, `n`/`n1…` are user-supplied values. For some commands n is
  a data length (bit image) and for others a set/clear switch (underline) (p. 13).
- The manual repeatedly calls the receive buffer the "print buffer"
  (Pufferspeicher/Druckpufferspeicher). In practice it is a **line buffer**:
  CR, LF, FF, ESC J, ESC < and the bit-image commands each "print all data
  stored in the printer's buffer" before doing their own action (pp. 14-17, 47-48).
  BUSY is held while printing, moving the carriage, feeding paper and when the
  buffer is full (p. 67), so the host can't send data while a line prints.

### 2. Print execution and format codes (section 4.2.1)

#### CR, 0x0D (p. 14)
- Prints everything in the buffer.
- Whether a line feed follows depends on AUTO FEED XT, i.e. DIP switch 7
  (ON = CR prints and feeds, OFF = CR prints only; factory setting OFF) (p. 14, DIP table p. 5).
  Interface pin 14 AUTO FEED XT held low also gives an automatic LF after
  printing (p. 65).
- **CR cancels SO enlarged mode** (p. 14).
- Example (p. 14): "CARRIAGE " "RETURN" sent without a CR join on one line. Text, then CR LF, then text, start a new line.

#### LF, 0x0A (p. 15)
- Prints the buffer, then feeds the paper one line.
- Power-on line spacing is 1/6" (DIP 2: ON = 1/8", OFF = 1/6"; factory OFF) (p. 15, p. 5).
- **LF cancels SO enlarged mode** (p. 15).

#### VT, 0x0B (p. 19)
- Exactly the same as LF. There is no vertical tab table. Example: two VTs give two line feeds (p. 19).
- It also cancels SO (p. 29: SO lasts until "LF or VT").

#### FF, 0x0C (p. 16)
- Prints the buffer, then moves to the top of the next form.
- The top of form is set at power on, at reset (INIT), or when ESC C is received.
  ESC C sets the form length (p. 16).
- Power-on form length is 11" (DIP 1: ON = 11", OFF = 12"; factory ON) (p. 16, p. 5).
  Note that p. 20 also says ESC C's power-on value is 66 lines.
- **FF cancels SO enlarged mode** (p. 16). Example: after `ESC C 5`, SO text,
  LF, FF, text "ENLARGED MODE CLEARED BY FF CODE" prints at normal width (p. 16).

#### ESC J n: n/216" feed after printing (p. 17)
- Prints the buffer, then feeds n/216".
- One-shot: it doesn't change the line spacing. The manual says the command is "cleared" after the feed (p. 17).
- Valid for 0 ≤ n ≤ 127. With n = 0 there is no feed after printing (p. 17).
  What happens for n > 127 isn't stated, but a 7-bit interface can't send it.
- **ESC J does not cancel SO** (p. 17, and p. 29 "LF or VT (except ESC J)").
- I measured the example on p. 17 (ESC J 10/50/90, each followed by text and a BASIC CR LF).
  The gap between printed lines is LF (36/216") + n/216", to scale. So ESC J
  with an empty buffer feeds at once, and the normal LF adds to it.

#### HT, 0x09 (p. 18)
- Moves the print position to the next tab stop set by ESC D.
- At power on a stop is set every 8 columns (p. 18).
- If no stop is set, HT is ignored (p. 21).
- If the text already printed reaches the next stop, printing continues from the stop after that (p. 21).
- I couldn't verify from the scan how many columns the example on p. 18 skips (two consecutive HTs).

#### ESC D n1 … nk NUL: set horizontal tabs (p. 21)
- Up to 28 stops. The list ends with NUL, or with the 28th value itself, with no NUL needed (p. 21).
  Everything after the NUL (or n28) is taken as print data or other control codes.
- Sets a tab at the ni-th print position (column) for each i, and **clears all previous stops** (p. 21).
- Each value must be greater than the one before. A value that isn't is invalid (p. 21).
  The manual doesn't say whether the remaining values are still used. Uncertain.
- Valid range 1 ≤ ni ≤ 127. A value outside it is invalid, "i.e. any stops set
  before stay in force" (p. 21). This seems to mean an out-of-range value leaves the
  old table untouched, not just that one entry is ignored. Uncertain.
- Tabs can be set up to column 127. If printing is asked to go past 127 columns,
  the carriage returns and the full line prints automatically, and the manual adds
  that "HT then acts like LF" (p. 21). Odd wording, uncertain: an HT past the last
  usable column apparently forces a line-full print and new line.
- Columns are presumably counted in current character widths. 1-based or 0-based
  isn't stated. In the example, `ESC D 5 25 NUL` followed by "HT-1" HT "HT-2" HT "HT-3"
  prints the three labels spread across the line (p. 21).

#### ESC C n: form length in lines (p. 20)
- Sets the form length to n lines. Power-on value 66 lines (p. 20).
- Valid for 1 ≤ n ≤ 127 (p. 20).
- **The top of form becomes the current position where the command arrives** (p. 20).
- **Cancels skip-over-perforation (ESC N)** (p. 20, p. 22).
- Not stated: whether the length is held as lines or turned into an absolute
  distance at the current spacing. The ESC C NUL n note implies the inch form is
  "absolute" in contrast. Uncertain.

#### ESC C NUL n: form length in inches (p. 20)
- Form length n inches, valid for 1 ≤ n ≤ 22 (p. 20).
- Sets the top of form here, and cancels skip-perforation (p. 20).
- Held as an absolute value, so later changes to line spacing don't change it (p. 20).
- Example: `ESC C 5`, `ESC N 1`, then five lines prints 4 lines, skips one, and continues on the next "page" (p. 20, 22, 23).

#### ESC N n: skip over perforation (p. 22)
- Skips the last n lines of each page. Valid for 1 ≤ n ≤ 127 (p. 22).
- Even with n in range, the skip can't extend the form length set by ESC C.
  When printing crosses the skip boundary, the paper moves to the first print
  line of the next page (p. 22).
- Cancelled by ESC C (both forms) and by ESC O (p. 22-23).
- DIP 5 "Zeilenüberspringung (1 Zoll)": ON = a 1" skip is in force at power on.
  Factory OFF (p. 5).

#### ESC O: cancel skip over perforation (p. 23)
- Example: after ESC O, "---CLEAR SKIP---" lines run straight across the page boundary (p. 23).

#### ESC 0: 1/8" spacing (p. 24)
- Sets the line spacing to 1/8" **and performs a line feed** (p. 24, "und bewirkt Zeilenvorschub").
  The text also says that "the line feed following this command is 1/8"".
- I measured the example (p. 24): after "* 1/8 PITCH SET *" CHR$(10) and then ESC 0, the gap to
  the next line is about 7/72" + 1/8". So ESC 0 does feed immediately. **Not Epson behaviour.**

#### ESC 1: 7/72" spacing (p. 25)
- Sets 7/72" spacing **and performs a line feed** (p. 25). The example's 7/72" lines
  overlap their 7-dot-high characters closely (p. 25).

#### ESC 3 n: n/216" spacing (p. 26)
- Sets n/216" spacing **and performs a line feed**. Valid for 1 ≤ n ≤ 127 (p. 26).
  Out of range isn't described. Presumably ignored, as for ESC A.

#### ESC A n: set n/72" spacing (p. 27)
- Sets the line spacing to n/72" (summary p. 12: "set command" for n/72").
- Valid for 1 ≤ n ≤ 85. **Out of range: the command is ignored and the previous spacing kept** (p. 27).
- Power-on n = 12 (1/6") (p. 27).
- Every example follows ESC A n with ESC 2 (p. 28), and ESC 2's text says the current spacing changes
  to the ESC A value "when ESC 2 is received". This is the old MX-80 style:
  **ESC A stores a value and ESC 2 applies it.** Whether ESC A alone also changes the spacing is uncertain.
  The p. 27 heading says "sets the spacing to n/72"".

#### ESC 2: execute n/72" spacing (p. 27)
- Applies the value from the latest ESC A (summary p. 12: "Durchführungsbefehl", execute command).
- Even if another command changed the spacing after ESC A, ESC 2 returns to the last ESC A value (p. 27).
- **If no ESC A has come before, ESC 2 sets 1/6"** (p. 27).
- Example (p. 28): `ESC A n ESC 0 ESC 2` gives n/72" lines (10, 15, 20, then DATA 8, 9, 12 or similar, partly illegible).
  `ESC A n ESC 0` alone gives 1/8" lines.
- Whether ESC 2 also does an immediate line feed, as ESC 0/1/3 do, isn't stated. Uncertain.

### 3. Print-mode codes (section 4.2.2)

#### SO, 0x0E: enlarged (double width) (p. 29)
- Enlarged lasts until any of these (p. 29):
  - CR, DC4, CAN, or ESC W with an even n arrives;
  - a line feed through LF or VT (but **not** ESC J);
  - an automatic line feed because the buffer is full.
- FF also cancels it (p. 16).
- Example: "DOT" normal, SO " MATRIX" DC4, " PRINTER" CR LF. Only MATRIX is wide (p. 29).

#### SI, 0x0F: condensed (p. 30)
- Condensed (17 cpi, 3.5 dots per character, p. 49) until DC2 arrives (p. 30).
- Together with SO or ESC W it gives condensed enlarged characters at 8.5 cpi (p. 30).
- **With emphasized (ESC E) active, SI is ignored, because emphasized has priority** (p. 30, p. 33).
  Example (p. 30): emphasized "IMPACT", then SI "DOT MATRIX" DC2 with no emphasis,
  then emphasized + SO "PRINTER".
- Not cancelled by CR or LF. Only DC2 is listed (p. 30).

#### DC4, 0x14: cancel enlarged (p. 31)
- Cancels SO enlarged (p. 31). The manual doesn't say whether it also cancels ESC W.
  Its text names SO only. Uncertain.

#### DC2, 0x12: cancel condensed (p. 31)
- Cancels SI condensed (p. 31). Example output: condensed "IMPACT", then
  emphasized+enlarged "DOT MATRIX", then emphasized "PRINTER".

#### ESC - n: underline on/off (p. 32)
- Only bit 0 of n counts: 0 = off, 1 = on. All other bits are ignored (p. 32).
- Wording: "after this command the data in the buffer are printed and underlined" (p. 32).
  This most likely just means "data from now on print underlined". It doesn't seem to force a buffer print. Uncertain.
- **Graphics characters 129-255 selected with ESC = cannot be underlined** (p. 32).
- Mixes with every other mode except bit image (p. 32).
- **Only characters between non-space characters are underlined.** Leading and
  trailing spaces are not, spaces between characters are. HT is treated the same way:
  with SPC "A" SPC "B" SPC, the underline runs from A to B, taking in the middle
  space but not the outer ones. HT "A" HT "B" HT behaves the same (p. 32).
- Example (p. 32): underlined "Elementary"; then SI " Junior " DC2 with underline off;
  then ESC E with underline on, "High" bold and underlined. The underline sits under the text and covers the full cell width.
- Works in NLQ (p. 45-46, p. 53).

#### ESC E: emphasized (p. 33)
- Emphasized on. **Not cancelled when other modes are mixed in** (p. 33).
- **Has priority over SI condensed. SI is ignored while emphasized** (p. 33).
- Character width doesn't change: emphasized is 6 dots like normal (p. 49). The
  example shows heavier strokes at normal pitch, made by doubling each dot horizontally.
- Example (p. 33): three rows of "()" in emphasized, then three in normal.

#### ESC F: cancel emphasized (p. 34)
- Example (p. 34): `ESC E "DOT MATRIX " ESC F "PRINTER" LF`, then SO "DOT " ESC E "MATRIX " ESC F "PRINTER" DC4 CR LF.
  The second line is all double width, with MATRIX also bold.

#### ESC G: double strike (p. 35)
- Each character is printed twice, with the second pass **1/216" lower** (p. 35).
- Mixes with other modes (p. 35).
- **With super/subscript, the script wins and ESC G is ignored** (p. 35). The script itself is
  already two passes 1/216" apart (p. 37). See section 5 priorities.

#### ESC H: cancel double strike (p. 36)

#### ESC S n: superscript / subscript (p. 37)
- Bit 0 of n: 0 = superscript, 1 = subscript (p. 37). The text says even/odd, so higher bits don't matter.
- The text prints in the upper or lower half of the character cell (p. 37). The character
  height is 1.2 mm, the width "variable" (p. 58).
- **A line holding scripts is printed in two unidirectional passes with a 1/216" feed between them** (p. 37, p. 58).
- Mixes with other modes. Mixed modes don't cancel it, and it doesn't cancel them (p. 37).
- **With double strike, the double strike is not done together with the script printing** (p. 37).
  Read with p. 35 and p. 53: scripts override double strike.
- Superscript and subscript are mutually exclusive. Setting one clears the other (p. 53).
- Examples: `ESC S 0` with SI for exponents in "F(X)=aX⁴+bX³+cX²+dX+e", the main text
  emphasized and the scripts not (p. 37). `ESC S 1` with SI for "Ba(OH)₂ + H₂SO₄ -> BaSO₄ + 2H₂O" (p. 38).
- The ESC T example (p. 39) shows normal-width scripts printed in a widely spaced light
  face, and condensed scripts denser and bolder-looking.

#### ESC T: cancel super/subscript (p. 39)

#### ESC W n: double width on/off (p. 40)
- Bit 0: 1 = on, 0 = off (p. 40).
- Stays on until ESC W with bit 0 = 0. **CR doesn't cancel it** (p. 40). Unlike SO, it is not one-line.
- **ESC W cancels SO enlarged** (p. 40). (Both ESC W 1 and ESC W 0 do, by the wording.)
- Example: "DOUBLE WIDTH " normal, ESC W 1, ESC E "ENLARGED " wide and bold, ESC W 0 "PRINTING" bold at normal width (p. 40).

#### ESC 7: character set 1 (p. 41)
- Selects set 1 (ASCII: @ [ \ ] { | } ~ at 64, 91-93, 123-126) (p. 41).

#### ESC 6: character set 2 (p. 42)
- Selects set 2 (German: § Ä Ö Ü ä ö ü ß at those codes) (p. 41-42).
- "Issued automatically at power on", subject to DIP 3 (ON = set 2, OFF = set 1; factory ON) (p. 42, p. 5).
- Example output (p. 42): in set 2, code 94 is still ^, 95 _, 96 ` (only the 8 codes change).

#### ESC =: graphics (shift) character set (p. 43)
- After ESC =, each received code 0-127 prints as the character 128-255 from the code tables (p. 43).
- The interface is 7-bit. ESC = makes the printer treat bit 8 as 1 internally (p. 43).
- **Cancelled by NUL (0x00)** (p. 43).
- **Important example detail (p. 43):** the "ASCII -> GRAPHIC" demo sends ESC = and then
  bytes X+I for I = 0..31 with X = 16, 32, 64, 94, ended by NUL. With X = 16 that covers
  0x10-0x2F, and the printed first row shows the graphics for 144-175. So **while ESC = is active,
  the control codes 0x10-0x1F (DC2, DC4, CAN, ESC 0x1B, …) print as graphics 144-159
  instead of acting as controls.** Codes 0x01-0x0F weren't tested (CR and LF in that range
  presumably still work). Uncertain.
- The range X = 94 covers 0x5E-0x7D → 222-253 (p. 43).
- Graphics run from 129 to 255 (127 characters; 128 would be the NUL terminator) (p. 32, p. 58, p. 68).
- Graphics characters are printed unidirectionally (p. 58), can't be underlined (p. 32),
  and in NLQ are printed double strike (p. 45).

#### ESC U n: unidirectional on/off (p. 44)
- Bit 0: 1 = unidirectional (left to right), 0 = bidirectional (p. 44).
- Power-on default bidirectional (p. 44).
- Even in bidirectional mode, bit image, graphics characters and super/subscript
  are always printed unidirectionally (p. 50, p. 58).

#### ESC I n: NLQ select (p. 45)
- **n = 3 selects NLQ, n = 1 selects draft** (p. 45). Other values aren't described. Uncertain:
  possibly bit 1 is tested.
- NLQ mixes with normal, enlarged (SO/ESC W) and underline. Other modes are ignored
  while NLQ is on, because NLQ has priority (p. 45).
- Characters NLQ doesn't contain are printed double strike in draft form (p. 45).
- Both examples end by sending `ESC CHR$(3)`, an undefined ESC code, which by p. 13
  is simply discarded. This looks like a misprint.

#### ESC x n: NLQ select (p. 46)
- **n = 1 selects NLQ, n = 0 draft** (p. 46). The other rules are the same as ESC I.
- DIP 4 "NLQ": ON = NLQ in force at power on (factory ON!) (p. 5). So by default the printer starts in NLQ.

### 4. Other codes (section 4.2.3)

#### CAN, 0x18 (p. 47)
- Clears the data in the print buffer (p. 47).
- **It clears no control settings except SO** (p. 47). Enlarged SO is cancelled, and all other modes stay.

#### ESC 8: ignore paper end (p. 47)
- The printer ignores paper empty and can stay ON LINE and print to the end of the paper.
- The paper-out warning isn't fully disabled: **the ERROR lamp still lights and the PE signal is still raised** (p. 47).
  With ESC 8 in force the ON LINE key also stays usable at PE (p. 11).

#### ESC 9: honour paper end again (p. 47)
- Cancels ESC 8. Paper-out detection is fully in force again (p. 47).

#### ESC <: carriage home (p. 47)
- Prints the buffer, then moves the carriage to its home position (p. 47).
- **Data printed after the homing continue at the position directly after the data printed before** (p. 47).
  It is a mechanical re-homing that keeps the logical column, not a carriage return.
- Its purpose is to prevent accumulated horizontal position errors (p. 47).
- **This differs from Epson, where ESC < is one-line unidirectional printing.**

### 5. Bit image (section 4.3, pp. 48-52)

#### Common rules (ESC K, p. 48-49, and applied to the others "mutatis mutandis")
- **Pin mapping (p. 49): only 7 pins are used.** Pin 1 (top) and pin 9 (bottom) are not
  used for bit image. Bit b7 (MSB, value 64) drives pin 2, down to b1 (LSB, value 1)
  on pin 8. The diagram labels the bits b1..b7. Pin 9 "is not used for bit image"
  is stated explicitly, and pin 1 is drawn as an unused open circle.
- **"n must not exceed 127"** (pp. 48, 50, 51, 52): each data byte is 0-127, 7 bits.
- n1 + 256 × n2 = number of data columns that follow. n1 is the low byte, n2 the high byte (p. 48).
- Mode is entered **after the buffer contents have been printed** (p. 48). Yet text and
  bit image can share a line, and different bit-image modes can be mixed in one line
  (p. 48, p. 3). Uncertain how both hold together. Probably the text so far is laid out
  into the line image first.
- The previously selected print mode is not cancelled (p. 48).
- Once the n1/n2 columns have been received, the bytes that follow print as text again (p. 48).
- Bit image always prints unidirectionally (p. 48, p. 58).
- Underline doesn't apply to bit image (p. 32).
- Line capacity: at most 480 columns per line in single density. **Data beyond 480 dot
  positions are ignored** (p. 48). Text uses up the same space: 6 dots per normal or emphasized
  character (12 enlarged), 3.5 dots per condensed one (7 enlarged). For example, 10 normal characters
  leave 480 - 60 = 420 columns for graphics (p. 49).
- The example (pp. 48-52) sends `ESC K 20 0` and 20 bytes of 2^J - 1 for J = 1..7,
  seven times per line, five lines. The result is a ramp that grows upward from the
  bottom pin (value 1 = lowest dot), confirming LSB = bottom.

#### ESC K n1 n2: single density (p. 48)
- 1 ≤ n1 + 256n2 ≤ 480. 480 columns per 8" line, i.e. 60 dpi (p. 48, p. 3, p. 58).
- Excess columns beyond the line are ignored (p. 48). Out-of-range counts aren't described for ESC K.

#### ESC L n1 n2: double density (p. 50)
- 1 ≤ count ≤ 960. **If the count is out of range the command is invalid** (p. 50).
- Other rules as ESC K, with 960 in place of 480 (p. 50). 120 dpi.

#### ESC Y n1 n2: double speed, double density (p. 51)
- 1 ≤ count ≤ 960. Out of range makes the command invalid (p. 51).
- **Adjacent dots are not printed** (p. 51). Consecutive dots in a row are dropped, the usual high-speed restriction.
- More than 960 columns: the excess is ignored, because "line full" occurs at 960 (p. 51).

#### ESC Z n1 n2: quadruple density (p. 52)
- 1 ≤ count ≤ 1920. Other rules as K/L with 1920 (p. 52). 240 dpi.
- The manual doesn't mention an adjacent-dot restriction for ESC Z (unlike Epson's ESC Z).

### 6. Mixing print modes (section 4.4, p. 53)

The six possible combinations ("O" = possible):

| Mode | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Normal | O | O | | | | |
| Condensed | | | O | O | | |
| Emphasized | | | | | O | O |
| Double strike | O | | O | | O | |
| Super/subscript | | O | | O | | O |
| Enlarged | O | O | O | O | O | O |
| Underline | O | O | O | O | O | O |

So a character is {normal | condensed | emphasized} × {double strike | script} ×
enlarged? × underline? (p. 53).

Notes (p. 53):
1. If two modes in the same group are selected, the combination further right wins,
   because there is a priority order. Examples: combination 1 plus scripts → 2;
   combination 2 plus condensed → 3; combination 4 plus double strike → no change.
2. Priority order: **Normal < Condensed < Emphasized** and **Double strike < Scripts**.
3. If modes that can't be mixed are selected together, the printer prints in the mode with
   priority. "Setting one of the two cancels the other automatically" (p. 53).
   **This contradicts** ESC E ("not cancelled when mixed", p. 33), ESC S ("other modes
   don't cancel it", p. 37) and the ESC G/SI texts ("ignored", not "cancelled").
   The p. 53 note 1 example (4 + double strike → no change) fits "flag kept but overridden".
   The NLQ paragraph also says only internal flags are set or reset. Likely behaviour: each
   mode keeps its own flag, and priority picks what prints. Uncertain; check against the firmware.
4. Superscript and subscript are mutually exclusive. Setting one cancels the other.

- All the circled modes can be used within the same line (p. 53). The introduction says
  "six different print modes can be mixed within a single line" (p. 3).
- **NLQ**: mixes with normal, enlarged and underline. Other modes (condensed, emphasized,
  double strike, scripts) are ignored under NLQ. Their command **only sets or clears the
  internal flag** for the ignored mode, so it takes effect when NLQ is turned off (p. 53).

### 7. Front panel, self test, hex dump, paper out (pp. 9-11)

#### Panel (p. 9)
- Lamps: POWER (red, lit when the power is on); ERROR (red, **lit when there is no paper,
  flashing on a motor fault**); ON LINE (green, printer connected to the host and ready).
- **At power on the printer comes up ON LINE**, ready to receive (p. 9).
- ON LINE key: toggles ON LINE / OFF LINE on each press (p. 9). The interface appendix calls it the SELECT key (p. 67).
- LINE FEED key: one press feeds one line, holding it feeds continuously. **Works only OFF LINE** (p. 9).
  The setup text tells the user to press LINE FEED once after loading paper, with the printer disconnected
  from the computer, "so the specified spacing between the first and second line is assured" (p. 8, p. 60).
- There is no form-feed key and no top-of-form key (only ON LINE and LINE FEED).

#### Self test (p. 10)
- Hold LINE FEED while switching on. Runs OFF LINE (p. 10).
- Prints every character in the ROM. The sample is the familiar rolling ASCII pattern:
  each line starts one character later, codes 32-126 (p. 10).
- **Ends only by switching off or when the paper runs out** (p. 10).

#### Hex dump (p. 11)
- Hold LINE FEED **and** ON LINE while switching on (p. 10-11).
- Received data are printed in hexadecimal. **The dump starts only when the buffer is full**
  (p. 11). To dump before the buffer fills, press ON LINE to go OFF LINE (p. 11).
- **Ends only by switching off and on again** (p. 11).
- The example (a BASIC line sending text and CHR$ codes) and its hex output are too garbled
  in the scan to read the layout (bytes per line, whether an ASCII column is printed).
  Uncertain. The OCR shows pairs like "44 55 40 50 … 0A", i.e. space-separated hex pairs.

#### Carriage home at power on (p. 11)
- The carriage moves to its home position at power on (p. 11).

#### Paper out, PE (p. 11)
- At paper end the ERROR lamp lights and the printer goes OFF LINE. **The ON LINE key is
  disabled until PE clears** (p. 11).
- After ESC 8, the ON LINE key is not disabled (p. 11).
- **After the paper end is detected, printing continues for about another 1/2"**, i.e. three more
  lines at 1/6", before printing stops automatically (p. 11).

### 8. DIP switches (p. 5): behaviour notes beyond the table

- SW6 "Drucken bei vollem Puffer: Mit LF / Ohne LF" (print when buffer full; ON = with LF,
  OFF = without; factory ON). When the line buffer fills (a full line of characters), the printer
  prints it automatically. This switch chooses whether that automatic print also feeds a line (ON)
  or only returns the carriage (OFF) (p. 5). The SO text calls this "an automatic line feed because
  the buffer is full", which cancels SO (p. 29).
- SW7 CR (AUTO FEED XT): ON = CR prints with LF. Factory OFF (p. 5).
- SW8 SLCT IN: ON = held selected (fixed). Factory ON (p. 5).
- Factory settings as printed: 1 ON (11"), 2 OFF (1/6"), 3 ON (set 2), 4 ON (NLQ!), 5 OFF, 6 ON, 7 OFF, 8 ON (p. 5).

### 9. Power-on state (gathered)

- ON LINE (p. 9); carriage homed (p. 11).
- Line spacing 1/6" (DIP 2), ESC A value 12 (p. 15, p. 27).
- Form length 11" or 12" (DIP 1); ESC C says 66 lines. Top of form = the position at power on (p. 16, p. 20).
- Skip perforation per DIP 5 (1") (p. 5).
- Tabs every 8 columns (p. 18).
- Character set per DIP 3 (set 2 factory) (p. 42).
- NLQ per DIP 4 (on, factory) (p. 5).
- Bidirectional (p. 44).
- INIT (pin 31) low returns the printer to the power-on state and clears the buffer (p. 65).
  The pulse is ≥ 25 µs or ms (illegible). Busy may last up to about 3.5 s after it (timing diagram, p. 66). Uncertain.

### 10. Interface appendix E (pp. 64-67): behaviour points

- Centronics parallel, 36-pin. DATA 1-8 are listed, but the printer takes 7-bit data (p. 43).
  Whether DATA 8 is ignored isn't stated.
- STROBE: data read on the strobe edge. ACKNLG pulse about 6 µs. BUSY about 350 µs typical per
  character (p. 66; timing values partly illegible).
- PE goes high when the paper runs low/out (p. 65).
- AUTO FEED XT low → LF after each printed line (p. 65).
- FAULT goes low on a fault or when the printer is off line (p. 65).
- SLCT lamp/state: set by the SELECT key on or power on; reset by PE, abnormal motor operation, or the SELECT key off (p. 67).
- BUSY: set when off line, at PE, buffer full, printing, carriage moving, paper feeding,
  and during data input. Reset by going on line or by PE clearing (p. 67).
- FAULT: set at PE or SELECT off. Reset by SELECT on, PE cleared, or power on/off (p. 67).

### 11. Technical data points that matter for simulation (p. 58)

- Bidirectional logic-seeking for normal, enlarged, condensed and emphasized.
  Super/subscript use two unidirectional passes. **Bit image and graphics characters are unidirectional only.**
- Character sizes: normal 2.4 × 2.0 mm (H × W); enlarged 2.4 × 4.0; condensed 2.4 × 1.2;
  condensed enlarged 2.4 × 2.4; super/subscript 1.2 mm high, width variable;
  **graphics characters 2.8 × 2.4 mm** (taller and wider than text: 8 rows × 6 full dots, filling the 1/10" cell).
- Matrix: normal characters "9 × 9 dot grid (4 half dots)"; graphics characters 8 × 6;
  bit image 8 × 480 / 8 × 960 / 8 × 1920. These say 8 rows, but section 5 gives 7 usable pins.
  Uncertain: maybe pin 1 is counted with no data bit.
- Dot pitch 1/60" horizontal, 1/72" vertical.
- Spacing 1/6", 1/8" or programmed n/216".
- 80 cpl (10 cpi), 40 (5), 132 (17 cpi; 3.5 dots per character = 17.14 cpi), 66 (8.5 cpi).
- 50 cps; 9 pins; original + 2 copies.
- Character set: 96 ASCII, 8 German, 127 graphics. The introduction mentions 104 NLQ characters (p. 3).
  That is 96 + 8 = 104: NLQ covers ASCII and German only, no graphics.
- Paper width: single sheets A4 8.3" or letter 8.5". Tractor option 4"-10".

### 12. Dot patterns, appendix F (pp. 68-69)

#### Draft and graphics (p. 68)
- Each pattern is drawn on a grid of **10 columns × 8 rows of cells**. Dots sit on the grid
  **intersections**: 11 horizontal positions and 9 vertical positions (one per pin).
- **Horizontal positions are half-dot steps (1/120")**, so the 11 positions span 5½ full dots of a
  6-dot (12 half-step) cell. A text dot can sit on any half step. This is the "9 × 9 with half dots" of p. 58:
  characters use half-dot positions horizontally, with the usual rule that adjacent half-dot
  positions in a row aren't both struck. Graphics use full-dot steps only.
- Character placement as drawn:
  - "!" (33) uses the top rows (it starts on the top line, pin 1).
  - Underscore "_" (95) is a row of 5 dots on the **bottom line (pin 9)**, at full-dot spacing.
  - Lowercase descenders (g, j, p, q, y) go below the baseline to pin 9.
  - Capitals run from the top line down to about the 7th/8th position.
  So text uses pins 1-9 with descenders, not shifted down a pin as on the Epson FX.
- **Graphics 129-255 use 6 full-dot columns at full-dot spacing across all 11 positions
  (0, 2, 4, … 10) and 8 rows.** For example 208 is two solid rows of 6 dots at the top, and 144 is a centred
  2 × 2 dot block. Blocks and lines meet the neighbouring cells, so graphics join across characters
  and between lines at 8/72" (graphics are 2.8 mm high).
- Graphic 207 is a staggered checkerboard (shading). 216-223 are further shading patterns and
  stippled shapes (p. 68).
- Character set 1's alternates for 64, 91, 92, 93, 123, 124, 125, 126 (@ [ \ ] { | } ~) are drawn
  in a separate bottom row. The main chart shows set 2's § Ä Ö Ü ä ö ü ß in those places (p. 68).
- Graphics 129-255 seen on p. 68 include block elements (129-143: quarter and half blocks),
  box-drawing lines (145-159), accented and special characters (£, ©, ¶, fractions ¼ ½ ¾, ±, ÷,
  ¬, ¿, ¡ around 160-176), Greek letters (α β γ δ ε θ λ μ π σ φ Σ Ω around 177-191),
  diagonals and arcs (192-206), shading (207, 216-219), card suits and faces (220-233),
  arrows (240-247) and stick figures (248-255). Exact glyph identities come from the code tables (pp. 54-55).

#### NLQ (p. 69)
- NLQ patterns are shown for 33-126 (set 2's German characters in the main grid) and for
  set 1's alternates 64, 91-93, 123-126 (p. 69). **There are no NLQ graphics characters**, consistent with
  "characters not available in NLQ are printed double strike" (p. 45).
- The NLQ face is a serif design (Courier-like): slab-serifed capitals, serifed lowercase, open
  4, "a" with a tail (p. 69, and the ESC x sample on p. 46).
- The NLQ grid is visibly finer than the draft grid, but **the scan is too coarse to count its
  rows and columns reliably**. Uncertain. It looks like the same cell outline with denser lines, consistent with
  two passes offset vertically by 1/216" or half a dot, as NLQ on 9-pin printers usually works. That is
  not stated in the manual.

### 13. Troubleshooting and care (p. 59)

- Doesn't work at all: no power. Doesn't print although powered and data sent: cable not connected,
  or printer not ON LINE (press ON LINE). Ribbon not advancing: cassette wrongly fitted (p. 59).
  Nothing about behaviour beyond this.

### 14. Other notes

- The introduction (p. 3) claims the printer can program automatic line-spacing change, line skipping,
  switching between character sets, and between normal and other modes. It also claims
  "user-programmable character sets built from 8-bit images", which **probably refers to bit-image
  graphics**. No download-character command exists in the command list (p. 12). Uncertain wording.
- Bit-image density in the introduction: 480 / 960 / 1920 dots per 8" line (p. 3).
