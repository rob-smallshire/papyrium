#### Printer

The parallel printer port (`printer-port`) takes one sink extension. The
built-in `file-printer` spools everything the BBC sends to the port into a
file on the host; `describe-extension file-printer` prints the same list.
See `docs/printer-port.md` for the port model and the other sinks.

| Option | Default | Description |
|--------|---------|-------------|
| `--file-printer path=<file>[:key=value...]` | (omitted = no printer) | Spool the printer port to `<file>`, created or truncated at launch. |

`--file-printer` parameters (colon-separated, the generic extension grammar):

| Key | Default | Meaning |
|-----|---------|---------|
| `path=<file>` | required | File to write; created or truncated at attach. |
| `line_ending=raw\|lf\|crlf` | `raw` | `raw` keeps the bytes as sent. The MOS sends CR for a newline and, by default (`*FX6,10`), suppresses LF to the printer; `lf` turns a lone CR into LF and a CR LF pair into LF, `crlf` turns a lone CR into CR LF and leaves CR LF alone. |
| `buffer=<n>` | `256` | Receiver queue depth in bytes. When it is full the next byte waits for /ACK until the file has caught up, so a slow disc stalls the guest, never the host. |
| `online=true\|false` | `true` | Start online. `false` models a switched-off printer: the BBC's print stalls waiting for /ACK until `FilePrinter.SetOnline` (or the panel's Online toggle) switches it on, and then resumes. |

##### tcp-printer

The `tcp-printer` plugin sends everything the BBC prints to a raw TCP
printer port on the network: a JetDirect printer, a printer emulator such as
Scriptorium, or `nc -l 9100`. Only the bytes cross, with no framing or protocol.
The printer is online exactly while it is connected: until the connection is
made, and after it drops, the BBC's print waits for /ACK as it would for a
switched-off printer, and carries on once the printer is reachable again.
`describe-extension tcp-printer` prints the same list.

| Option | Default | Description |
|--------|---------|-------------|
| `--tcp-printer [key=value...]` | (omitted = no printer) | Print to a raw TCP printer port, `localhost:9100` unless given. |

`--tcp-printer` parameters (colon-separated, the generic extension grammar):

| Key | Default | Meaning |
|-----|---------|---------|
| `url=[scheme://]host:port` | (none) | The printer endpoint in one value, e.g. `url="socket://printer.local:9100"`; the scheme is optional and ignored. Cannot be combined with `host` or `port`. |
| `host=<host>` | `localhost` | Printer hostname or address; an alternative to `url`. |
| `port=<n>` | `9100` | Printer TCP port, the JetDirect convention; an alternative to `url`. |
| `buffer=<n>` | `256` | Receiver queue depth in bytes. When it is full the next byte waits for /ACK until the socket has caught up, so a slow printer stalls the guest, never the host. |
| `reconnect_ms=<n>` | `1000` | Milliseconds between connection attempts while not connected. `0` makes one attempt at launch and never retries. |

The `TcpPrinter.GetStatus` RPC and the sidebar panel report the endpoint,
whether it is connected, and the bytes received from the port and sent to
the socket. There is no way to set the printer online: it follows the
connection.

##### host-parallel-printer

The `host-parallel-printer` plugin sends everything the BBC prints to a
printer device on the host: a parallel port, or a USB printer such as a
USB-to-Centronics cable, both written to as a plain device file.
Only the bytes cross; nothing is read from the device or configured on it.
The printer is online exactly while its device is open: while the device is
missing or the printer refuses it, the BBC's print waits for /ACK as it
would for a switched-off printer, and carries on once the device opens.
Linux and Windows only; macOS has no printer device node.
`describe-extension host-parallel-printer` prints the same list.

| Option | Default | Description |
|--------|---------|-------------|
| `--host-parallel-printer device=<path>[:key=value...]` | (omitted = no printer) | Print to the host printer device `<path>`. |

`--host-parallel-printer` parameters (colon-separated, the generic extension grammar):

| Key | Default | Meaning |
|-----|---------|---------|
| `device=<path>` | required | The host printer device. Linux: `/dev/usb/lp0` (a USB printer or USB-to-Centronics cable) or `/dev/lp0` (a parallel port). Windows: a USB printer's interface path, `\\?\usb#...`, or `LPTn`, which is opened as `\\.\LPTn`. A USB printer on Windows is not an LPT port, and the `USB001` name the Printers dialog shows is a spooler port, not a device. `HostParallelPrinter.ListDevices` lists the devices present. |
| `buffer=<n>` | `256` | Receiver queue depth in bytes. When it is full the next byte waits for /ACK until the device has caught up, so a slow printer stalls the guest, never the host. |
| `reconnect_ms=<n>` | `1000` | Milliseconds between attempts to open the device while it is not open. `0` makes one attempt at launch and never retries. |

The `HostParallelPrinter.GetStatus` RPC and the sidebar panel report the
device, whether it is open, and the bytes received from the port and
written to the device. `HostParallelPrinter.ListDevices` lists the printer
devices present on the host with friendly names: the `/dev/usb/lp*` and
`/dev/lp*` nodes on Linux, the USB printer interface paths on Windows. It
only lists; it chooses nothing.

