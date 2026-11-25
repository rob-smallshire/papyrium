# Printing from BBC Micro emulators

How to print from a BBC Micro emulator to Papyrium, one guide for each:

| Emulator | How it reaches Papyrium | Live? | Guide |
|---|---|---|---|
| Beebium | a TCP connection to `papyrium serve` | yes | [beebium.md](beebium.md) |
| MAME | a TCP connection, or a file Papyrium follows | yes | [mame.md](mame.md) |
| BeebEm | a file Papyrium follows | yes | [beebem.md](beebem.md) |
| B-em | a file Papyrium follows | yes, in blocks | [b-em.md](b-em.md) |
| beebjit | a file Papyrium follows | at exit | [beebjit.md](beebjit.md) |
| b2 | a saved file, printed or sent | no | [b2.md](b2.md) |
| jsbeeb | none yet | no | [jsbeeb.md](jsbeeb.md) |

## Papyrium

Install Papyrium with `uv tool install papyrium` (or run it without
installing as `uvx papyrium`; in a checkout of this repository, `uv run
papyrium`). `papyrium serve` runs a printer until you stop it with
Ctrl-C, printing each job into a numbered directory under
`papyrium-jobs`: the bytes received (`capture.prn`), a record (`job.json`)
and the pages as PNG and PDF. A job ends when no bytes have arrived for
five seconds (`--idle-timeout`).

Choose the printer with `--model`; `papyrium list-models` lists them, and
`papyrium describe-model NAME` describes a model and its options, which
set its switches and paper with `-M KEY=VALUE`. The default is the Epson
FX-80.

## On the BBC

The BBC prints to whatever its printer port is connected to; these are
the same in every emulator.

```
*FX5,1
VDU 2
PRINT "HELLO"
VDU 3
```

`*FX5,1` chooses the parallel printer, the default on a Model B. `VDU 2`
sends everything printed to the screen to the printer as well, until `VDU
3`. `VDU 1,n` sends one byte to the printer alone, so escape sequences go
as `VDU 1,27,1,69` (ESC E, emphasized on an Epson printer), and a form
feed, which ejects the page, as `VDU 1,12`.

The BBC sends CR alone at the end of each line unless told otherwise.
Either let it send LF as well with `*FX6,0`, or leave it alone and switch
on the printer's auto line feed: `papyrium serve -M auto-line-feed=yes`.
Without one or the other, every line prints over the last.
