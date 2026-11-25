# papyrium.transport.file_follow

A Papyrium transport that follows a file as a sender writes to it, as
`tail -f` does, and delivers the bytes added as a printer's input. It
serves emulators that print to a file, such as BeebEm (Comms > Printer
Destination > File...), B-em (Print to file (binary)) and beebjit
(`beebjit.printer`); `docs/emulators/` says how each writes its file.

It looks at the file every `poll-interval` seconds (default 0.1) and
never writes to it. It starts at the file's end, since such a file
usually holds earlier sessions' printing, unless `from-start` is given; a
file that does not exist yet is waited for and read from its start. A
file truncated, replaced, or written afresh in place is read again from
its start.

The file gives no backpressure, and nothing in it marks where a job
ends: jobs end on the idle timeout, or at the printer language's own
boundaries.

```
papyrium serve -t file-follow -T filepath=~/beebem-printer.prn
```

Registered as `file-follow` on the `papyrium.transport` axis.
