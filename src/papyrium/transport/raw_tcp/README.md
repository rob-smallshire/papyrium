# papyrium.transport.raw_tcp

A Papyrium transport that listens for raw TCP connections, by default on
port 9100 (the JetDirect or AppSocket convention), and delivers the
unframed bytes that arrive as a printer's input. It stands in for a
parallel cable: flow control is TCP's own, and a disconnect does not end a
job. One connection is served at a time; later connections wait their
turn.

Registered as `raw-tcp` on the `papyrium.transport` axis.
