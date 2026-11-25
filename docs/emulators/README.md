# Emulators

How BBC Micro emulators deliver what the emulated machine prints, and
how Papyrium can collect it. Each note below reads one emulator's source,
describes what its printer port does with the bytes, and proposes how a
Papyrium transport (or a change to the emulator) would take them in.

| Emulator | Note | Output | Live? | Papyrium route |
|---|---|---|---|---|
| Beebium | (Beebium's repository) | raw TCP to a print server | yes | `raw-tcp` transport |
| BeebEm | [beebem.md](beebem.md) | appends to a chosen file | yes | follow the file (proposed) |
| b2 | [b2.md](b2.md) | in-memory buffer, saved by hand | no | read a saved file as one job; or patch b2 to stream |

## What the emulator owes Papyrium

Whatever the delivery, Papyrium needs the bytes the BBC put on the
printer port, unaltered: every byte on port A of the User VIA that the
emulated printer accepted, in order, all eight bits, with no line-ending
translation. Each emulator note says whether its output is that.

## Patterns so far

- **Nothing pushes back.** No emulator yet lets the reader stall the
  BBC. BeebEm acknowledges each byte immediately; b2 emulates the
  handshake but its printer is never busy for longer than a few cycles.
  Only Beebium, over TCP, has real backpressure. A transport for the
  others needs no flow control, and the BBC prints at full speed.
- **No job boundaries in the stream.** Turning the emulated printer off
  and on leaves no mark in the bytes. Jobs end by the spooler's idle
  timeout and by the language's own boundaries (form feed), as the
  domain rules already say.
- **Files are the common denominator.** An emulator without a network
  printer still writes bytes to a file, either continuously (BeebEm) or
  on request (b2). Two file transports cover these: one that follows a
  growing file, one that reads a finished file as a single job.
