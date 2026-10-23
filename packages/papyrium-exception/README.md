# papyrium-exception

Categorised exceptions and the CLI error-reporting boundary shared by every
Papyrium package: the `PapyriumException` root with `DataError`,
`ConfigurationError` and `InternalError` categories, each carrying a stable
exit code; `handled_errors`, which prints data and configuration errors
without a traceback and exits with the right code; and `render_error`,
which walks an exception's cause chain and notes.

Derived from `oaknut-exception` (MIT, Copyright (c) 2026 Robert
Smallshire).
