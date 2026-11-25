# BeebEm

BeebEm's printer output, read from the source of BeebEm for Windows
(version 4.23, commit `592226e`, April 2026) and of the macOS port
(commit `012ef83`, December 2025). The two share the printer code; the
differences are noted. Paths below are under `Src/` in either tree.

## The menus

Comms > Printer On/Off attaches the printer. Comms > Printer
Destination chooses where its bytes go: File..., Clipboard, or LPT1 to
LPT4. The destination can be changed only while the printer is off.

## What happens to a byte

Every write to the User VIA's output register A while the printer is on
sends the byte to the printer (`UserVia.cpp`, the `VIA_REG_ORA` case of
`UserVIAWrite`, calling `WriteToPrinter`). The data direction register
and the strobe are not consulted.

There is no busy line. 25 cycles after each byte, `PrinterPoll` raises
CA1, the acknowledge, and a fallback raises it every 100,000 cycles in
case the interrupt is missed. The printer is always ready, so the BBC
prints as fast as the operating system can drive the port, and nothing
outside the emulator can make it wait.

## File

Choosing File... shows a save dialog ("Select printer output file")
that does not warn about an existing file, because the file is appended
to, never replaced. The chosen path is kept in BeebEm's preferences
under `PrinterFile`, with `PrinterEnabled` and `PrinterPort`, so it can
also be set by editing the preferences file.

Turning the printer on opens the file with `fopen(path, "ab")`, appending
in binary mode (`PrinterEnable`, `UserVia.cpp`). It stays open until the
printer is turned off or the destination changes, and is then closed
(`PrinterDisable`). If the printer was on when BeebEm last saved its
preferences, the file is opened again at start-up. The file therefore
accumulates output across printer on/off and across BeebEm sessions.

Each byte is written with `fputc` and immediately `fflush`ed, so a
reader sees it at once. The bytes are exactly the BBC's: no translation
is applied to the file. A failed write reports an error, closes the
file, and leaves the printer on but printing nowhere until it is
toggled.

Turning the printer off and on writes nothing to the file: the file
holds no job boundaries.

## Clipboard

Bytes are collected in memory and copied to the clipboard one second
after the last one. When Translate CR/LF is on (the default), a line
feed is added after every carriage return (`BeebWin::PrintChar`,
`BeebWinIo.cpp`). Not useful to Papyrium.

Edit > Copy uses the printer to capture text: it switches the printer
destination to Clipboard and turns the printer on (`BeebWin::OnCopy`).
After using it, the destination must be set back to File.

## LPT1 to LPT4

These pass the name `LPT1` (and so on) to the same `fopen`. On Windows
that opens the parallel port device. On macOS it creates an ordinary
file of that name in BeebEm's current directory.

## Collecting the output

Point BeebEm's File destination at a file and have Papyrium follow it,
as `tail -f` does, with the `file-follow` transport
(`papyrium serve -t file-follow -T filepath=FILE`), which works like
this:

- Start at the file's current end by default, since it holds earlier
  sessions' output; optionally from the start, to replay it.
- Poll the file's size every 100 to 200 ms and read whatever lies past
  the last offset. This needs no platform-specific file watching and no
  dependency, and BeebEm's flush after every byte means polling is the
  only delay.
- If the file shrinks below the offset, or is replaced (its identity
  changes), start again from 0. If it does not exist yet, wait for it.
- Never write to or truncate the file. On Windows the C runtime's
  append mode seeks to the end before each write, so a truncation by
  another process races with BeebEm.
- The job ends on the spooler's idle timeout or the language's own
  boundaries; with no flow control and no job marks, the idle timeout
  usually decides.

The same transport serves any emulator that prints by appending to a
file.

### Named pipes, considered and set aside

Because the path goes straight to `fopen`, it could name a POSIX FIFO
or, on Windows, a named pipe such as `\\.\pipe\papyrium` (set in the
preferences file). That would give a stream with no file growing on
disc, but:

- on POSIX, opening a FIFO blocks until a reader opens it, which stalls
  BeebEm when the printer is turned on, and at start-up if it was left
  on;
- a full pipe blocks BeebEm's emulation thread;
- neither source tree ignores `SIGPIPE`, so if Papyrium exits, BeebEm's
  next printed byte would terminate it.

Following an ordinary file avoids all three.
