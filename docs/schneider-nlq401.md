# Schneider NLQ401 and relatives: notes for a possible future model

Not modelled. These notes record what is known, from the CPCWiki page
<https://www.cpcwiki.eu/index.php/NLQ401>, in case Papyrium adds it later.

## The printer

The NLQ401 was Schneider's near letter quality printer for German
Schneider CPC computers, advertised in the CPC6128 manual; a tractor feed,
the SFT401, was sold separately. The hardware was made by Centronics
(the label reads Centronics Data Computer Corp., Model No. 3101) and sold
under other names:

- **Centronics GLP 500**, reportedly the same printer.
- **Brother M1009**, the same hardware in a different case and colour,
  but without NLQ: Schneider's own EPROM is what added it. The M1009 is
  not the Brother M-1109 that Papyrium models (`docs/brother-m1109.md`),
  which is Brother's own Epson FX-80 compatible design; the similar
  model numbers appear to be a coincidence.
- **Commodore MPS-803**, apparently from the same maker, with a CBM serial
  port instead of Centronics and only 7 pins used for text and graphics,
  though the head is the same 9-pin one.
- **Robotron 6313** (East German), different hardware with an
  NLQ401-compatible mode selected by DIP switch.

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
- Its draft and NLQ designs are not expected to match the M-1109's, but a
  local comparison against `m1109-draft` and `m1109-nlq` would settle it.
- Its command set is unknown here; the user manual would be the reference.
