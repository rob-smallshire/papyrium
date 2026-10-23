"""Pytest bootstrap for papyrium-font-draft-9.

Under pytest's importlib mode (required for PEP 420 namespace packages)
neither the package's own ``tests`` directory nor the workspace root is
auto-injected into ``sys.path``. Inserting both here lets tests import
shared helpers.
"""

import sys
from pathlib import Path

_TESTS_DIRPATH = Path(__file__).parent
_WORKSPACE_ROOT_DIRPATH = _TESTS_DIRPATH.parent.parent.parent
for _path in (_TESTS_DIRPATH, _WORKSPACE_ROOT_DIRPATH):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))
