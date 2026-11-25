# Commodore MPS-803 firmware

What Papyrium has learnt from the Commodore MPS-803's firmware: the 4K
internal mask ROM of its NEC uPD78C11 (`mps803_78c11.bin`, SHA-1
69ee52b09d87ac3c0a5105a4f0af1e862d2a5814). The ROM is kept uncommitted in
`docs/local/commodore-mps-803/`, beside the user's guide (UG) and the 1987
service manual (SM), whose account of the printer is
`docs/commodore-mps-803.md`. This note restates what the program shows,
in our own words. The tools are in `tools/mps803-rom/`; the map
`tools/mps803-rom/mps803-map.txt` names every routine below, and the
annotated listing it gives is
`docs/local/commodore-mps-803/mps803_78c11.dis`. The character generator
is dumped, with both character sets' code tables, in
`docs/local/commodore-mps-803/mps803-characters.txt`.

Addresses written `$....` are CPU addresses, which here are also offsets in
the ROM. `VV:xx` is RAM at `$FFxx` (the working-register page is $FF).

The program uses two uPD7810 tricks to read past. Skips: a test such as
`OFFIW` skips the next instruction when its condition holds, and many
routines return with `RETS`, skipping the instruction after their call,
as a second outcome. And the overlay rule: of consecutive `MVI A`
instructions only the first executes (likewise consecutive `LXI HL`), so a
run of them is a table of entry points; `text_line_feed` ($0450) chooses
its line feed this way.

## Memory and vectors

- **ROM** $0000-$0FFF: program $0000-$0BC1, $FF filler $0BC2-$0C3E,
  character generator $0C3F-$0FFE, and at $0FFF a byte that makes the
  ROM's byte sum zero (the power-on check, $006A).
- **RAM** $FF00-$FFFF, the stack at the top. Power on writes $FF and then
  $00 through all of it ($0078), so every variable starts at zero. The
  line buffer is $FF29 on; the map lists every variable.
- **Vectors.** $0008 (INTT0/INTT1) and $0018 (INTE0/INTE1) save the
  registers and call through RAM: the timer interrupt's handler address
  is at $FF09, the external (event counter) interrupt's at $FF0B, exactly
  as in the Schneider NLQ401. The other vectors land inside these handlers
  or the table after them and are never enabled.
- **Coroutines.** The motors are driven by timer 1. `yield` ($0B8C) pops
  its own return address and makes it the timer handler, so the rest of
  the calling routine runs, a step at a time, in the timer interrupt,
  while the program returns to the caller's caller. `wait_motion` ($0A50)
  waits until a motion has finished (timer 1 masked again).

Port use agrees with the SM (`docs/commodore-mps-803.md` §7.3): port A's
low half drives the carriage stepper (phases in VV:00) and its high half
the paper feed stepper (VV:01); port B drives the head wires, active low;
port C is set to control mode for RxD (PC1, bus DATA), SCK (PC2, bus
CLK), INT2 (PC3, bus ATN) and CO1 (PC7, the head pulse /HPLS, timed by
the event counter), with PC0 (LF button) and PC5 inputs and PC4 (lamp) and
PC6 (carriage current) outputs; PF5 pulls DATA low, PF6 is the home switch
(low at home), PF7 the paper-empty switch (high without paper). The A/D
converter reads AN0 (+24 V), AN1 (head thermistor), AN2 (SW1) and AN3
(SW2).

## Power on ($0000-$0121)

1. Ports, timers and the serial receiver are set up ($0035).
2. The ROM sum and a RAM write test; a failure goes to `error_flash`
   ($0109), which toggles the lamp every 9 × $8F timer ticks for ever,
   the same flashing as a motor error. (The SM's troubleshooting says a
   failed ROM check lights the lamp steadily; this firmware flashes it.)
3. The switches: listener address VV:08 = $24, or $25 if AN2 reads $7F or
   more (SW1 open, with its pull-up, presumably device 5). LF held (PC0
   low) requests the self test.
4. **Carriage**: step left with an eight-step acceleration until the home
   switch closes (600 steps without it is a motor error); decelerate;
   step right until the switch opens (more than 28 steps is a motor error);
   then move right 248 steps (8 ramp, 232, 8 ramp), towards the middle of
   the line, and take that as position 248. Position 0 is therefore where
   the switch opens. This settles SM's two accounts: left first, then
   towards the middle.
5. With no paper at power on, the paper counter is set past its limit, so
   the first line printed or fed raises paper empty.
6. Self test, or the bus loop.

