# Printing from beebjit

beebjit always has a printer, which prints to `beebjit.printer` in the
directory beebjit was started from. Papyrium follows that file.

## Start Papyrium

In beebjit's directory, or giving the file's full path:

```sh
papyrium serve -t file-follow -T filepath=beebjit.printer -T from-start=yes
```

## Print

On the BBC, as described in [the guides' introduction](README.md#on-the-bbc),
but **leave `*FX6` alone**. beebjit writes every CR as LF, which Papyrium's
printers take as a new line; with `*FX6,0` the BBC would send CR and LF,
and every line would be followed by a blank one.

## Things to know

- beebjit holds the printing to itself and writes it to the file when it
  exits: quit beebjit to print the job.
- Each run that prints starts the file afresh; Papyrium notices, by its
  length or its first bytes, and reads it from the start. A run that
  begins exactly as the last one did, and prints more, goes unnoticed
  until then: restart Papyrium after it to be sure.
- Because CR becomes LF, a byte 13 in a bit image or in an escape
  sequence's argument is changed too: text prints well, graphics may not.

`docs/emulators/beebjit.md` describes beebjit's printer as read from its
source, and the changes that would make it a faithful printer port.
