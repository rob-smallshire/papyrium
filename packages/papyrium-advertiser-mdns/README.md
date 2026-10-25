# papyrium-advertiser-mdns

Announces Papyrium printers on the local network with multicast DNS, the
way Bonjour and Avahi announce network printers, so senders such as a
Centronics-to-network bridge can find them without being told an address.

A raw TCP printer is announced as a `_pdl-datastream._tcp` service, the
type Apple's Bonjour Printing specification gives for raw port printing,
so it appears like any other network printer. Its TXT record follows that
specification's keys and says it is a Papyrium printer:

```
txtvers=1
qtotal=1
ty=Brother M-1109 (Papyrium)
product=(Brother M-1109)
note=Papyrium virtual printer
usb_MFG=Brother
usb_MDL=M-1109
usb_CMD=ESCP9
uuid=<the printer's UUID>
```

A client looking only for Papyrium printers can match "Papyrium" in `ty`
or `note`, or in the instance name, and can recognise a particular printer
by its `uuid` across renames and restarts.

Only endpoints the network can reach are announced; an unspecified address
stands for every address of its family on this machine except loopback.
The services name their own host, `papyrium-<8 hex digits>.local.`, so
Papyrium never answers for the machine's own name. If the printer's name is
taken, a free variant is chosen and the name actually registered is
logged.

Registered as `mdns` on the `papyrium.advertiser` axis. It uses
[python-zeroconf](https://github.com/python-zeroconf/python-zeroconf),
which is licensed LGPL-2.1-or-later, unmodified as an ordinary dependency;
anyone distributing a bundle that includes it must meet the LGPL's terms
for that library.
