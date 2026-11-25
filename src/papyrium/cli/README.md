# papyrium.cli

The `papyrium` command. `papyrium serve` runs a printer: it listens on a
transport (raw TCP on port 9100 by default), captures every job it
receives, prints it with the chosen printer model, and can announce itself
on the network with `--advertise`. `papyrium print` prints a file, or
standard input, as one job in the same job directory, for printer output
an emulator saves all at once; `papyrium send` sends one to a running
printer's raw TCP port instead. `papyrium render` prints a captured job
again, `list-jobs` reports the jobs captured, and the `list-...` and
`describe-...` commands report the installed plug-ins.

It finds printer models, transports, outputs and advertisers as plug-ins,
so those of a separately installed extension appear beside Papyrium's
own.
