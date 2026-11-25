# jsbeeb

jsbeeb's printer output, read from upstream's source (commit `0fc23ea8`,
25 November 2026, version 2.26.0). Paths below are under `src/`. The
printer is `printer.js`; it is wired to the user VIA in `6502.js`
(`resetPeripherals`) and `web/machine.js`, and shown by
`web/front-panel.js`.

jsbeeb runs in a web browser, and also as an Electron desktop app
(`app/`) that loads the same page.

## The printer

A printer is always attached; there is no menu to turn it on. The first
time the BBC prints, a notice says output is being kept, and Alt-B opens
the printer window: a pop-up holding a text area that shows the output
so far and grows as the BBC prints. There is no menu, no file, and no
way to save or copy the output except selecting it in the text area.

## What happens to a byte

The printer watches CA2 (`ca2changecallback`, called by `setca2` in
`via.js`). When CA2 is an output and falls, the strobe, it pulses CA1
low and high, the acknowledge, and takes the byte in the user VIA's
output register A (`Printer.outputStrobe`). The acknowledge is
immediate and the printer is never busy, so the BBC prints at full
speed.

Each byte becomes one character of a JavaScript string
(`String.fromCharCode`), so all eight bits survive, and is dispatched as
an `output` event. The printer keeps only the most recent 64K characters
(`MaxBufferedChars`), for showing when the window is opened. While
jsbeeb replays emulation after a rewind, bytes are acknowledged but not
kept, so a rewind does not print a job twice.

The window is the only listener. It appends each character to the text
area's value. A text area is no capture: it normalises line endings
(a lone CR becomes LF) and shows control codes as they fall, so even
copying the text out does not recover the bytes the BBC sent.

## Collecting the output

There is no route as jsbeeb stands: nothing it does with printed bytes
leaves the page in a usable form.

The `output` event is the natural hook for a change to jsbeeb. Every
byte the printer accepts passes through it, in order, unaltered, and
it is not raised during rewind replay. Something listening to it could
send the bytes on:

- **In the Electron app**, through the preload bridge to the main
  process (`app/preload.js`, which already carries the VDFS file
  calls), which can open a TCP connection to port 9100, served by the
  existing `raw-tcp` transport, or append to a file, followed as for
  BeebEm ([beebem.md](beebem.md)). This works with Papyrium as it is.
- **In a browser**, which cannot open raw TCP connections or write to an
  arbitrary file, over a WebSocket (or HTTP) to a Papyrium transport
  that accepts one. A page served over HTTPS may reach `ws://localhost`
  in Chrome and Firefox, which treat loopback as secure, though recent
  Chrome asks the user's permission before a public site reaches the
  local network. Safari's behaviour needs checking.
- **In either**, a "save printer output" action writing the bytes (kept
  as bytes, not text) to a downloaded file, which Papyrium would read as
  one job, as for b2 ([b2.md](b2.md)). The simplest change, but not live.

The jsbeeb printer acknowledges every byte at once, so none of these
gives backpressure unless the printer is changed to hold the acknowledge
until the bytes are sent.

jsbeeb is GPL-3.0-or-later. Any of these would be a change proposed to
its maintainer; whether to pursue it is Rob's decision.
