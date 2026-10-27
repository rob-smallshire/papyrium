# papyrium.output.pdf

A Papyrium output that writes each job as one PDF document (`job.pdf`),
one PDF page per printed page at the paper's true size. Every struck dot
is a vector dot (a small filled circle drawn once and placed at each
dot), so pages stay sharp at any zoom and print at the host printer's
full resolution.

It has no dependencies beyond the Python standard library, and the same
pages always give a byte-identical file: no timestamps, no random IDs.

Under the dots, each printed character is laid down as invisible text in
its cell, so the document can be searched and text copied from it.
The text is written in printed order, one string per line. macOS Preview
ignores that order when selecting: it rebuilds lines from the page
layout and takes gaps that line up down several rows, as in a table, for
column gutters, so a drag selection can run down a column. Copied and
extracted text keep the printed order.

Registered as `pdf` on the `papyrium.output` axis. Options: `ink`, the
grey level of the ink from 0 (black) to 1 (white), default 0.15; `text`,
the invisible text layer, default yes; `filename`, default `job.pdf`.
