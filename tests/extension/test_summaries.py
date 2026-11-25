"""Every installed plug-in's description opens with a one-sentence summary.

The summary is the description's first paragraph, which listings such as
``papyrium list-models`` show alone: a single sentence, ending in a full
stop, short enough to read in a table.
"""

from importlib.metadata import entry_points

import pytest

from papyrium.extension import describe_extension, namespace_for

#: The longest a summary may be.
SUMMARY_LENGTH = 80

AXES = ("transport", "language", "model", "font", "output", "advertiser")

PLUGINS = [
    (kind, point.name)
    for kind in AXES
    for point in sorted(entry_points(group=namespace_for(kind)), key=lambda point: point.name)
]


@pytest.mark.parametrize(("kind", "name"), PLUGINS, ids=[f"{k}:{n}" for k, n in PLUGINS])
def test_the_summary_is_one_short_sentence(kind, name):
    summary = describe_extension(kind, namespace_for(kind), name, summary=True)
    assert summary.endswith("."), summary
    assert ". " not in summary, summary
    assert len(summary) <= SUMMARY_LENGTH, f"{len(summary)} characters: {summary}"