## The serial bus ($0121-$01FB)

The printer is a listener only. Bits are shifted in by the CPU's serial
receiver, clocked by bus CLK, so the firmware handles only the handshake
around each byte.

- **Idle** ($0124): wait for ATN to fall (the INT2 flag), polling the LF
  button meanwhile.
- **ATN**: pull DATA low at once, wait about 3.3 ms (`delay_3ms`, $01AF),
  and receive the byte.
- **Per byte** (`receive_byte`, $01C3): wait for CLK released, release
  DATA, wait for DATA to read high, then wait for CLK to fall within a
  28-pass loop (about 200 µs). If it falls, the eight bits arrive through
  the receiver; the firmware waits for CLK low, **pulls DATA low (busy)**
  and returns with the byte and the state of ATN. DATA stays low until
  the byte has been interpreted, including any printing and feeding it
  caused, which is the printer's BUSY.
- **EOI**: if CLK does not fall in time, the firmware pulls DATA low for
  about 60 µs and receives the byte again ($018C).
- **Under ATN after our LISTEN**:
  - $60: graphic set (`sa_graphic`); $67: business set (`sa_business`).
  - **Any other secondary address** (including the OPEN and CLOSE bytes
    $Fx, $Ex) sets VV:07 bit 0, and every data byte is then **ignored**
    until UNLISTEN or our LISTEN again. This settles SM conflict 5.
  - Our LISTEN again clears that; data with no secondary address selects
    the graphic set.
  - $3F (UNLISTEN): wait for CLK released, release DATA, go idle.
  - Any other ATN byte is ignored and listening continues.
