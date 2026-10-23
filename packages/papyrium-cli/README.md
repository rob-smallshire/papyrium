# papyrium-cli

The `papyrium` command. `papyrium serve` runs a printer instance: it
listens on a transport (raw TCP on port 9100 by default) and captures
every job it receives. `papyrium list-jobs` reports the jobs captured so
far, and `list-transports` / `describe-transport` introspect the installed
transport plug-ins.
