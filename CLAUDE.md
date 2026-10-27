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
name Scriptorium). Background design documents belong to Beebium and live
in its repository.

Printer behaviour comes from the manufacturers' manuals. They are
copyrighted, so they live uncommitted in `docs/local/` (ignored by git),
one directory per printer named for maker and model (`epson-fx80/`,
`brother-m1109/`, `star-lc10/`, ...). Each manual has a plain name, with
its text beside it as `<manual>.txt` and, for a scan OCRed with
`tools/manual-ocr/ocr.sh`, its page images and per-page text in
`<manual>-pages/`. What Papyrium takes from them is
restated in our own words, with page references, in committed notes:
`docs/epson-fx80.md` for the FX-80, `docs/epson-lx800.md` for the
LX-800, `docs/brother-m1109.md` for the Brother M-1109 and `docs/star-lc-10.md` for the Star LC-10 and LC-10
Colour. Check a behaviour question there, then
in the manual, before deciding it yourself, and record new findings there.
Where a printer's firmware has been read, what it shows is written up
beside them: `docs/star-lc10-firmware.md` for the LC-10.

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
- **Advertisers** announce a running printer on the network (multicast
  DNS). Each plug-in describes itself in neutral terms (a transport's
  endpoints, a model's and a language's identity) and only the advertiser
  knows its protocol's records.

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

- Where a printer claims to emulate another (the LC-10's Standard mode
  an Epson LX-800, its IBM mode an IBM Proprinter II), model the emulated
  printer first, from its own manual, and build the emulating printer on
  it as a variant: the copy is then measured against the original it
  copied, and the original is a model in its own right.
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

### Layout

A uv workspace of `packages/papyrium-*` members sharing the PEP 420
`papyrium` namespace (never add `src/papyrium/__init__.py`). The workspace
root is also the bare `papyrium` distribution, which ships no code: it
depends on `papyrium-cli` and every printer model and provides the
`papyrium` command; `papyrium-cli` alone brings no printer model. `README.md`
lists the packages. Entry-point groups are `papyrium.transport`,
`papyrium.language`, `papyrium.model`, `papyrium.font`,
`papyrium.output` and `papyrium.advertiser`. Positions on the page are whole units of 1/4320 inch
(`papyrium.core.page`). Golden captures and images for the FX-80 are in
`packages/papyrium-model-epson-fx80/tests/golden/`; the multicast DNS
test is in `integration/mdns/` (`uv run pytest integration/mdns`); Beebium end-to-end
tests are in `integration/beebium/` and are not part of `uv run pytest`.

## Development

- Python, managed with `uv` only: `uv add`, `uv run`, `uv run pytest`.
  `pyproject.toml` and `uv.lock` are committed; the root
  `pyproject.toml` pins PyPI as the index, so the lock never records a
  developer's private index, which CI cannot reach. Prefer pure-Python or
  wheel-only dependencies so Windows installs are painless.
- No platform-specific code in the core; platform specifics only in host
  printer output.
- Tests: `uv run pytest` (the default suite); `uv run pytest oracles/escapy`
  (EscaPy oracle, needs uvx); the Beebium end-to-end tests with the command
  in `integration/beebium/test_beebium_printing.py` (needs a Beebium build).
  Refresh golden images with `PAPYRIUM_UPDATE_GOLDEN=1 uv run pytest` and
  look at them before committing.
- **CI** (`.github/workflows/ci.yml`) runs the tests against wheels built
  from every package, installed over a `uv sync --no-install-workspace`
  environment and run with `uv run --no-sync` (a plain `uv run` would
  reinstate the editable installs), on Linux, macOS and Windows. A test
  that reads files from the source tree rather than the installed package
  passes locally and fails there.
- **Releases** (Rob decides when, and the version): every distribution
  shares one version. `uv run bump-my-version bump minor` (or `major`,
  `patch`) bumps it everywhere, relocks, commits "Bump papyrium to X" and
  tags `vX`; pushing the tag runs `.github/workflows/release.yml`, which
  runs the CI workflow, checks the tag matches the version, builds every
  distribution and publishes them to PyPI with the `PYPI_TOKEN` secret.
  Builds are reproducible (`SOURCE_DATE_EPOCH` from the tagged commit)
  and files already on PyPI are left out, so a release that stopped part
  way, as when PyPI limits new projects, is resumed with
  `gh workflow run release.yml -f tag=vX`.
- **Every printer model has a demonstration page**, `demo()`: a job we
  write ourselves (in its package's `demo.py`, with
  `papyrium.language.escp.writing` for ESC/P) that shows the printer at
  its best. The conformance suite checks it prints without warnings, each
  model pins it as golden pages, its README and the root README's
  gallery show it, and `papyrium demo MODEL` prints it.
- **Generated READMEs.** `README.md`, the printer models' READMEs and
  `docs/images/` are rendered by `scripts/render_readme.py` from Jinja2
  templates (`scripts/readme-templates/`, `packages/*/readme/`), running
  `scripts/readme-examples/` against the workspace. Edit the templates,
  never the READMEs; the pre-commit hook (`uv run pre-commit install`)
  regenerates them and fails the commit until they are staged.
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
- **Naming**: `_filename`, `_filepath`, `_dirpath`, `_dirname` suffixes,
  never `_file` or `_dir`.
- **Ubiquitous language**: transport, language, printer model, output,
  job, page, capture, used identically in code, CLI, API and docs.
- **Comments describe the present**, not the history of the code.
- **No defensive locking**; design ownership so a mutex is needed only
  where two threads genuinely share state.
- **No backward compatibility** before 1.0; change the API freely.
- **Never silently discard a failure**; log why.
- **No copyrighted material** without Rob's decision: no ROM images or
  dumps, commercial software or its output, and no manuals. Test captures come from BASIC programs
  this project writes itself. Fonts are kept as swappable data.
- **Own implementations, others by licence.** Papyrium's languages are
  implemented from public documentation (printer manuals, specifications).
  Whether another implementation's code may be reused depends on its
  licence, which Rob decides case by case: permissively licensed code
  (MIT, BSD, Apache-2.0) may be adapted with its notice kept; anything
  else, such as GPL or AGPL code (EscaPy, Ghostscript), is used only as a
  test oracle: run as a separate process, never imported, never
  distributed, never read as a basis for our code. Compare layout and
  behaviour, not pixels, where an oracle renders differently (EscaPy uses
  outline fonts).
- Ghostscript, if used for a PostScript model, runs as a subprocess the
  user installs; never link `libgs`. Any plug-in that imports AGPL code is
  a separately distributed package and needs Rob's licence decision.
- Fonts (dot fonts, and outline fonts for daisywheel print wheels) are
  our own design, carry a licence that permits redistribution, or are
  reconstructions of a printer's characters from its printed output, as
  `m1109-draft` is from the M-1109 manual's pages (`tools/m1109-glyphs/`).
  Whether a printer's ROM may be used, for its characters or otherwise,
  is Rob's decision, case by case (yes for the LX-800's, which gives
  `lx800-draft` and `lx800-nlq-roman` through `tools/lx800-rom/`, and for
  the LC-10 Colour's, for everything needed to simulate the LC-10 and
  LC-10 Colour, which gives `papyrium-font-lc10` through
  `tools/lc10-rom/`); without it, a reconstruction never
  comes from reading a ROM, and no ROM image is ever committed.
- Do not modify anything under `/Users/rjs/Code/beebium`; ask
  beebium-architect about Beebium's behaviour.
