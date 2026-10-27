# papyrium.extension

The entry-point plug-in framework shared by every extensible *axis* of
Papyrium: transports, printer languages, printer models, fonts and
outputs.

Each axis declares a `kind` (a short identifier such as `"transport"`).
Concrete extensions subclass `Extension`, override `_kind()`, and register
under the `papyrium.<kind>` entry-point namespace in the
`pyproject.toml` of the distribution that ships them, Papyrium's own or a
separate one:

```toml
[project.entry-points."papyrium.transport"]
raw-tcp = "papyrium.transport.raw_tcp:RawTcpTransport"
```

Consumers discover and load them through `list_extensions()`,
`create_extension()` and friends, which wrap
[stevedore](https://docs.openstack.org/stevedore/). A plug-in shipped by
any installed package appears automatically.

Derived from `oaknut-extension` (MIT, Copyright (c) 2026 Robert
Smallshire).
