# Scriptorium: specification as handed over from Beebium

The project has since been renamed Papyrium. This document keeps the
name it was written under; read Scriptorium as Papyrium throughout.

Scriptorium is a dot-matrix printer emulator that runs as a headless
service. It receives the byte stream a computer sends to a parallel
printer, interprets it as a period printer would (an Epson FX-80 class
ESC/P printer first), lays the result out on emulated paper, and delivers
pages as files, to a host printer, or to a future preview window.

This document is the state of the design as it stood in the Beebium
project on 2026-10-23, when the printer emulator was split out into its
own repository under the name Scriptorium (earlier working name:
Printium). It is a starting point, not a contract: the Scriptorium
developer owns the design from here and should refine it as the code
teaches them.

## 1. Where Scriptorium sits

Three concerns, three owners. Beebium keeps the first; Scriptorium is the
third; the second is the link between them.

| Concern | Owner |
|---------|-------|
| The port: the BBC Micro's printer connector, strobe/ack timing, the guest stalling when the printer is busy or absent | Beebium core (`PrinterPort`, `CentronicsReceiver`) |
| The sink: where the bytes go | Beebium extensions on the `printer-port` attachment point: `file-printer`, `tcp-printer`, `host-parallel-printer` |
| The printer: a command language, a character ROM, paper, output documents | Scriptorium |

Beebium contains no printer-language code and must stay that way.
Scriptorium contains no knowledge of the BBC Micro, the 6522 VIA or
Beebium's protocols; it is a printer that happens to be reached over a
socket, and any machine emulator (or a real machine behind a
USB-to-Centronics adapter and a small bridge) can drive it.

## 2. The link: a raw TCP byte stream

- Scriptorium listens on a TCP port. The default is 9100, the JetDirect
  convention, which also lets it stand in for a network printer for any
  host software that speaks raw 9100.
- What crosses is the bytes the computer sent to its printer port, 8-bit,
  unframed, in order. There is no protocol, no header, no job marker.
- A connection's lifetime says nothing about jobs. Beebium's `tcp-printer`
  connects at machine launch and holds the connection open for the life
  of the machine, reconnecting every second if it drops. A disconnect is
  not a form feed and not an end of document. Equally, several
  connections in sequence may be one document.
- Scriptorium must accept bytes at any rate and never block the sender
  for long. In Beebium a printer that does not read stalls the emulated
  machine (the guest waits for /ACK), which is faithful but makes slow
  readers very visible.
- Scriptorium being down is harmless to Beebium: the BBC's print simply
  waits, as it would for a switched-off printer, and resumes when
  Scriptorium comes up.

### What a BBC Micro actually sends

- Lines end in CR alone by default. The MOS (`*FX6,10`) suppresses LF to
  the printer; with `*FX6,0` the BBC sends LF then CR, in that order.
  A real FX-80 treats CR as carriage return only, unless its auto-LF DIP
  switch is set. Scriptorium needs an "auto line feed on CR" option that
  models that switch, and it should probably default on for the BBC case
  so that `PRINT` lines do not overprint.
- Form feed (0x0C, `VDU 1,12` on the BBC) ejects the page. Software
  that never sends one leaves a part-filled page; see job boundaries.
- Software such as View, Wordwise, InterWord and screen-dump utilities
  emits FX-80 escape sequences: bold, underline, condensed, elite,
  proportional, superscript, line spacing, and bit-image graphics
  (`ESC K`, `ESC L`, `ESC Y`, `ESC Z`, `ESC *`).
- Bytes may have bit 7 set (italic/graphics on the FX-80 character set).
- The emulated machine can stop and resume at any time. Scriptorium must
  not time anything on the assumption of continuous flow except for the
  optional idle job-end rule below.

## 3. Architecture

### The breadth first

Scriptorium is a general-purpose virtual vintage printer, not an ESC/P to
PDF converter. The tail of `docs/beebium/printing-architecture.md` (from
the prompt "I'm familiar with RFC2217" to the end) settles this and is
the authoritative statement of scope. In summary:

```
Transports                Printer models                 Outputs
  raw TCP (9100)            Epson FX-80 (ESC/P)            PDF
  RFC 2217 (serial)         Panasonic KX-P1180 (ESC/P)     raster image (PNG)
  file / stdin              daisywheel (Diablo 630 codes)  host printing
                            PostScript (via Ghostscript)   preview / API
                            HP 7475A plotter (HP-GL)
```

- **Transport, printer model and rendering backend are independent
  layers**, chosen by configuration. Nothing in a transport knows the
  language; nothing in a model knows where the bytes came from or where
  the pages go.
- **A printer language is not a printer model.** The FX-80 and KX-P1180
  share most of an ESC/P interpreter but differ in character ROM,
  command subset, printable area and mechanics. Models share language
  interpreters; a model is the thing the user selects.
- **One mechanism per instance.** A real printer is connected by serial
  or by parallel, never both at once feeding one head. Serial and
  parallel transports are alternative configurations of one printer
  instance; several instances may run side by side.
