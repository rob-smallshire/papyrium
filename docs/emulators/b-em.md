# B-em

B-em's printer output, read from its source (commit `0b6f1d2`, October
2025). Paths below are under `src/`. The printer code is in `uservia.c`,
the menus in `gui-allegro.c`, the command-line options in `main.c`.

## The menus and options

File > Printing offers five destinations, chosen as radio items (the
`print_dest_type` enumeration in `uservia.h`):

| Menu item | Command-line option | Destination |
|---|---|---|
| Print to stdout (text) | `-printstdout` | B-em's standard output |
| Print to file (text) | `-printfile FILE` | a file, translated |
| Print to file (binary) | `-printfilebin FILE` | a file, raw |
| Print to command (text) | `-printcmd CMD` | a command's standard input, translated |
| Print to command (binary) | `-printcmdbin CMD` | a command's standard input, raw |

The file items show a save dialog ("Print to file", suggesting
`*.prn`). The destination is not saved in B-em's configuration, so it
must be chosen again after each launch, or given on the command line.

Edit > Printer to clipboard is a separate checkbox: while it is ticked,
printed characters are collected; unticking it puts them on the
clipboard.

## What happens to a byte

A write to the User VIA's output register A (`via_write` in `via.c`)
calls `uservia_write_portA`. If a destination is chosen or the
clipboard is collecting, the byte goes to the printer; otherwise it goes
to the printer port DAC (`lpt_dac`), which is how B-em plays sound
through the printer port.

The handshake is immediate. Writing the byte sets CA1, and when the VIA
returns CA2 high (`printer_set_ca2`) CA1 is cleared again. The printer
is never busy, so the BBC prints at full speed and nothing outside the
emulator can make it wait (except a blocked pipe, below).

The destination is opened lazily, by the first byte printed after it is
chosen (`printer_open`), and closed only when another destination is
chosen in the menu (`printer_close`, called from `file_print_change`),
or on a write error. Choosing the item that is already ticked closes it
and leaves printing off. B-em does not close the printer when it shuts
down (`main_close` does not call `printer_close`); the C library flushes
and closes the stream when the process exits normally.

### Binary and text

Binary destinations write every byte with `putc`, unaltered: a faithful
capture.

Text destinations assume the BBC's printer ignore character is the
default line feed: they drop every LF, turn CR into a newline, turn
0x60 into a pound sign, and write through `fputwc`, so the bytes on the
file depend on the C library's locale. A zero byte as the first byte
after the destination is chosen is dropped. None of this is any use to
Papyrium, which needs the bytes the BBC sent. The clipboard applies the
same pound-sign translation.

### No flushing

B-em never flushes a file or command stream while printing. Bytes sit
in the C library's buffer (typically 4 KB) and reach the file or
command only when the buffer fills, when the destination is changed or
turned off in the menu, or when B-em exits. The end of a job can
therefore stay inside B-em indefinitely. The user can push it out by
clicking the ticked Printing item, which closes the stream and turns
printing off, then choosing it again.

### Files

Files are opened with `fopen(name, "ab")` (binary) or `"a"` (text), so
they are appended to, never replaced, and accumulate output from one
session to the next.

### Commands

Command destinations run the command with `popen` and write to its
standard input. A pipe would make the command a real printer: when the
command reads slowly, the pipe fills and B-em's writes block, so the BBC
waits. But as written, command printing cannot start:

- B-em calls `popen(cmd, "ab")` (binary) or `popen(cmd, "a")` (text).
  `popen` takes `"r"` or `"w"`; on macOS both of B-em's modes fail with
  `EINVAL` (tested), and glibc and the Windows C runtime document the
  same restriction. B-em logs "unable to start print command" and turns
  printing off. (The message names the print file, not the command.)
- The command named on the command line by `-printcmd` or
  `-printcmdbin` is stored as the print file name, not as the command.
  The command actually run is always the `printcmd` key of B-em's
  configuration file, `lp` if it is not set.

## Collecting the output

**As B-em stands:** choose Print to file (binary) and have Papyrium
follow the file with the `file-follow` transport
([beebem.md](beebem.md)). Bytes arrive in buffer-sized blocks rather
than one at a time, and the end of each job arrives only when the user
turns printing off and on again (or quits B-em). The idle timeout should
then end the job.

**With a change to B-em:** three small fixes would make Print to
command (binary) the best route:

1. open the pipe with `"w"` (and `"wb"` on Windows);
2. take the command from `-printcmd` and `-printcmdbin`;
3. flush after each byte (or once per emulated frame).

The command could then hand the bytes to Papyrium: `papyrium send -`
(or `nc HOST 9100`, where installed) to a running printer's `raw-tcp`
transport, or `papyrium print -` to print them as one job when B-em
closes the pipe.
Papyrium would get the bytes as they are printed and B-em would get real
backpressure. Flushing alone (fix 3) would also make the file route
deliver bytes promptly.

B-em is GPL-2.0. These would be changes proposed to its maintainers;
whether to pursue them is Rob's decision.
