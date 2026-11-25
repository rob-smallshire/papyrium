# Research resources

Sources outside this repository for printers Papyrium models or may model,
kept here so they are not lost. Manuals and ROM images fetched from them
live uncommitted in `docs/local/`; what they show is written up in the
printer notes beside this file.

## For printers not yet modelled

- **Epson MX-80**: an emulation in a branch of MAME,
  <https://github.com/goldnchild/mame/tree/epson_mx80>, and ROM dumps of
  the MX-80 III F/T, <https://github.com/palazzol/miscroms/tree/master/epson%20mx-80%20III%20F-T>.
  The Centronics GLP's ESC A, which stores a line spacing for ESC 2 to
  select, is the MX-80's behaviour.
- **Star NX-1020**: a reverse engineering of its firmware,
  <https://github.com/keithgh1/star-nx1020-re>; a relative of the Star
  LC-10 (`docs/star-lc10-firmware.md`).
- **Epson LQ-2500**: 86Box's emulation of it as a network-shared printer,
  <https://supratim-sanyal.blogspot.com/2020/11/network-shared-dot-matrix-printer-emulation.html>.

## The Great Little Printer family

- "The Great Little Printer",
  <http://manuale-archive.keep.pl/files/The_Great_Little_Printer.html>: the
  two editions (Centronics Models 3101 and 3102) and their other names.
- CPCWiki's NLQ401 page, <https://www.cpcwiki.eu/index.php/NLQ401>, with the
  NLQ401's German user and service manuals, the uPD7811G and uPD78C11A
  data sheets, its schematic and its EPROM image; also its pages on
  Amstrad/Schneider printer resources, control codes, buttons and DIP
  switches, and character sets.
- The NLQ401's service and technical manuals (English) on the Internet
  Archive,
  <https://archive.org/details/nlq-401-schneider-service-manual-technical-manual-engacme>.
- An Apple II driving a Centronics GLP 3101 over RS-232, with photographs of
  the GLP's manual (part 37403101-9A00) and its switch tables transcribed:
  <https://github.com/lambdamikel/apple2-glp-printer>. Its owner reports
  the GLP 3101 has NLQ and a serial port, the Brother M-1009 neither.
- The Brother M-1009's manual: no scan found; the Centre for Computing
  History holds a copy,
  <https://www.computinghistory.org.uk/det/19452/Brother-M-1009-Instruction-Manual/>.
- The Brother M-1109's user guide, <https://www.amigalynx.net/manuals/M1109-UG.pdf>.
- The Commodore MPS-803's user's guide and service manuals, at
  <https://www.zimmers.net/anonftp/pub/cbm/manuals/printers/> and
  <https://www.zimmers.net/anonftp/pub/cbm/schematics/printers/>.
- MAME's `nlq401` device, a skeleton that does not yet print:
  `src/devices/bus/centronics/nlq401.cpp` in MAME.

## Processors and character sets

- NEC's uPD7810/7811 user's manual (instruction set, special registers,
  ports, timers, interrupts),
  <https://datasheets.chipdb.org/NEC/uPD78C1x/uPD78C10_Details.pdf>, and the
  uPD7810/11 data sheet, <https://datasheets.chipdb.org/NEC/781x/uPD7810.pdf>.
- The Amstrad CPC character set and its Unicode mapping,
  <https://en.wikipedia.org/wiki/Amstrad_CPC_character_set>, which
  `papyrium.font.glp` follows for codes 128-255.

## Emulators

`docs/emulators/` describes how BBC Micro emulators deliver printer output.
