"""Pieces the ESC/P printers' demonstration pages share."""

from __future__ import annotations

import math

from papyrium.language.escp.writing import ESC, line, picture

#: A smiling face for ESC &: an attribute byte (top eight pins, columns
#: 0-11) and eleven columns, bit 7 the top pin.
SMILE = bytes([0x8B, 0x3C, 0x42, 0xA5, 0x81, 0xA5, 0x99, 0x81, 0x42, 0x3C, 0x00, 0x00])


def heading(text: str) -> bytes:
    """A section heading: emphasized and underlined, a blank line above."""
    return line() + line(ESC + b"E" + ESC + b"-\x01", text, ESC + b"-\x00" + ESC + b"F")


def waves(
    *, mode: int = 1, command: bytes | None = None, width: int = 480, rows: int = 32
) -> bytes:
    """Two crossing sine waves over a ruled baseline, as a bit image in
    ``ESC *`` mode *mode* or with the bit-image *command* (see :func:`picture`)."""

    def ink(x: int, y: int) -> bool:
        phase = 4 * math.pi * x / width
        first = rows / 2 - (rows / 2 - 3) * math.sin(phase)
        second = rows / 2 - (rows / 2 - 3) * math.cos(phase / 2)
        on_curve = abs(y - first) < 1.2 or abs(y - second) < 1.2
        return on_curve or y == rows - 1 or (y >= rows - 4 and x % (width // 8) == 0)

    return picture(width, rows, ink, mode=mode, command=command)
