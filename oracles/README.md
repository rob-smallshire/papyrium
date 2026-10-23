# Oracles

Independent implementations used to check Papyrium's behaviour. Each is
run as a separate program, never imported into Papyrium, never
distributed with it, and never used as a source for its code; see
CLAUDE.md. These suites are not part of the default `uv run pytest`.

| Directory | Oracle | Run with |
|---|---|---|
| `escapy/` | EscaPy (PyPI `pyscape`, AGPL-3.0), an ESC/P to PDF interpreter, through `uvx` | `uv run pytest oracles/escapy` |