- **Serial transport has its own flow control** (XON/XOFF or RTS/CTS),
  which RFC 2217 can carry; parallel flow control is Beebium's problem
  and never reaches Scriptorium. The BBC drives a serial printer with
  `*FX5,2`, and Beebium's `rfc2217-client-serial` extension is the
  existing bridge, so the RFC 2217 transport makes Scriptorium reachable
  from the BBC's RS423 port with no new Beebium work.
- **The page representation is not PDF.** An intermediate page model
  lets dot-matrix output keep its dots and a PostScript model keep its
  vectors, with PDF, raster and host printing as backends over it.
- **A management API** for jobs, model selection and retrieving pages,
  separate from the data transports.
- Scriptorium serves any emulator, or real hardware behind a network
  adapter; Beebium is merely its first client.

The milestones in section 5 start with raw TCP, the FX-80 and PNG
because that is the shortest path to something useful, not because the
project is any narrower than the table above. Every seam introduced in
milestone 1 and 2 should be shaped so that a second transport, a second
model and a second output slot in without reworking the first.

### The layers

Layers, each with a seam that can be tested alone:

```
transport  ->  spooler  ->  interpreter  ->  page model  ->  renderers  ->  outputs
(TCP 9100)    (raw .prn    (ESC/P parser   (dots, paper    (PNG, PDF,    (directory,
 file, stdin)  capture,     and printer     motion, page    preview)      host printer,
               job rules)   state)          boundaries)                   API events)
```

1. **Transport.** A TCP listener on a configurable port; also a file
   replay and stdin, so a captured job can be re-run without any
   emulator. Several clients may connect over time; one at a time is
   enough initially.
2. **Spooler and job boundaries.** Every byte received is appended to a
   raw capture (`.prn`) for the current job before anything interprets
   it. The raw capture is the reproducibility mechanism: a `.prn` file
   replayed through Scriptorium must give byte-identical page output,
   and the test suite is built on this. Job boundaries:
   - a form feed is always a page boundary, never by itself a job end;
   - an idle timeout (configurable, default a few seconds, 0 = never)
     ends the job and flushes the part-filled page;
   - an explicit end-job request through the API or CLI;
   - optionally, a page count.
3. **Interpreter.** A parser for the FX-80 command set (ESC/P, not
   ESC/P2 and not ESC/POS) driving a printer model: current column, line
   spacing, pitch, emphasis flags, margins, tabs, character set, and
   the print head. The model emits an intermediate representation: dot
   placements at printer resolution, paper motion, page breaks. Target
   one specific historical printer and its DIP switches rather than
   "all of ESC/P"; the FX-80 manual is the reference, and the Panasonic
   KX-P1180 is a second model to consider later.
4. **Page model.** Continuous fanfold stationery, 9.5 in wide (8.5 in
   between the tear-off strips), 11 in long, 66 lines at 6 lpi, 80 columns at 10 cpi, 9-pin head, 240 dpi
   horizontal in the densest mode, 72 dpi vertical (n/72 line spacing
   with n/216 fine spacing). Page size, resolution and character ROM
   belong to the printer model, not the renderer.
5. **Renderers.** PNG first (one image per page, dots as dots). PDF next,
   either as vector dots or an embedded bitmap, and optionally a
   "logical" rendering using host fonts for searchable text later. A
   live preview is a renderer that streams pages or partial pages to a
   client.
6. **Outputs.** A directory of numbered jobs and pages; a host printer via
   the platform print system (CUPS `lp` on macOS/Linux, the Windows
   spooler); the API's event stream.

### Character ROM

The FX-80's glyphs are Epson's. Do not copy its character ROM. Either
design a 9-row dot font in the FX-80 style (it is about 96 glyphs plus
the italic and international variants, well within reach) or adopt a
permissively licensed bitmap font with a suitable look, and keep the font
as data so the user can swap it. The exact FX-80 appearance is a goal,
pixel identity with the real ROM is not.

### Reference implementation and licence

EscaPy (PyPI `pyscape`, AGPL-3.0) is an existing Python ESC/P and ESC/P2
to PDF interpreter, about 12,000 lines with tests. It is worth running as
a comparison oracle: feed the same `.prn` to both and diff. Whether any of
its code is incorporated is a licence decision for Rob (Scriptorium's
licence is not yet chosen; GPL-3.0 was considered acceptable for Beebium
components). If EscaPy is used, it is as an external converter or under
its licence; it must not leak into Beebium.

## 4. Service shape

Scriptorium is a headless service, like a Beebium server, with:

- a CLI to start it (`scriptorium serve --port 9100 --output-dir ...`),
  replay a capture (`scriptorium render job.prn --png out/`), and query
  or end jobs;
- a control API for configuration, status (online, bytes received,
  current job, pages so far), job events, and page images for a preview,
  so that a GUI can be built later without changing the core. Beebium
  uses gRPC with protobuf for this and a Python client is natural; a
  simpler HTTP+JSON API is acceptable if gRPC is more machinery than the
  project needs. Either way the service, not the client, is the single
  source of truth: a GUI displays what the service reports and never
  computes printer state itself;
