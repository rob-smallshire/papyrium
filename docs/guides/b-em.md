# Printing from B-em

B-em sends its BBC Micro's printer output to a file. Papyrium follows the
file, printing what is added.

## Set up B-em

**File > Printing > Print to file (binary)** and choose a file, such as
`b-em-printer.prn`, or start B-em with `-printfilebin b-em-printer.prn`.
Choose the binary item: the text items change line endings and some
characters.

B-em does not remember the choice; choose it again each time you start
it, or use the command line option.

## Start Papyrium

```sh
papyrium serve -t file-follow -T filepath=/path/to/b-em-printer.prn
```

B-em adds to the end of an existing file, so Papyrium starts at its end;
add `-T from-start=yes` to print what is already there.

## Print

On the BBC, as described in [the guides' introduction](README.md#on-the-bbc).

## The end of a job

B-em keeps up to about 4 KB of printing to itself before writing it to
the file, so the file grows in blocks, and the end of a job stays in B-em
until printing is turned off. To finish a job, click the ticked **Print to
file (binary)** item, which turns printing off and writes out the rest,
then choose it again (the same file) for the next job. Quitting B-em
writes it out too. Papyrium ends the job five seconds after the last
bytes arrive.

**Print to command** does not work in B-em as it stands: B-em cannot
start the command.
