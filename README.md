# Papyrium

Papyrium is a virtual vintage printer. It runs as a headless service,
receives the bytes a computer sends to its printer, interprets them as a
chosen period printer would, lays the result out on emulated paper, and
writes the pages as PNG images and PDF documents.

The first printer is an Epson FX-80 9-pin dot-matrix printer speaking
ESC/P, and the first client is Beebium, the BBC Micro emulator. Papyrium
knows nothing about the computer on the other end: any emulator, or real
hardware behind a network adapter, can drive it.

## Quick start

From a checkout, with [uv](https://docs.astral.sh/uv/):

```sh
uv sync
uv run papyrium serve
```

This listens on `localhost:9100` (raw TCP, the JetDirect convention) as an
Epson FX-80, and writes each job into `papyrium-jobs/job-NNNN/`:

| File | Contents |
|---|---|
| `capture.prn` | Every byte received, exactly as sent |
| `job.json` | When the job started and ended, why it ended, and the printer setup |
| `page-0001.png`, ... | Each page, written as the paper is ejected |
| `job.pdf` | The whole job, written when the job ends |

Print something to it:

```sh
printf 'HELLO FROM PAPYRIUM\r\n\x0c' | nc localhost 9100
```

A job ends after five seconds without bytes (`--idle-timeout`), or when
the service stops. A disconnect never ends a job: an emulator may hold one
connection open for its whole life.

## Printing from a BBC Micro in Beebium

```sh
uv run papyrium serve
/path/to/beebium/build/src/server/beebium-model-b --tcp-printer host=localhost:port=9100
```

On the BBC:

```
*FX6,0
*FX5,1
VDU 2
PRINT "HELLO"
VDU 1,12
VDU 3
```

`*FX5,1` selects the parallel printer. The BBC normally suppresses line
feeds to the printer and sends CR alone; `*FX6,0` lets them through. If you
would rather leave the BBC at its defaults, switch on the FX-80's auto line
feed DIP switch instead:

```sh
uv run papyrium serve -M auto-line-feed=yes
```

Escape sequences go to the printer with `VDU 1`, so `VDU 1,27,1,69` turns
on emphasized printing (`ESC E`).

## Commands

| Command | Purpose |
|---|---|
| `papyrium serve` | Run a printer until interrupted |
| `papyrium render JOB_OR_CAPTURE` | Print a captured job again, from a job directory or a `.prn` file |
| `papyrium list-jobs` | List captured jobs |
| `papyrium list-models`, `describe-model NAME` | The printer models installed, and their options |
| `papyrium list-transports`, `list-languages`, `list-fonts`, `list-outputs` | The other plug-ins installed |

Options are passed as `KEY=VALUE`: `-T` for the transport (`-T port=9101`),
`-M` for the printer model (`-M character-set=uk`), and
`-O OUTPUT.KEY=VALUE` for an output (`-O png.dpi=300`). Choose outputs with
`-o png -o pdf`. Reports such as `list-jobs` print as a table, or as TSV or
JSON with `--as tsv` or `--as json`.

Replaying a capture with the same printer setup always gives identical
pages; `render` on a job directory uses the setup recorded in its
`job.json`.

## How it is built

Papyrium is a framework of independent, pluggable axes, each an entry-point
extension point that separately distributable `papyrium-*` packages can
add to:

| Axis | Plug-ins so far |
|---|---|
| Transports deliver bytes | `raw-tcp` |
| Languages interpret them | `escp` |
| Printer models are what the user chooses | `epson-fx80` |
| Fonts stand in for character ROMs | `draft-9`, an original 9-pin design |
| Outputs write pages | `png`, `pdf` |

The packages live under `packages/`:

| Package | Contents |
|---|---|
| `papyrium-exception` | Error hierarchy, exit codes, the CLI error boundary |
| `papyrium-extension` | Entry-point plug-in machinery |
| `papyrium-core` | The axes and their conformance suites, the page model, the spooler and job captures, rendering |
| `papyrium-transport-raw-tcp` | Port 9100 raw TCP |
| `papyrium-language-escp` | An incremental ESC/P interpreter for 9-pin printers |
| `papyrium-font-draft-9` | The draft-9 dot font |
| `papyrium-model-epson-fx80` | The Epson FX-80 |
| `papyrium-output-png` | PNG pages |
| `papyrium-output-pdf` | PDF documents of vector dots |
| `papyrium-cli` | The `papyrium` command |

`docs/specification.md` is the design as handed over from Beebium, and
`CLAUDE.md` records the working practices.

## Tests

```sh
uv run pytest
```

The FX-80's golden tests replay the captures in
`packages/papyrium-model-epson-fx80/tests/golden/` and compare every page
with a pinned image. The end-to-end tests that drive a real Beebium BBC
Micro are in `integration/beebium/`; their module docstring gives the
command to run them. `oracles/` compares Papyrium with independent
interpreters run as separate programs: `uv run pytest oracles/escapy`.
