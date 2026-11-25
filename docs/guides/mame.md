# Printing from MAME

MAME emulates the BBC Micro (`bbcb`, `bbcm` and their relatives) with a
Centronics printer on its parallel port. The printer's output, the
"printout" medium `-prin`, can be a file or a TCP connection to Papyrium.
You need MAME's BBC ROMs in its rompath; `mame -verifyroms bbcb` checks
them.

## Live, over TCP

Start Papyrium first:

```sh
papyrium serve
```

then MAME, with the printout connected to Papyrium's port:

```sh
mame bbcb -prin socket.127.0.0.1:9100
```

Each byte goes to Papyrium as the BBC prints it. Use an IPv4 address such as `127.0.0.1`: MAME's sockets
are IPv4 only.

- **Start Papyrium first.** If nothing is listening, MAME listens on the
  port itself instead, holding it so that Papyrium cannot start there,
  and throws away everything printed.
- MAME does not reconnect: if Papyrium stops, mount the printout again
  from MAME's File Manager, or restart MAME.

## Through a file

```sh
mame bbcb -prin ~/bbc-printer.prn
papyrium serve -t file-follow -T filepath=~/bbc-printer.prn -T from-start=yes
```

MAME writes each byte as it prints. Name a file that does not exist yet:
MAME overwrites an existing file from its start without shortening it, so
an older, longer printout's end would be left behind it.

## Print

On the BBC, as described in [the guides' introduction](README.md#on-the-bbc).

MAME types an `-autoboot_command` at the emulated keyboard's speed, so a
long command typed that way needs time to finish before printing starts.
