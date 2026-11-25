"""Unit tests for the generic extension framework.

End-to-end entry-point discovery is exercised where real plug-ins are
registered. Here we cover the axis-agnostic behaviour: the Extension
contract, namespace formation, docstring-driven descriptions, and the
not-found error path.
"""

import pytest

from papyrium.exception import ConfigurationError, PapyriumException
from papyrium.extension import (
    Extension,
    ExtensionError,
    extension,
    namespace_for,
)
from papyrium.extension._text import first_paragraph, normalize_name, strip_lines


class _Wrapped(Extension):
    """A widget whose summary wraps
    onto a second line.

    More about it.
    """

    @classmethod
    def _kind(cls) -> str:
        return "widget"


class _Widget(Extension):
    """A test widget extension.

    Second paragraph that should not appear in the single-line summary.
    """

    @classmethod
    def _kind(cls):
        return "widget"


class _Undocumented(Extension):
    @classmethod
    def _kind(cls):
        return "widget"


class TestNamespace:
    def test_namespace_uses_papyrium_prefix(self):
        assert namespace_for("transport") == "papyrium.transport"

    def test_namespace_for_arbitrary_kind(self):
        assert namespace_for("widget") == "papyrium.widget"


class TestExtensionContract:
    def test_kind_delegates_to_underscore_kind(self):
        assert _Widget.kind() == "widget"

    def test_name_is_the_constructor_argument(self):
        assert _Widget(name="acme").name == "acme"

    def test_version_defaults_to_package_version(self):
        assert _Widget.version().count(".") == 2


class TestDescribe:
    def test_describe_returns_full_docstring(self):
        description = _Widget.describe()
        assert "A test widget extension." in description
        assert "Second paragraph" in description

    def test_describe_summary_is_the_first_paragraph(self):
        assert _Widget.describe(summary=True) == "A test widget extension."

    def test_a_summary_may_wrap_across_lines(self):
        assert _Wrapped.describe(summary=True) == "A widget whose summary wraps onto a second line."

    def test_describe_handles_missing_docstring(self):
        assert _Undocumented.describe() == "No description available."


class TestNotFound:
    def test_unknown_extension_raises_extension_error(self):
        with pytest.raises(ExtensionError) as exc_info:
            extension("widget", "papyrium.widget", "does-not-exist")
        assert "does-not-exist" in str(exc_info.value)

    def test_extension_error_is_a_configuration_error(self):
        # A mis-installed plug-in is a setup problem, not bad data, so it
        # carries the configuration exit code, not a traceback.
        assert issubclass(ExtensionError, ConfigurationError)
        assert issubclass(ExtensionError, PapyriumException)


class TestTextHelpers:
    def test_strip_lines_trims_blank_edges_but_keeps_interior(self):
        assert strip_lines("\n\n a \n\n b \n\n") == " a \n\n b "

    def test_first_paragraph_skips_leading_blanks_and_joins_its_lines(self):
        assert first_paragraph("\n\n  hello  \nworld\n\nmore") == "hello world"

    def test_first_paragraph_of_empty_is_empty(self):
        assert first_paragraph("   ") == ""

    def test_normalize_name_preserves_hyphens(self):
        assert normalize_name("  raw-tcp  ") == "raw-tcp"
