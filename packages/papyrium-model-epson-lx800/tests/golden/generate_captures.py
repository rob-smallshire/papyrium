"""Write the LX-800's golden test captures: our own ESC/P byte streams.

Run from this directory with ``uv run python generate_captures.py`` after
changing a capture; then refresh the golden images with
``PAPYRIUM_UPDATE_GOLDEN=1 uv run pytest`` and inspect them before
committing.
"""

from pathlib import Path

ESC = b"\x1b"
CRLF = b"\r\n"


def lx800_features() -> bytes:
    """What the LX-800 does that the FX-80 does not."""
    out = bytearray(ESC + b"@" + b"Epson LX-800" + CRLF + CRLF)
    out += b"Draft: The quick brown fox jumps over the lazy dog." + CRLF
    out += ESC + b"x\x01" + b"NLQ Roman: The quick brown fox jumps over the lazy dog." + CRLF
    out += ESC + b"k\x01" + b"NLQ Sans Serif, printed in Roman here." + ESC + b"k\x00" + CRLF
    out += ESC + b"a\x01" + b"Centred" + CRLF + ESC + b"a\x02" + b"Right aligned" + CRLF
    paragraph = (
        b"Full justification spreads the words of a paragraph across the line, "
        b"sharing the spare room among the spaces, so that both margins are straight."
    )
    out += ESC + b"a\x03" + paragraph + CRLF + ESC + b"a\x00"
    out += (
        b"\xe0\xe1\xe2\xe3\xe4 IBM table in NLQ: "
        + ESC
        + b"t\x01"
        + b"\xe0\xe2\xe3\xe4\xe6\xf1\xf2\xf3\xfb"
        + ESC
        + b"t\x00"
        + CRLF
    )
    out += ESC + b"x\x00" + CRLF
    out += (
        ESC
        + b"!\x40"
        + b"Italic by ESC !"
        + ESC
        + b"!\x00 and "
        + ESC
        + b"!\x80"
        + b"underlined by ESC !"
        + ESC
        + b"!\x00"
        + CRLF
    )
    out += (
        ESC
        + b"M\x0f"
        + b"Condensed elite: twenty characters to the inch"
        + b"\x12"
        + ESC
        + b"P"
        + CRLF
    )
    for number, name in ((11, b"Spain II"), (12, b"Latin America")):
        out += ESC + b"R" + bytes([number]) + name.ljust(14) + b"@ [ \\ ] ^ ` { | } ~" + CRLF
    out += ESC + b"R\x00"
    out += ESC + b"e\x00\x0a" + b"Tabs\tevery\tten" + CRLF
    out += b"Skip" + ESC + b"f\x00\x0a" + b"ten spaces" + CRLF
    out += b"\x0eEnlarged until CR" + CRLF + b"and back to normal" + CRLF
    return bytes(out) + b"\x0c"


CAPTURES = {"lx800-features": lx800_features}

if __name__ == "__main__":
    here = Path(__file__).parent
    for name, build in CAPTURES.items():
        (here / f"{name}.prn").write_bytes(build())
