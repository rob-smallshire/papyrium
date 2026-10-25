"""Endpoint: where a transport listens, and whether the network can reach it."""

import pytest

from papyrium.core.transport import Endpoint


@pytest.mark.parametrize(
    "addresses, local_only",
    [
        (("127.0.0.1",), True),
        (("127.0.0.1", "::1"), True),
        (("0.0.0.0",), False),
        (("::",), False),
        (("127.0.0.1", "192.168.1.20"), False),
    ],
)
def test_local_only_when_every_address_is_loopback(addresses, local_only):
    assert Endpoint(protocol="appsocket", port=9100, addresses=addresses).local_only is local_only


def test_an_endpoint_needs_a_port_and_an_address():
    with pytest.raises(ValueError, match="port"):
        Endpoint(protocol="appsocket", port=0, addresses=("127.0.0.1",))
    with pytest.raises(ValueError, match="address"):
        Endpoint(protocol="appsocket", port=9100, addresses=())


def test_a_transport_has_no_endpoints_or_network_options_unless_it_says_so():
    from papyrium.core.testing import MemoryTransport

    assert MemoryTransport(name="memory").endpoints() == ()
    assert MemoryTransport.all_interfaces_options() == {}
