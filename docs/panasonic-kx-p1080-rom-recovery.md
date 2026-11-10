# Recovering the Panasonic KX-P1080U's firmware

How Papyrium came to have the whole of a KX-P1080U's firmware, including
the 4 KB that never left the CPU, when we started with a dump of its EPROM
alone. The findings themselves are in `docs/panasonic-kx-p1080.md`; this
is the story of how they were reached, what went wrong and what worked,
for whoever does the same to the next printer.

Rob decided (2026-11-10) that anything in this printer's ROMs may be used.
The ROM images stay uncommitted in `docs/local/panasonic-kx-p1080/`.

## What we started with

- `KX-P1080U.BIN`, 16 KB read from the printer's EPROM, with nothing to
  say what CPU ran it or where it sat in memory.
- The KX-P1080 and KX-P1080i manuals as PDF scans, and a phone
  photograph of six pages of the KX-P1080U's own manual. These were OCRed
  (`tools/manual-ocr/ocr.sh`) and restated, with page references, in the
  notes.
- A friend of Rob's with the printer itself, an EPROM programmer and
  great patience.

## Naming the CPU

The byte statistics point to one family. 0x54 followed by an address
recurs as a run of three-byte jumps at 0x2000; 0x44 with an address is
common, 0xB8 more so; and over a hundred sequences read an address
0xFFxx. Those are the NEC µPD7810 family's JMP, CALL and RET, and its
internal RAM at 0xFF00-0xFFFF. MAME's disassembler, built as the
stand-alone `unidasm` and used only as a tool, disassembled the EPROM
cleanly with `-arch upd7810`.

The board photographs, which came last, confirmed the family and refined
the part: the CPU at IC2 is a Matsushita **MN1276**, Panasonic's own
masked part of the µPD7811 kind, and the EPROM at IC3 an NEC D27128D
labelled `PJWIXP1080U / IC3 U160B / 61201`.

## The memory map, and the hole in it

The call targets settled where the EPROM sits. Calls land on routine
entries in 0x2000-0x3FFF and in 0x4000-0x4FFF, and either way only if the
address is taken modulo 0x4000 as the offset in the file; calls into
0x0000-0x1FFF never land on anything sensible. So the EPROM answers at
0x0000-0x3FFF and again at 0x4000-0x7FFF, but its first 4 KB is only ever
reached through the upper copy. Something else answers at
0x0000-0x0FFF, and on a µPD7811 that is the CPU's 4 KB mask ROM. Reset,
the interrupt vectors and the CALT table (0x0080-0x00BF) live there,
which is why the EPROM's own bytes at those addresses make no sense as
code.

At first that looked like a curiosity: the main program, the command
interpreter and the NLQ font were all in the EPROM.

## Mapping the EPROM

The Star LC-10's annotated disassembler became a shared tool,
`tools/rom-map/disassemble.py`, driven by a map file
(`tools/kx-p1080-rom/kx-p1080-map.txt`). The file names the ROM, the
architecture and how the ROM's bytes appear at the CPU's addresses
(`@segment`, `@mirror`), and which working-register page `VV:xx` operands
address (`@vpage FF`). Data regions keep the disassembly on instruction
boundaries, and every routine and RAM location traced gets a name, so
the listing grows more readable as the tracing goes on.

Tracing from the character path outwards found:

- the NLQ characters, indexed at `$4B00`, stored as two passes of columns
  on a 1/240 inch grid, half of each symmetrical character stored and
  mirrored, italics slanted at print time;
- 41 IBM PC characters in NLQ that no KX-P1080 manual mentions and no
  command reaches;
- the proportional widths, which differ from both manuals at seven
  characters;
- the escape dispatch table at `$32FA`, which holds exactly the manual's
  commands;
- the line buffer, the graphics densities and the national sets.

## The draft font is not there

The draft path (`$4302`) multiplies the character code by nine and adds
a base from a small table at `$4348`: `$00C0` upright, `$0540` italic,
and `$09C0` and `$0BB8` for the IBM PC characters. Every one of those is
inside the CPU's 4 KB. Laid end to end, 128 + 128 + 56 + 56 characters
of nine bytes fill that ROM exactly from the end of the CALT table. **The
draft fonts, the face the printer uses most, were in the mask ROM, and
the dump did not have them.**

There were two ways on:

1. Reconstruct draft from printed samples, as the Brother M-1109's
   characters were rebuilt from its manual's pages. That would be faithful
   only as far as the samples go.
2. Make the printer print its own mask ROM. The µPD7811 has no read
   protection, the firmware reads those tables itself, and the code that
   runs is in the EPROM, which we can replace.

We took the second.

## Making the printer read itself out

### The first design, and why it was dropped

The first patch (`a349a42`) changed the bit-image path so that each
graphics byte received printed the internal ROM byte at an address it
gave, as one column of eight dots. That made 4 KB into a few pages of dot
columns. Rob rejected it: on a forty-year-old printer, one dot per bit
has no redundancy against a sticking pin or a tired ribbon, and reading
it back would need software of its own. A hex dump is redundant (each
digit is a whole character), anyone can read it, and a checksum can
check it.

