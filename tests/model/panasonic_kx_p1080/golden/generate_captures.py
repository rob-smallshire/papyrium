"""Write the KX-P1080's golden test captures: our own ESC/P byte streams.

Run from this directory with ``uv run python generate_captures.py`` after
changing a capture; then refresh the golden images with
``PAPYRIUM_UPDATE_GOLDEN=1 uv run pytest`` and inspect them before
committing.
"""

from pathlib import Path

ESC = b"\x1b"
CRLF = b"\r\n"
SAMPLE = b"The quick brown fox jumps over the lazy dog. 0123456789"


def kx_p1080_features() -> bytes:
    """What the KX-P1080 does that the FX-80 does not, and its fonts."""
    out = bytearray(ESC + b"@" + b"Panasonic KX-P1080U" + CRLF + CRLF)
    for n, name in enumerate([b"Pica", b"Elite", b"15 cpi", b"17 cpi"]):
        out += ESC + b"w" + bytes([n]) + name + b": " + SAMPLE + CRLF
    out += ESC + b"w\x00" + CRLF
    out += b"Draft italic: " + ESC + b"4" + SAMPLE + ESC + b"5" + CRLF
    out += ESC + b"n" + b"NLQ: " + SAMPLE + CRLF
    out += b"NLQ italic: " + ESC + b"4" + SAMPLE + ESC + b"5" + CRLF
    out += ESC + b"o" + b"NLQ elite: " + SAMPLE + CRLF + ESC + b"P" + CRLF
    out += ESC + b"p\x01" + b"Proportional draft: " + SAMPLE + CRLF
    out += ESC + b"n" + b"Proportional NLQ: " + SAMPLE + CRLF
    out += ESC + b"4" + b"Proportional NLQ italic: " + SAMPLE + ESC + b"5" + CRLF
    out += ESC + b"W\x01" + b"Wide proportional" + ESC + b"W\x00" + ESC + b"p\x00" + ESC + b"P"
    out += CRLF + CRLF
    out += b"International, italic: " + ESC + b"6" + bytes(range(0x80, 0xA0)) + ESC + b"7" + CRLF
    out += b"Slashed zero in italic, code 255: " + ESC + b"6\xff" + ESC + b"7" + CRLF
    out += ESC + b"y" + b"A" + bytes([0xFF, 0x81, 0xBD, 0xA5, 0xA5, 0xBD, 0x81, 0xFF, 0])
    out += b"Download, code 65: AAA" + ESC + b"z" + b"A" + b"  released: AAA" + CRLF
    out += b"\x0c"
    return bytes(out)


CAPTURES = {"kx-p1080-features": kx_p1080_features}

if __name__ == "__main__":
    here = Path(__file__).parent
    for name, make in CAPTURES.items():
        (here / f"{name}.prn").write_bytes(make())
        print(f"wrote {name}.prn")
