"""Write the M-1109's golden test captures: our own ESC/P byte streams.

Run from this directory with ``uv run python generate_captures.py`` after
changing a capture; then refresh the golden images with
``PAPYRIUM_UPDATE_GOLDEN=1 uv run pytest`` and inspect them before
committing.
"""

from pathlib import Path

ESC = b"\x1b"
CRLF = b"\r\n"


def mode_one_differences() -> bytes:
    """What the M-1109's Mode I does that the FX-80 does not."""
    out = bytearray(ESC + b"@" + b"Brother M-1109, Mode I" + CRLF + CRLF)
    out += b"Draft, then " + ESC + b"x\x01near letter quality" + ESC + b"x\x00." + CRLF
    out += ESC + b"M\x0fCondensed elite: twenty characters to the inch\x12" + ESC + b"P" + CRLF
    out += b"\x0eEnlarged until CAN\x18cancels it" + CRLF
    for number, name in ((9, b"Norway"), (10, b"Denmark II"), (11, b"England II")):
        out += ESC + b"R" + bytes([number]) + name.ljust(12) + b"# $ @ [ \\ ] ^ ` { | } ~" + CRLF
    out += ESC + b"R\x00" + ESC + b"I\x01" + b"BEL \x07 DC1 \x11 CAN \x18" + ESC + b"I\x00" + CRLF
    # A ramp in the 144 dpi mode, which drops the second of two adjacent dots.
    ramp = bytes(0xFF >> (i % 8) for i in range(144))
    out += ESC + b"A\x08" + ESC + b"*\x07" + bytes([len(ramp), 0]) + ramp + CRLF + ESC + b"2"
    # Without default vertical tabs, VT is a line feed.
    out += b"\x0bAfter VT" + CRLF
    return bytes(out)


CAPTURES = {"mode-one": mode_one_differences}

if __name__ == "__main__":
    here = Path(__file__).parent
    for name, build in CAPTURES.items():
        (here / f"{name}.prn").write_bytes(build())
