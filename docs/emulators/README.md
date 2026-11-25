# Emulators

How BBC Micro emulators deliver what the emulated machine prints, and
how Papyrium can collect it. Each note below reads one emulator's source,
describes what its printer port does with the bytes, and proposes how a
Papyrium transport (or a change to the emulator) would take them in.

| Emulator | Note | Output | Live? | Papyrium route |
|---|---|---|---|---|
| Beebium | (Beebium's repository) | raw TCP to a print server | yes | `raw-tcp` transport |
| BeebEm | [beebem.md](beebem.md) | appends to a chosen file | yes | `file-follow` transport |
| b2 | [b2.md](b2.md) | in-memory buffer, saved by hand | no | `papyrium print` (or `send`) a saved buffer; or patch b2 to stream |
| B-em | [b-em.md](b-em.md) | appends to a file, or pipes to a command | yes, but buffered | `file-follow`; or fix B-em's command printing |
| jsbeeb | [jsbeeb.md](jsbeeb.md) | a text area in a pop-up window | no | set aside: browser-based, a poor fit for Papyrium |
| beebjit | [beebjit.md](beebjit.md) | truncates a fixed file, CR made LF | yes, but buffered | `file-follow`, text only; or patch beebjit |
| MAME | [mame.md](mame.md) | a file, or a TCP connection (`-prin socket.HOST:PORT`) | yes | `raw-tcp`, unchanged; or `file-follow` |

## What the emulator owes Papyrium

Whatever the delivery, Papyrium needs the bytes the BBC put on the
printer port, unaltered: every byte on port A of the User VIA that the
emulated printer accepted, in order, all eight bits, with no line-ending
translation. Each emulator note says whether its output is that.

## Patterns so far

- **Few push back.** Most emulators never let the reader stall the
  BBC. BeebEm acknowledges each byte immediately; b2 emulates the
  handshake but its printer is never busy for longer than a few cycles;
  B-em acknowledges at once. Only Beebium and MAME, over TCP, have real
  backpressure (B-em's command printing would, through a pipe, if it
  worked). A transport for the others needs no flow control, and the
  BBC prints at full speed.
- **Output may lag.** BeebEm flushes every byte; B-em and beebjit never
  flush, so a file they write grows in blocks and the end of a job can
  stay in the emulator until printing is turned off or it exits. A
  follower must not assume the file is complete when it stops growing.
- **Text modes are no use.** Several emulators offer a "text" or
  clipboard destination that translates line endings and the pound
  sign. Papyrium needs the binary or raw destination every time.
  beebjit has only a translating one (CR becomes LF).
- **Files are appended to or truncated.** BeebEm and B-em append, so a
  follower starts at the end; beebjit truncates at each run's first
  byte, which a follower sees only as the file shrinking.
- **No job boundaries in the stream.** Turning the emulated printer off
  and on leaves no mark in the bytes. Jobs end by the spooler's idle
  timeout and by the language's own boundaries (form feed), as the
  domain rules already say.
- **Files are the common denominator.** An emulator without a network
  printer still writes bytes to a file, either continuously (BeebEm) or
  on request (b2), or both (B-em). The `file-follow` transport follows
  a growing file; `papyrium print` prints a finished file as one job,
  and `papyrium send` sends it to a running printer.
- **A command's standard input is the next best thing to a socket.**
  B-em can pipe printer output to a command (once fixed). `papyrium
  send -` forwards its standard input to a running printer's raw TCP
  port, on every platform, so it serves any emulator that can do this;
  `papyrium print -` prints it as one job without a running printer.
- **A browser can reach Papyrium only over the web's own protocols.**
  jsbeeb in a browser can open neither a raw TCP connection nor a file
  of its choosing; a WebSocket (or HTTP) transport would be the way in.
  Its Electron app, with Node in the main process, can use `raw-tcp`.
