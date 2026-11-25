# Printing from BeebEm

BeebEm sends its BBC Micro's printer output to a file, appending each byte
as it is printed. Papyrium follows the file, printing what is added.

## Set up BeebEm

1. **Comms > Printer Destination > File...** and choose a file, such as
   `beebem-printer.prn`. It can exist already: BeebEm adds to its end.
2. **Comms > Printer On/Off** to switch the printer on.

BeebEm remembers both in its preferences (`PrinterFile` and
`PrinterEnabled`), so the printer is on with the same file next time.

## Start Papyrium

```sh
papyrium serve -t file-follow -T filepath=/path/to/beebem-printer.prn
```

Papyrium starts at the end of the file, so earlier sessions' printing
is not printed again; add `-T from-start=yes` to print what is already
there. It waits for the file if BeebEm has not made it yet.

## Print

On the BBC, as described in [the guides' introduction](README.md#on-the-bbc).
A job ends five seconds after the last byte; BeebEm writes each byte at
once, so jobs appear promptly.

## Things to know

- **Edit > Copy** in BeebEm uses the printer to copy text: it switches the
  printer destination to Clipboard. Set it back to File afterwards.
- The BBC never waits for the printer: BeebEm accepts each byte at once.
- The Clipboard destination changes line endings, and LPT1 to LPT4 are
  for real printer ports; only File gives Papyrium the BBC's bytes.
