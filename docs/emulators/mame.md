# MAME

MAME's printer output for the BBC Micro machines, read from its source
(commit `8155050`, November 2026) and tried with MAME 0.289 running
`bbcb` headless, with ROMs borrowed from other emulators. Paths below are
under `src/`. What was tried, and how, is under "Trying it".

## The printer port

Every BBC machine (`mame/acorn/bbcb.cpp`, `bbcbp.cpp`, `bbcm.cpp`,
`bbcmc.cpp`) wires the user VIA's port A, through an output latch, to a
Centronics slot named `printer`; CA2 drives the strobe and the slot's
acknowledge drives CA1. The slot holds a device chosen with
`-printer NAME`, by default `printer`, the generic Centronics printer
(`devices/bus/centronics/printer.cpp`). Others include emulations of real
printers (`fx80`, `lx800`, `nlq401` and more), below.

The generic printer emulates the handshake with real timing. On the
strobe's falling edge it goes busy; 10 µs later it pulses the
acknowledge low and hands the latched byte to its output; 7 µs after that
it is no longer busy, and 5 µs later the acknowledge returns high
(`ack_timer_tick`, `busy_timer_tick`). Every bit of the byte is kept.

The output is a "printout" image (`devices/imagedev/printer.cpp`), mounted
with `-printout FILE` (`-prin` for short) or from the File Manager in
MAME's menus. With nothing mounted the printer reports a paper error
(the BBC does not look at that line), acknowledges each byte and throws
it away. Each byte is written as it is printed, through MAME's file layer
(`emu/diimage.cpp`, `lib/util/corefile.cpp`), which does not buffer
writes: a `pwrite` per byte on POSIX.

## Printing to a file

`-prin printer.prn` first tries to open an existing file for writing,
without truncating it (`determine_open_plan`), and only creates the file
(truncating) if that fails (`emu/image.cpp`). So:

- a new file is created and filled as the BBC prints, a byte at a time;
- an **existing file is overwritten from its start but not truncated**:
  the new printing replaces the old byte for byte, and whatever the old
  file held beyond the new printing's length stays at its end.

Both were seen in MAME: printing `BYE` into a file that held
`HELLO FROM MAME` left `BYE\rO FROM MAME\r`.

The `file-follow` transport, starting at the end of an existing file,
sees nothing until the new printing outgrows the old file, and then reads
from the start (the file's first bytes have changed), old tail and all.
Give MAME a file that does not exist (delete it, or name a new one each
session) and follow it with `-T from-start=yes`, or use a socket.

## Printing to a socket

MAME's file layer opens a path of the form `socket.HOST:PORT` as a TCP
connection instead of a file (`osd/modules/file/posixsocket.cpp`,
`winsocket.cpp` on Windows), and the printout image goes through that
layer. So

```
mame bbcb -prin socket.127.0.0.1:9100
```

connects the BBC's printer port straight to `papyrium serve`'s `raw-tcp`
transport, with no change to MAME or Papyrium. Tried on macOS, a BBC
program's output arrived byte for byte as the BBC printed it, and the
job ended on Papyrium's idle timeout while MAME stayed connected. On
POSIX (the Windows implementation was not read):

- The connection is IPv4 only (`AF_INET`, `gethostbyname`), so name an
  IPv4 address, or a host that resolves to one, where Papyrium listens.
- The socket is blocking, so a printer that stops reading stalls MAME's
  emulation: real backpressure, which no other emulator here offers
  (from the source; not tried).
- Papyrium must be running first. If the connection is refused, MAME
  falls back to creating the image, which for a socket path means
  **binding and listening** on that address and port (seen in MAME: it
  reports "Connection refused" and then holds the port): it then has
  the port Papyrium wanted, and drops every printed byte, since writes
  to a listening socket fail and the printer ignores the failure.
- MAME does not reconnect. If Papyrium stops, the connection is gone
  until the printout is mounted again; nothing in MAME's source ignores
  `SIGPIPE`, so its next printed byte may terminate MAME.
- Each write's result is ignored, so a write that fails loses its byte
  silently.

## The serial port

The BBC's RS423 port is a slot too (`-rs423 NAME`). With `null_modem`,
its bytes go to a "bitbanger" image (`-bitb`), which takes the same
`socket.HOST:PORT` paths, so a BBC printing to a serial printer (`*FX5,2`)
reaches a raw TCP port the same way. The null modem's own settings
(baud rate, framing, flow control) must match the BBC's (`*FX7`, `*FX8`);
with its default 9600 baud, 8N1, `*FX5,2` and `*FX8,7` printed
`SERIAL` intact over `-rs423 null_modem -bitb socket.127.0.0.1:PORT`.

## MAME's own printers

The Centronics slot can also hold emulations of real printers, several
of which Papyrium models: `fx80` (Epson FX-80), `lx800` (Epson LX-800),
`nlq401` (Schneider NLQ 401), and others. These run the printer's own
firmware, which needs its ROM, and draw the paper in a MAME window. They
are not a route to Papyrium, but they could serve as a test oracle for
Papyrium's models, run as a separate process; using those ROMs would be
Rob's decision.

## Collecting the output

- **Live, with no changes:** `mame bbcb -prin socket.127.0.0.1:9100`
  into `papyrium serve`, started first. The best route of any emulator
  here: live, faithful, and with backpressure.
- **Through a file:** `mame bbcb -prin NEW-FILE.prn`, followed with
  `papyrium serve -t file-follow -T filepath=NEW-FILE.prn -T
  from-start=yes`; the file must not exist before MAME starts.
- **Afterwards:** `papyrium print FILE.prn` prints the file as one job.

MAME is GPL-2.0 overall; the BBC drivers and these devices are
BSD-3-Clause.

## Trying it

MAME 0.289 (Homebrew) ran the `bbcb` set from the verified rompath that
Beebium's MAME oracle assembles (`oracle/mame/setup_roms.sh` in Beebium,
which gathers ROMs from other emulators). Each run was headless:

```
mame bbcb -rompath ROMPATH -video none -sound none -nothrottle \
  -seconds_to_run 25 -skip_gameinfo -window -nomax \
  -autoboot_delay 2 -autoboot_command 'VDU2:PRINT"HELLO":VDU3\n' \
  -prin socket.127.0.0.1:9100
```

MAME types the autoboot command at keyboard speed in emulated time, so a
longer command needs more `-seconds_to_run`; a run that ends before the
command is typed prints nothing, which looks like a lost connection but
is not. An `-autoboot_script` replaces the command.
