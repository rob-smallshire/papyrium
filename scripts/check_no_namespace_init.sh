#!/bin/sh
# PEP 420 implicit namespace package: there is no src/papyrium/__init__.py,
# so that separately distributed extensions can add modules to papyrium.
if [ -e src/papyrium/__init__.py ]; then
    echo "remove src/papyrium/__init__.py, to keep the papyrium namespace implicit"
    exit 1
fi
