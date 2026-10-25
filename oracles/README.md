# Oracles

Independent implementations used to check Papyrium's behaviour. Each is
run as a separate program, never imported into Papyrium, never
distributed with it, and never used as a source for its code; see
CLAUDE.md. These suites are not part of the default `uv run pytest`.

| Directory | Oracle | Run with |
|---|---|---|
| `escapy/` | EscaPy (PyPI `pyscape`, AGPL-3.0), an ESC/P to PDF interpreter, through `uvx` | `uv run pytest oracles/escapy` |

## Planned

| Oracle | Use | Decided |
|---|---|---|
| Ghostscript's `epsonc` device (AGPL-3.0-or-later), run as the `gs` command the user installs | Generates realistic colour 9-pin ESC/P jobs from PostScript or PDF, as a printer driver would: colour chosen with `ESC r`, one pass per colour per band, lightest to darkest. For checking the Star LC-10 Colour model against what real software sent. | Approved by Rob, 2026-10-25 |