### The hex dump

The self test is in the EPROM (`$2339`, started by holding LF at
power-on), and it already feeds characters through the printer's
ordinary text path, as if they had been received:

1. wait for bit 6 of `$FF8F` to clear;
2. put the character in `$FF74`;
3. `MVI D,0` and `CALT ($009E)`.

It ends a line with LF in `$FF74`, `CALL $2EF8` and `CALL $2245`.

`tools/kx-p1080-rom/dump_patch.py` replaces the self test's first
instruction with a jump to 135 bytes in the unused EPROM at `$1F40`.
That routine prints the internal ROM 16 bytes to a line: the address, a
colon, the bytes, and a checksum (the bytes' sum modulo 256). It prints
all 4 KB twice, then jumps to the self test's own ending. Its state lives
in the self test's RAM, `$FFF0-$FFF4`.

There was no µPD7810 assembler to hand, so the script assembles the
routine itself, from instruction encodings each seen in the firmware's
own code. It refuses to emit anything else, checks every size and
branch range, and prints the result disassembled by `unidasm` for
checking:

```
2339: 54 40 1f  JMP     $1F40

1f40: 71 f4 01     MVIW    VV:F4,$01     two passes
1f43: 34 00 00     LXI     HL,$0000
1f46: 70 3e f0 ff  SHLD    $FFF0
1f4a: 01 f1        LDAW    VV:F1         the address, as hex
1f4c: 40 a7 1f     CALL    $1FA7
1f4f: 01 f0        LDAW    VV:F0
1f51: 40 a7 1f     CALL    $1FA7
1f54: 69 3a        MVI     A,$3A         ':'
1f56: 40 bd 1f     CALL    $1FBD
1f59: 71 f2 00     MVIW    VV:F2,$00     checksum
1f5c: 71 f3 0f     MVIW    VV:F3,$0F     sixteen bytes
1f5f: 69 20        MVI     A,$20
1f61: 40 bd 1f     CALL    $1FBD
1f64: 70 3f f0 ff  LHLD    $FFF0
1f68: 2d           LDAX    (HL+)         the internal ROM's byte
1f69: 70 3e f0 ff  SHLD    $FFF0
1f6d: b0           PUSH    VA
1f6e: 74 c0 f2     ADDW    VV:F2
1f71: 63 f2        STAW    VV:F2
1f73: a0           POP     VA
1f74: 40 a7 1f     CALL    $1FA7
1f77: 30 f3        DCRW    VV:F3
1f79: 4f e4        JRE     $1F5F
 ...               two spaces, the checksum, a new line
1f8d: 01 f1        LDAW    VV:F1
1f8f: 77 10        EQI     A,$10         past 0x0FFF?
1f91: 4f b7        JRE     $1F4A
1f93: 40 9d 1f     CALL    $1F9D
1f96: 30 f4        DCRW    VV:F4
1f98: 4f a9        JRE     $1F43
1f9a: 54 84 23     JMP     $2384         the self test's end
 ...               newline, hexbyte, nibble, putc
1fbd: 55 8f 40     OFFIW   VV:8F,$40     putc: as the self test does it
1fc0: fc           JR      $1FBD
1fc1: 63 74        STAW    VV:74
1fc3: 6c 00        MVI     D,$00
1fc5: 8f           CALT    ($009E)
1fc6: b8           RET
```

The friend programmed the image into a 27128, fitted it, held LF and
switched on, and the printer typed out its own mask ROM.

## Reading the printout back

The friend scanned five A4 pages at 300 dpi
(`internal-rom-dump-scan.pdf`), 60 lines a page: the first of the two
passes.

### OCR engines

General-purpose OCR did badly on dense hex. Tesseract, even limited to
hex digits and colons, dropped digits, read A0 as AD and 0A as DA, lost
the leading 0 of addresses, and fell apart on the fainter later pages:
129 usable lines of 256. macOS's Vision framework broke each page into
fragments of a token or two. Neither knew that every character sits on
a fixed grid.

### A reader that knows the layout

The printout is very regular: 10 characters to the inch (30 px at
300 dpi) and the same 57 character positions on every line. So the
reader built for it, now `tools/kx-p1080-rom/read_dump_scan.py`:

1. **Rows.** A horizontal ink profile splits each page into its lines:
   60, 60, 60, 60 and 15, or 255 in all.
2. **Grid.** The obvious first version fitted one pitch per line by
   search and cut fixed cells. It drifted by half a character by the end
   of a line, so `80 40 20 10` read as `8B 4B 2B 3B`. The fix was to find
   the glyphs from the ink and fit origin and pitch by least squares to
   their centres: 30.0 px on almost every line.
3. **Cells.** A cell is cut at each of the 38 digit positions (four
   address, 32 data, two checksum), wider than the glyph, with the
   matcher searching ±3 px vertically and a range of horizontal offsets.
   A first attempt centred cells on the detected glyphs instead; where two
   glyphs' ink merged, cells came out 7 px off, and even the addresses
   misread.
4. **Templates, trained on the addresses.** Rob's suggestion: the
   address at the start of each line is known from its position, 16
   times the line number. That gives four labelled glyphs on every line,
   all 16 digits on every page, in the same ribbon and the same scan. A
   template per digit per page (the ribbon fades from page to page) is
   the mean of its samples, each first aligned to the template so far.
   Each round then adds the lines whose checksum holds as more training
   data.
5. **Classify** every cell by normalised correlation against the page's
   templates at every offset.

That read 220 of the 255 lines with their checksums holding.

### The checksum is a check, not a corrector

Swapping a doubtful cell for its runner-up until the checksum held
"fixed" 20 more lines. Looking at them against the image showed several
were wrong. Line 0BD0 ends `00 56 FA`; the reader saw `58`, and the
corrector changed the line's first byte from A8 to A6 to make the sum
come right. With up to two substitutions among several doubtful cells,
a one-in-256 coincidence is not rare. So no corrected line was kept:
those, and the 15 that failed outright (mostly on page 4, where the
ribbon was faintest), 35 lines in all, were read by eye from enlarged
crops, and every one of them passed its checksum.

### An independent second reading

A matching checksum still lets two compensating misreads through. So
every cell of every line was read again, by a different method: a
five-nearest-neighbour vote over all the aligned cells from *other*
lines, never its own. It agreed with the transcription on every cell of
every line, except on 0D60, whose grid fit had failed. That line's cells
were misaligned, and it was among those read by eye.

### The result

- `KX-P1080U-internal.bin`: the 4 KB internal ROM. 255 of its 256 lines
  are confirmed by their checksum and by two independent readings.
- The printer stopped after 0FE0, printing neither line 0FF0 nor the
  second pass, though the routine's logic goes on to both; the cause is
  not yet known. Line 0FF0 is filled with 0xFF like the 64 bytes before
  it, which is safe as far as anything traced goes: no code in the EPROM
  names an address in 0x0D00-0x0FFF, and the last draft table ends at
  0x0DAF.
- `KX-P1080U-internal.txt`: the transcript, each line marked as read by
  the scanner, by hand or assumed.
- `KX-P1080U-cpu.bin`: what the CPU sees at 0x0000-0x7FFF, the internal
  ROM at 0x0000, the rest of the EPROM to 0x3FFF, and the whole EPROM
  again from 0x4000.

## What the internal ROM holds

It is almost all data:

- **Reset** disables interrupts, jumps over the vectors, sets `V` to 0xFF
  in both register banks and the memory mapping register `MM` to 0x0F,
  and jumps to `$2000`. The interrupt vectors and the CALT table all
  point into the EPROM's jump table at 0x2000, so the program is entirely
  in the EPROM. That is why the 37 jumps at 0x2000 seemed to have no
  callers.
- **The draft characters**, nine column bytes each, exactly where the
  draft path said: 128 upright from 0x00C0, codes 0-31 being the
  international characters; 128 italic from 0x0540; and the IBM PC
  characters' draft forms from 0x09C0 and 0x0BB8. The first time they
  were drawn, A to H came out as A to H.
- **Block graphics** for the IBM PC characters from 0x0DB0, which no
  command of the KX-P1080U reaches, and 0x50 bytes unused at the end.

## What came after

- **The draft column format.** The routine at `$46CE` that turns a
  column byte into pins lowers a column two pins when its bit 0 is set,
  column by column, so a j's hook reaches the ninth pin while its stem
  does not.
- **Fonts.** `tools/kx-p1080-rom/extract.py` makes `papyrium.font.kx_p1080`:
  draft and draft italic from the internal ROM, and NLQ and its italic
  from the EPROM, built and slanted as the firmware builds and slants
  them.
- **The printer.** `papyrium.model.panasonic_kx_p1080` prints with them,
  with the ROM's proportional widths, and with download characters and
  NLQ's passes traced through the firmware (`docs/panasonic-kx-p1080.md`).
- **The reader** became a tool. Run on the scan with the 35 lines read by
  eye (`KX-P1080U-internal-hand.txt` in `docs/local/`) and the last line
  filled with 0xFF, it gives the same image, byte for byte.

## Lessons

- **Find what the CPU sees, not what the file holds.** The mirror at
  0x4000 was the clue to an internal ROM, and checking each draft table
  base against the memory map is what showed the fonts were missing.
- **If the printer can read it, the printer can print it.** A patched
  EPROM turned a mask ROM nobody could read into a printout.
- **Print for the reader you have.** Hex text with a per-line checksum,
  printed twice, survives an old ribbon and suits both eyes and
  software.
- **Use the structure.** A fixed grid, known addresses for training, and
  a checksum to accept lines did what general OCR could not.
- **Use a checksum to verify, not to correct.** A second reading by a
  different method is what makes a transcription trustworthy.

## Still to do

- Why the dump stopped after 0FE0. A suspect: the self test's RAM,
  `$FFF0-$FFF4`, which the routine borrows, is also the serial receive
  buffer's state. A rerun with private RAM and an end marker would give
  line 0FF0 and a second reading of everything.
- Thirteen draft characters have a dot in two adjacent columns, which
  the head cannot fire twice so soon; Papyrium prints such a dot once, as
  it does for the LX-800. A sample of the printer's draft would show what
  it does.
