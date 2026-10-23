# papyrium-output-pdf

A Papyrium output that writes each job as one PDF document (`job.pdf`),
one PDF page per printed page at the paper's true size. Every struck dot
is a vector dot (a zero-length stroke with round caps), so pages stay
sharp at any zoom and print at the host printer's full resolution.

It has no dependencies beyond the Python standard library, and the same
pages always give a byte-identical file: no timestamps, no random IDs.

Under the dots, each printed character is laid down as invisible text in
its cell, so the document can be searched and text copied from it.

Registered as `pdf` on the `papyrium.output` axis. Options: `ink`, the
grey level of the ink from 0 (black) to 1 (white), default 0.15; `text`,
the invisible text layer, default yes; `filename`, default `job.pdf`.
