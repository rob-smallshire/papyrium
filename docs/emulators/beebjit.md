# beebjit

beebjit's printer output, read from its source (commit `789871b`,
November 2026). The printer is in `bbc.c` (`bbc_CA2_changed_callback`);
the file handling in `util.c`.

## The printer

A printer is always attached, with no option to configure or turn it
off. Power-on reset raises CA1 so the BBC sees a ready printer.

When CA2 is an output and falls, the strobe, the printer takes the byte
on the user VIA's port A (`via_read_ORAnh`), writes it to a file, then
pulses CA1 low and high, the acknowledge. In the source's words, "the
world's fastest printer": it is never busy, so the BBC prints at full
speed.

## The file

The first byte printed in a run creates `beebjit.printer` in the
current directory, through `util_file_try_open(name, 1, 1)`, which opens
it with `fopen(name, "wb+")`. The name and place are fixed, and the
file is **truncated**, not appended to: each run that prints replaces
the previous run's output. It stays open until beebjit exits
(`bbc_destroy`).

Bytes are written with `fwrite` and never flushed, so they reach the
file in blocks of the C library's buffer size (typically 4 KB), and the
end of a job only when beebjit exits.

**Every CR (0x0D) is written as LF (0x0A).** The file is therefore not
a faithful capture. With the BBC's defaults (CR-only line ends, LF
ignored) every LF in the file was a CR, and the translation could be
undone; but a genuine 0x0A (sent with `*FX6,0` or `VDU 1,10`) cannot be
told from a translated CR, and 0x0D bytes in a printer's bit-image
graphics or in an escape sequence's parameters are corrupted
irrecoverably.

## Collecting the output

**As beebjit stands:** follow `beebjit.printer` in beebjit's working
directory, as for BeebEm ([beebem.md](beebem.md)), reading from the
start whenever the file is truncated. Two hazards:

- Truncation keeps the file's identity, so it is seen only as the size
  falling below the follower's offset. If a new run prints more than
  the old file held between two polls, the truncation is missed and the
  start of the new run is lost. The modification time going backwards
  is no help either; a follower would need to keep, and compare, the
  first bytes it read.
- Text prints recognisably if LF is read as CR (a transport option, or
  the printer model's auto line feed), but graphics are lost, so this
  route suits text only.

**With a change to beebjit**, the printer would be useful as is:

1. write the bytes unaltered (drop the CR to LF translation);
2. take the file name from the command line, and append rather than
   truncate, or truncate only on request;
3. flush after each byte, or once per frame.

beebjit is GPL-3.0. These would be changes proposed to its author;
whether to pursue them is Rob's decision.
