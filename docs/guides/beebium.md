# Printing from Beebium

Beebium connects its BBC Micro's printer port to a printer over TCP, the
way a network printer is reached on port 9100. Papyrium's `raw-tcp`
transport, the default for `papyrium serve`, is that printer. Bytes go
across as the BBC prints them.

## Start Papyrium

```sh
papyrium serve
```

It listens on port 9100 on this machine. Choose the printer with
`--model`, such as `papyrium serve --model star-lc10`, and set its
switches with `-M`.

## Give Beebium a printer

In Beebium, add a **Network Printer** (the `tcp-printer` peripheral) to
the BBC Micro, with the host and port Papyrium listens on: `localhost`
and `9100`. It attaches to the BBC's parallel port.

From the command line, the same is:

```sh
beebium-model-b --tcp-printer host=localhost:port=9100
```

Papyrium may run on another machine: serve with `-T host=` to listen on
every interface (or with `--advertise`, which also announces it on the
local network), and give that machine's name or address as the host.

## Print

On the BBC, as described in [the guides' introduction](README.md#on-the-bbc):

```
*FX6,0
*FX5,1
VDU 2
PRINT "HELLO"
VDU 1,12
VDU 3
```

The job appears in `papyrium-jobs/job-0001/` five seconds after the last
byte, as `page-0001.png` and `job.pdf`. Closing Beebium, or restarting
Papyrium, does not end a job early or lose its bytes: a job ends only when
the bytes stop.

`integration/beebium/` holds tests that drive a real Beebium BBC Micro to
print this way.
