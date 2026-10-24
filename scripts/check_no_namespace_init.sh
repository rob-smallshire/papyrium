#!/bin/sh
# PEP 420 implicit namespace packages: no package may ship
# src/papyrium/__init__.py; its code lives in src/papyrium/<axis>/<name>/.
found=$(ls packages/*/src/papyrium/__init__.py 2>/dev/null)
if [ -n "$found" ]; then
    echo "remove, to keep the papyrium namespace implicit:"
    echo "$found"
    exit 1
fi
