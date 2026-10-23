# CLAUDE.md

Guidance for working in the Papyrium repository.

## What Papyrium is

A general-purpose virtual vintage printer, run as a headless,
cross-platform service. It receives the byte stream a computer sends to
its printer, interprets it as a chosen period printer would, lays the
result out on emulated paper, and delivers pages as files, to a host
printer, or to a preview client. Beebium (the BBC Micro emulator at
`/Users/rjs/Code/beebium`) is its first client, but any emulator, or real
hardware behind a network adapter, can drive it. Papyrium knows nothing
about the computer on the other end; the computer's port belongs to the
emulator.

The design starts from `docs/specification.md` (written under the earlier
name Scriptorium). Background from Beebium is in `docs/beebium/`; those
files are verbatim copies and are exempt from the ASCII rule below.

## Architecture

Independent, pluggable axes, each chosen by configuration:

- **Transports** deliver bytes and know no printer language: raw TCP on
  9100 (a parallel connection), RFC 2217 (a serial connection, with its
  own XON/XOFF or RTS/CTS flow control), file and stdin.
- **Printer languages** are interpreters: ESC/P, Diablo 630, PostScript
  (via Ghostscript), HP-GL.
- **Printer models** are what the user selects. A language is not a
  model: the Epson FX-80 and Panasonic KX-P1180 share the ESC/P
  interpreter but differ in character ROM, command subset, printable area
  and mechanics.
- **Outputs** are backends over an intermediate page model, not PDF: PNG,
  PDF, host printing, preview. Dot-matrix output keeps its dots;
  PostScript and plotters keep their vectors.

One printer instance has one mechanism; serial and parallel are
alternative configurations of it, and several instances may run side by
side. A management API, separate from the data transports, handles jobs,
model selection, status and page retrieval. The service is the single
source of truth; clients display what it reports.

Each axis is a plug-in extension point discovered through entry points
(the `oaknut-extension` pattern from `/Users/rjs/Code/oaknut/packages`),
so each transport, language, model and output can be an independently
distributable `papyrium-*` package. Each axis has a conformance suite in
core that plug-in packages subclass in their own tests.

### Domain rules

- Connection lifetime is not job lifetime. A disconnect never ends a job.
- Every byte is appended to the job's raw `.prn` capture before
  interpretation. A capture replayed with the same model configuration
  must give byte-identical pages.
- The spooler owns only language-independent job rules (idle timeout,
  explicit end-job). Page and job boundaries defined by a language (form
  feed, `showpage`) come back from the model.
- The sender can stop and resume at any time; time nothing except the
  optional idle timeout.
- A BBC sends CR-only line ends by default (LF then CR with `*FX6,0`);
  the FX-80 auto line feed DIP switch is modelled.

## Development

- Python, managed with `uv` only: `uv add`, `uv run`, `uv run pytest`.
  `pyproject.toml` and `uv.lock` are committed. Prefer pure-Python or
  wheel-only dependencies so Windows installs are painless.
- No platform-specific code in the core; platform specifics only in host
  printer output.
- **asyncio** for everything that waits: transports, the spooler and its
  bounded buffer (backpressure), timers, the management API, the serve
  loop. Languages, models and outputs are synchronous, deterministic
  functions of the captured bytes, run off the event loop by the server,
  so replay is identical whatever delivered the bytes.
- Packages follow the oaknut family (`/Users/rjs/Code/oaknut/packages`):
  `papyrium-exception` (error hierarchy, exit codes, `handled_errors`),
  `papyrium-extension` (entry-point axes), a conformance suite per axis.
- **CLI** with Click, following `oaknut-econet-host` and `oaknut-disc`: a
  root group whose commands run inside `handled_errors` with `--debug`,
  `use_plain_help`, and asyoulikeit `@report_output` on every command
  that reports something, so it gets pretty, TSV and JSON output.

## Practices

- **Test first.** Write the failing test, make it pass, then refactor.
  `.prn` replay with golden page images is the backbone: every
  interpreter feature gets a small capture and a pinned rendering.
- **Refactor first.** When a change is hard, first make the change easy
  (refactor, keep green), then make the easy change. Progress slowing
  down is the signal of accidental complexity.
- **Targeted tests per commit**; the full suite is the pre-push gate.
- **Commit as you go**, fast-forward on master; no throwaway branches;
  worktrees for parallel work.
- **Commit messages**: imperative title, a body saying why, no AI or model
  names, no emojis; attribution trailers at the end are allowed.
- **Never `git push`.** Rob pushes. Rob decides release timing and
  version numbers.
- **7-bit ASCII** in source and docs.
- **Naming**: `_filename`, `_filepath`, `_dirpath`, `_dirname` suffixes,
  never `_file` or `_dir`.
- **Ubiquitous language**: transport, language, printer model, output,
  job, page, capture, used identically in code, CLI, API and docs.
- **Comments describe the present**, not the history of the code.
- **No defensive locking**; design ownership so a mutex is needed only
  where two threads genuinely share state.
- **No backward compatibility** before 1.0; change the API freely.
- **Never silently discard a failure**; log why.
- **No copyrighted material**: no printer ROMs (Epson's character ROM
  included), commercial software or its output. Test captures come from
  BASIC programs this project writes itself. Fonts are self-designed or
  permissively licensed, kept as swappable data.
- EscaPy (PyPI `pyscape`, AGPL-3.0) may be run as an external comparison
  oracle; no code is incorporated without Rob's licence decision.
- Do not modify anything under `/Users/rjs/Code/beebium`; ask
  beebium-architect about Beebium's behaviour.
