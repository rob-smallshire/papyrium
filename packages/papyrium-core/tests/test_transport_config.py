"""Transport.from_config: building a transport from string options."""

import pytest

from papyrium.core.transport import Transport
from papyrium.exception import ConfigurationError


class _Configurable(Transport):
    """A transport with typed options."""

    def __init__(self, name, *, host="localhost", port=9100, timeout=1.5, verbose=False):
        super().__init__(name=name)
        self.host, self.port, self.timeout, self.verbose = host, port, timeout, verbose

    async def open(self):
        pass

    async def close(self):
        pass

    def __aiter__(self):
        raise NotImplementedError


def test_no_options_uses_the_defaults():
    transport = _Configurable.from_config(name="t", config={})
    assert (transport.host, transport.port, transport.verbose) == ("localhost", 9100, False)
    assert transport.name == "t"


def test_string_options_take_the_type_of_their_default():
    transport = _Configurable.from_config(
        name="t", config={"host": "0.0.0.0", "port": "9101", "timeout": "2.5", "verbose": "yes"}
    )
    assert (transport.host, transport.port, transport.timeout, transport.verbose) == (
        "0.0.0.0",
        9101,
        2.5,
        True,
    )


def test_hyphenated_keys_map_to_underscores():
    class _Hyphen(_Configurable):
        def __init__(self, name, *, read_size=1):
            super().__init__(name)
            self.read_size = read_size

    assert _Hyphen.from_config(name="t", config={"read-size": "8"}).read_size == 8


def test_typed_values_pass_through():
    assert _Configurable.from_config(name="t", config={"port": 9102}).port == 9102


def test_unknown_option_is_a_configuration_error():
    with pytest.raises(ConfigurationError, match="colour"):
        _Configurable.from_config(name="t", config={"colour": "red"})


def test_unparseable_value_is_a_configuration_error():
    with pytest.raises(ConfigurationError, match="port"):
        _Configurable.from_config(name="t", config={"port": "ninety"})


@pytest.mark.parametrize("text", ["maybe", ""])
def test_unparseable_flag_is_a_configuration_error(text):
    with pytest.raises(ConfigurationError, match="verbose"):
        _Configurable.from_config(name="t", config={"verbose": text})
