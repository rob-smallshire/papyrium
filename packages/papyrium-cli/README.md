# papyrium-cli

The `papyrium` command. `papyrium serve` runs a printer: it listens on a
transport (raw TCP on port 9100 by default), captures every job it
receives, prints it with the chosen printer model, and can announce itself
on the network with `--advertise`. `papyrium render` prints a captured job
again, `list-jobs` reports the jobs captured, and the `list-...` and
`describe-...` commands report the installed plug-ins.

It brings the raw TCP transport, the PNG and PDF outputs and the multicast
DNS advertiser, but no printer model: install the models you want, such as
`papyrium-model-epson-fx80`, or install `papyrium` for the command with
every model.