- cross-platform operation on macOS, Linux and Windows with no
  platform-specific core code; platform specifics only in the host
  printer output.

Python is an acceptable implementation language. If Python, the project
must be managed with `uv` (`uv init`, `uv add`, `uv run`), with a
`pyproject.toml`, a pinned lock file, and tests run with `uv run pytest`.
Prefer pure-Python or wheel-only dependencies so Windows installs are
painless.

## 5. Milestones

Each milestone is a usable thing on its own and lands as fast-forward
commits on master.

1. **Spooler.** TCP listener, raw `.prn` capture per job, job boundary
   rules, CLI `serve`. Test with `nc` and with Beebium (section 7). Exit
   criterion: a BBC `PRINT "HELLO"` with `*FX6,0` yields a `.prn` holding
   `HELLO` LF CR.
2. **Text interpreter and PNG.** FX-80 text subset: CR, LF, FF, tabs,
   pitch, emphasis, underline, line spacing, margins, the character set.
   Page model and PNG renderer. Exit criterion: a page of BASIC `PRINT`
   output renders as a readable 9-pin page image, byte-identical on
   replay.
3. **Graphics.** The bit-image modes. Exit criterion: a BBC screen dump
   (a BASIC program that reads the screen with POINT and emits `ESC K`
   rows is sufficient and avoids any copyrighted dump utility) renders.
4. **PDF output** and job/page management in the API.
5. **Control API and status**, enough for a preview client to list jobs
   and fetch pages.
6. **Host printing** through the platform print system.

## 6. Practices carried over from Beebium

These are the habits that have worked well and should be in
Scriptorium's own CLAUDE.md from day one.

- **Test first.** Write the failing test, make it pass, then refactor.
  The `.prn` replay with golden page images is the backbone: every
  interpreter feature gets a small capture and a pinned rendering.
- **Refactor first.** When a change is hard, first make the change easy
  (refactor, keep green), then make the easy change. Progress slowing
  down is the signal of accidental complexity.
- **Targeted tests per commit**; the full suite is the pre-push gate.
- **Fast-forward merges** on master; no throwaway branches; worktrees
  for parallel work.
- **Commit messages**: imperative title, a body saying why, no AI or
  model names in the body, no emojis; attribution trailers at the end
  are allowed. Never `git push`; Rob pushes.
- **Naming**: `_filename`, `_filepath`, `_dirpath`, `_dirname` suffixes,
  never `_file` or `_dir`.
- **Ubiquitous language**: pick names (job, page, capture, printer model,
  renderer) and use them identically in code, CLI, API and docs.
- **Comments describe the present**, not the history of the code.
- **No defensive locking**; design ownership so a mutex is needed only
  where two threads genuinely share state.
- **No backward compatibility** obligations before 1.0; change the API
  freely rather than carry shims.
- **Never silently discard a failure**; log why.
- **Copyrighted material** (printer ROMs, commercial BBC software, their
  outputs) is never committed. Test captures come from BASIC programs
  the project writes itself.
- Rob decides release timing and version numbers.

## 7. Driving it from Beebium

Beebium is at `/Users/rjs/Code/beebium`. A current build is in
`build/src/server/` (servers) with plugins under
`build/src/server/extensions/`.

- Launch a Model B printing to Scriptorium:
  `build/src/server/beebium-model-b --tcp-printer host=localhost:port=9100`
  (parameters are colon-separated; `url=socket://host:port` also works).
- Capture without Scriptorium, as the oracle for what the BBC sends:
  `build/src/server/beebium-model-b --file-printer path=job.prn`.
- On the BBC: `*FX6,0` (let LF through), `*FX5,1` (parallel printer),
  `VDU 2` (printer on), `PRINT "HELLO"`, `VDU 1,12` (form feed),
  `VDU 3` (printer off).
- The Python client in `clients/beebium-python-client` types into the
  machine and polls the screen; its `tests/test_tcp_printer.py` is a
  worked example of launching a server with `--tcp-printer`, accepting
  the connection and asserting the bytes. Run such tests with
  `BEEBIUM_SERVER=/Users/rjs/Code/beebium/build/src/server/beebium-model-b uv run pytest`
  from that directory.

## 8. Documents to copy from Beebium

Take copies into this repository's `docs/` (they are the design record,
and Beebium's may move):

- `docs/discussion/printing-architecture.md`: the original design
  conversation (currently staged, uncommitted, in the Beebium checkout).
- `docs/printer-port.md`: the port model and the sinks, including
  exactly how `tcp-printer` behaves on connect and disconnect.
- `docs/cli.md`, the "Printer" subsection: the sink parameters.
- `CLAUDE.md`: as the model for Scriptorium's own, scaled down.
- `docs/manuals_text/`: the Advanced User Guide chapter on the printer
  port and the User Guide's printer section, for what the BBC sends.

Not in Beebium, but needed: the Epson FX-80 user manual (command set and
DIP switches), available in scanned and transcribed form online.
