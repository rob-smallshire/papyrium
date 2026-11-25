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
standard RS-232 interface: the M-1009 and the M-1109 are distinct models, and Papyrium models only the
M-1109, under its four names (`brother-m1109`, `centronics-glp-ii`,
`sony-prn-m09`, `rca-vp2100`). The NLQ401 would be a variant of an M-1009
model, with Schneider's NLQ, not of the M-1109.

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
