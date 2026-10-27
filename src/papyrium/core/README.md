# papyrium.core

The heart of Papyrium, a virtual vintage printer. It defines the extension
axes (transports, languages, printer models, fonts, outputs and
advertisers), a conformance suite for each axis that plug-ins, Papyrium's
own and separately distributed ones, run in their tests, in-process test doubles, and the spooler that captures every byte
a printer receives into per-job `.prn` files.
