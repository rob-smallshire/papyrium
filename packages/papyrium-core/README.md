# papyrium-core

The heart of Papyrium, a virtual vintage printer. It defines the extension
axes (transports first; languages, printer models and outputs to follow),
a conformance suite for each axis that plug-in packages run in their own
tests, in-process test doubles, and the spooler that captures every byte
a printer receives into per-job `.prn` files.