- **Another device's LISTEN** ($0199): hold DATA briefly, release it and
  go idle (the SM's "system line release").
- UNLISTEN does **not** print: a line without CR stays in the buffer until
  a later CR, LF, overflow or full buffer.
- Nothing in the firmware times 33 ms; the SM diagram's "33 ms max" is not
  a firmware constant (conflict 11 is left open).

## Printing model

Bytes are interpreted into a **line buffer** of entries; the buffer is
printed on CR or LF, when the line overflows, or when it fills. A dot
position VV:20-21 runs from 0 to 480 across the line, in dots of 1/60 inch.

### Print mode (VV:17)

Bit 0 double width, bit 1 bit image, bit 2 reverse (RVS), bit 3 business
set, bit 6 quote mode. All zero at power on: standard width, graphic set.

### Buffer entries

| Entry | Meaning |
|---|---|
| $20-$BF | a glyph index (text) |
| $80-$FF | a bit-image column, in bit-image mode (the raw byte) |
| $C0-$FF | a quote-mode control code, in text mode: printed reversed (below) |
| $01-$08 | a mode toggle, XORed into the mode: 1 double width, 2 bit image, 4 reverse, 8 business set; combinations such as 3 occur |
| $09 hi lo $09 | a move: hi × 256 + lo blank columns |
| $0A n d $0A | a repeat: n copies (0 = 256) of column d |

The first entry records the mode it starts in (VV:24). A toggle is not
buffered when the buffer is empty, and a toggle equal to the last entry
removes that entry instead (`toggle_mode`, $093C), so SO SI with nothing
between costs nothing.

**Buffer size: 152 bytes** (`append_byte`, $094C), as the SM says, not the
UG's 90. A multi-byte entry can run a few bytes over before the check.
When the count reaches 152 the buffer is printed **without** a line feed
(`buffer_full`, $0962), and the next buffer carries on from the current
position: the output is the same as if it had not filled. A pending move
is forgotten at that point (none can be pending then in practice, as a
move is buffered only together with the item it precedes).

Costs, in buffer bytes: a character or bit-image column 1; a mode code
1 if it changes the mode, else 0; POS and ESC POS 4 when a character or
column follows (0 for a zero move); SUB 4; CR and LF nothing.

### Advancing and the right margin (`advance`, $07C7)

Each character advances 6 dots (12 double width), each bit-image column
1, each SUB n columns. First a pending move from POS or ESC POS is
buffered (`9 hi lo 9`) and added to the position. If the new position is
**480 or less** the item goes in this line; otherwise the line is printed,
fed and started afresh at 0 (`wrap_line`, $0831), and the item goes
there. So:

- the wrap is **lazy**: a line filled to exactly 480 prints only when the
  next item, CR or LF arrives (the SM's "printing does not start merely
  because column 480 has been reached");
- a standard character fits at positions 0-474 and a double-width one at
  0-468, so after a move to 475-479 (469-479) the next character goes to
  the start of the next line, which is the SM's rule (conflict 7);
- the automatic line feed leaves reverse, quote mode and the character
  set as they were (only CR and LF reset them);
- a SUB run that crosses the margin is split: the part that fits ends this
  line and the rest starts the next ($0808).

### Printing a line

`print_buffer` ($049D) checks the paper, waits out a paper-empty error
(holding DATA low), records the mode at the end of the line (VV:26, which
picks the line feed) and finds the line's extent (`line_extent`, $06E5):
leading and trailing entries that print nothing are dropped (spaces,
glyph $80, empty bit-image columns, moves, empty repeats), but in reverse
mode nothing counts as blank. An empty line prints nothing and only
feeds.

The carriage then prints **by the shortest path** ($04B8): to the right
if it is left of the line, and to the left if it is past the right end
(plus 16 steps), else from whichever end is nearer. A line holding
reverse characters, quote-mode controls, bit image or SUB is printed
**left to right only** (VV:1D bit 0). There is no other difference in
output between the directions: right to left, the entries are read
backwards and each glyph's columns in reverse order.

Each column is handed to the interrupt that fires the head
(`fire_head`, $06BA). The timer steps the carriage once per column at
$4F ticks a step (about 360 steps a second, if a tick is 384 clocks of
the 11 MHz crystal, which is inferred, not read), and schedules the head
$0684 event-counter counts after each step. The head pulse ends after a
time computed from AN0 (+24 V): $0319 less min(AN0, $95) × $E6 / $78
counts; a higher supply gives a shorter pulse, as the SM says.

The firmware's step bookkeeping fires a column one step further on moving
right than moving left (first column at print start + 1 rightwards,
end − 2 leftwards); read as compensation for the moving head's lag, both
directions put a column at the same place. This is an inference; for a
simulation, **dot x of a line is at carriage step 24 + x** in both
directions, as `line_extent` adds 24 ($18) to the dot positions. That is
the SM's "printing begins at the 24th pulse after the switch opens".

### Line feed (`line_feed`, $044C; `feed_paper`, $0B28)

Paper steps are 1/216 inch:

- **21 steps (7/72 in)** if the mode when the line printed had bit image
  set (conflict 2: 7/72, not the UG's 9 lpi);
- else **27 steps (1/8 in)** if AN3 (SW2) reads above $7F, else
  **36 steps (1/6 in)**. With SW2 between AN3 and 0 V and a pull-up, open
  is 1/8 in; which marked position that is was not settled (conflict 9).

The feed accelerates over 7 steps through a table at $002E, runs at $8E
ticks a step (about 200 steps a second), and decelerates over 7. The
manual LF button feeds by the same rule, with the mode of the last line
printed.

## Commands

The byte interpreter is `interpret` ($0256). In order:

1. **Parameters**: if a SUB, POS or ESC is waiting for bytes, the byte is
   one of them, whatever its value (a CR there is a parameter).
2. **Bit-image mode**: a byte with bit 7 set is a column; $00-$1F go to the
   control code table; $20-$7F are ignored. So in bit image **$91 and $92
   are columns**, not set or reverse codes.
3. **Text mode**: CR; then, in quote mode, every other byte prints; then
   $91 and $92; then $00-$1F through the table; $80-$9F (other than $91,
   $92) are ignored; $20-$7F and $A0-$FF print.

Control codes $00-$1F dispatch through a table at $036C. Only these have
handlers; all others are ignored:

| Code | Handler | What the firmware does |
|---|---|---|
| $08 BS | $03AC | Cancels a pending move. Sets bit image (toggle 2). Leaves double width as it was. |
| $0A LF | $0421 | Exactly as CR. |
| $0D CR | $0421 | Prints the line, feeds (7/72, 1/8 or 1/6 in by the mode), starts a new line at position 0; ends reverse and quote mode; clears the $11/$91 mark and returns to the set of the current secondary address; then the head-cooling pause if AN1 reads above $7F (62 × $E5 ticks, about 0.5 s). Double width and bit image persist. |
| $0E SO | $045D | Cancels a pending move. Double width on; bit image off. |
| $0F SI | $046A | Cancels a pending move. Double width off; bit image off. |
| $10 POS | $0419 | Two digits follow (below). |
| $11 | $03D3 | Business set (toggle 8), marked as chosen within the line. In bit image it does nothing but mark. |
| $12 RVS ON | $03BB | Reverse on (toggle 4); ignored in bit image. |
| $1A SUB | $0411 | In bit image only: n and d follow. In text mode the SUB alone is ignored (its following bytes are then ordinary data). |
| $1B ESC | $041D | $10 nH nL follow. |
| $91 | $03F2 | Graphic set, marked as chosen within the line. Text mode only. |
| $92 RVS OFF | $03C7 | Reverse off. Text mode only. |

**POS $10 d1 d2** ($034D): each digit is taken by its **low four bits**,
so the column is 10 × (d1 & 15) + (d2 & 15) and non-digits give that
arithmetic, not an error. The target is 6 × column dots; **80 or more is
ignored**.

**ESC $10 nH nL** ($0307): after ESC, any byte other than $10 is
**swallowed** (it is neither printed nor obeyed). Only **bit 0 of nH** is
kept, so the dot position is (nH & 1) × 256 + nL; **480 or more is
ignored** (conflict 1: the SM's 0-479 is right, the UG's 0-639 wrong; and
nH of 2 or 3 aliases to 0 or 1).

**Moves are forward only** (`set_position`, $031D). The target becomes a
pending move of target − current dots; a target **behind** the current
position gives no move at all, and printing carries on where it was. So
POS and ESC POS cannot move left or overstrike (the UG's p. 38 claim does
not hold). The move is kept pending until the next character, column or
repeat: a later POS or ESC POS replaces it (only the last counts, as the
SM says), and **BS, SO or SI cancel it** (`cancel_position`): that is what
the SM's "POS right before BS, SO or SI is invalid" means (conflict 6).
POS/ESC POS on a line filled to exactly 480 first prints and feeds it.

**SUB $1A n d** ($02DD): d below $80 cancels the command; else n copies
(n = 0 gives 256) of column d, advancing n dots, split at the margin as
above.

**Bit image**: a column byte's bit 0 is the **top** dot and bit 6 the
bottom; bit 7 must be set to mark it as data. Columns go one per dot,
1/60 in apart, with reverse and double width having no effect. SO or SI
end bit image; CR and LF do not.

**Reverse**: inverts all seven rows of all six columns of each character
cell (twelve double width), including the gap column, so reversed text
is a solid band and a reversed space a solid block. It does not apply
to bit image or to moves (a POS within reversed text leaves white).

**Quote mode**: each `"` printed in text mode toggles it (bit 6). While on,
every byte except CR prints, so **LF is printed** (as a reversed J) and
does not end quote mode, nor does it act (conflict 4); $00-$1F print as
the reversed glyphs of $40-$5F, and $80-$9F (including $91, $92) as the
reversed glyphs of $C0-$DF, in the set in force. Characters $20-$7F and
$A0-$FF print normally (reversed only if RVS is on). CR ends quote mode
and reverse. Quote mode is not tracked in bit image.

**Character sets and secondary addresses** (conflict on SM p. 1-8,
item 9): VV:27 holds the set of the current secondary address (1 business,
2 graphic). Each LISTEN with $60 or $67 applies its set, **unless** $11 or
$91 has changed the set within the current line and the secondary address
is the same as before, in which case the $11/$91 choice stands; a
different secondary address replaces it. CR and LF end the $11/$91 choice
and go back to the secondary address's set. In bit-image mode the
business set is not applied by a secondary address or CR (a quirk: a job
opened with SA 7 while the printer is still in bit image from earlier
prints in the graphic set until the next CR in text mode).

### Self test ($0895)

LF held at power on: after homing, lines of 80 characters, each line
starting one code later than the last, through codes $41 up to $7F, then
$A0 to $FF (skipping $80-$9F), then back to $20 with the character set
switched, for ever. Each line feeds by SW2. No interface is involved.

### Paper empty and the LF button

The paper feed counts steps fed while PF7 is high (no paper); more than
108 steps (three 1/6 in lines) raises paper empty at the next print or
feed: the lamp flashes and DATA is held low until paper is loaded and LF
pressed. That press does not feed. Off line, LF feeds one line, then
after about 0.5 s (100 waits of $8F ticks) feeds while held.

## Print geometry

- **Horizontal**: one dot column per carriage step, 1/60 inch. A character
  cell is **6 columns** (1/10 in), 80 to the 480-dot line. Double width
  prints **each glyph column twice** at full step pitch, 12 columns
  (conflict 12). Dot x is at carriage step 24 + x from the home switch's
  opening.
- **Vertical**: seven dots at 1/72 inch (three 1/216 in paper steps),
  driven from port B bits 0-6, bit 0 the top dot. The firmware forces
  **port B bit 7 high in every column** ($06BF), so **wire 8 never
  fires** (conflict 8). That wire 8 is the bottom wire is inferred from
  the SM's wire numbering, not read.
- **Line feeds**: 36, 27 or 21 steps of 1/216 in (1/6, 1/8, 7/72 in).

## The character generator

At $0C3F-$0FFE: **160 glyphs**, glyph indices $20-$BF, at $0B7F + 6 ×
index (`glyph_address`, $09CF). Each glyph is **six bytes, one per dot
column, left to right**; **bit 0 is the top row, bit 6 the bottom, bit 7
unused**. Letters and punctuation use five columns with the sixth blank
(a few, such as `!`, sit in the middle columns); the graphics use all six
so they join. The zero is slashed. Lower-case letters have no descenders.
Glyph $7F is six $FF bytes and no code reaches it.

Glyph indices: $20-$5F the PETSCII/ASCII characters space to ←; $60 the
horizontal line; $61-$7A lower case a-z; $7B-$7E four business-set
graphics (2 × 2 checkerboard, two diagonal hatchings, ✓); $80-$9F the
graphics of $A0-$BF; $A0-$BF those of $C0-$DF ($A0 has the same dots as
$60).

`glyph_index` ($08EC) maps a code to an index:

- **Graphic set**: $20-$60 → same; $61-$7F → $A1-$BF; $A0-$DF → $80-$BF;
  $E0-$FE → $80-$9E; $FF → $BE (π, as $DE).
- **Business set**: $20-$40 and $5B-$60 → same; $41-$5A → $61-$7A
  (lower case); $61-$7A and $C1-$DA → $41-$5A (capitals); $7B-$7D and
  $DB-$DD → $BB-$BD; $7E, $7F, $DE, $DF → $7B, $7C, $7B, $7C; $A9, $E9 →
  $7D; $BA, $FA → $7E (✓); $FF → $7B; $C0 → $A0; the rest of $A0-$BF and
  $E0-$FE as in the graphic set.

So the two sets differ exactly where PETSCII's upper-case/graphics and
lower/upper-case sets differ, and agree with the SM's tables (pp. 1-16,
1-17) as far as their scans can be read.

**mps803.bin** (3,584 bytes) is not from the printer: it is exactly this
character generator turned into rows. For all 384 printable codes of the
two sets, its 7 bytes (one per row, bit 7 the leftmost dot, bits 1-0
always clear) equal the ROM glyph that `glyph_index` chooses, transposed;
its non-printable codes are empty. It is derived data, consistent with
an emulator's table such as VICE's. (Its zero is slashed, as the ROM's
is; `docs/commodore-mps-803.md` §7.8 says otherwise and is wrong there.)

## Conflicts settled

Numbered as in `docs/commodore-mps-803.md` §8:

1. ESC POS: 0-479; 480 and above ignored; only bit 0 of nH counts.
2. Bit-image line feed: 7/72 in (21 steps).
3. Buffer: 152 bytes.
4. LF in quote mode is printed (reversed J) and ends nothing; only CR
   ends quote mode. Outside quote mode LF does all that CR does.
5. A secondary address other than 0 or 7 makes the printer ignore the
   data until UNLISTEN.
6. BS, SO and SI cancel a pending POS/ESC POS move.
7. The wrap is lazy; the 475 and 469 thresholds follow from fitting 6 or
   12 dots within 480; SUB splits at the margin.
8. Port B bit 7 (wire 8) never fires; bit 0 is the top dot.
9. AN2 at $7F or more gives device 5, AN3 above $7F gives 1/8 in; which
   switch positions these are is not settled.
10. Power on: left to home, then about 248 steps right.
11. Not settled (no 33 ms constant).
12. Double width repeats each column.

## Uncertain

- Absolute timings (the timer 1 tick, the event counter's rate, the head
  delay and pulse width) are inferred from the SM's speeds, not read from
  the clock configuration.
- The physical meaning of the one-step direction compensation.
- Which physical switch positions the A/D thresholds correspond to.
- Bus timing details beyond the handshake order (loop lengths were
  estimated, not counted in clock states).

## Settled since

- A quote-mode control prints reversed whether or not RVS is on: a column
  goes to the head uninverted (so reversed, the pins being active low) if
  either reverse (C bit 2) or the quoted-entry flag (C bit 6, set at
  $09E3 and cleared after the entry at $066E) is set (`ONI C,$44` at
  $0657), an OR, not an exclusive OR.
