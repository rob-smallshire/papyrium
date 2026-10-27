"""Write the golden test captures: our own ESC/P byte streams, as .prn files.

Run from this directory with ``uv run python generate_captures.py`` after
changing a capture; then refresh the golden images with
``PAPYRIUM_UPDATE_GOLDEN=1 uv run pytest`` and inspect them before
committing.
"""

import math
from pathlib import Path

ESC = b"\x1b"
CRLF = b"\r\n"
BBC = b"\n\r"  # A BBC Micro with *FX6,0 sends LF then CR.


def text_styles() -> bytes:
    return (
        ESC
        + b"@"
        + b"Papyrium: an Epson FX-80 emulation"
        + CRLF
        + CRLF
        + b"Normal, "
        + ESC
        + b"Eemphasized"
        + ESC
        + b"F, "
        + ESC
        + b"Gdouble-strike"
        + ESC
        + b"H, "
        + ESC
        + b"-\x01underlined"
        + ESC
        + b"-\x00,"
        + CRLF
        + ESC
        + b"4italic"
        + ESC
        + b"5, \x0eone-line enlarged\x14 "
        + b"\x0fcondensed text for wide reports\x12,"
        + CRLF
        + ESC
        + b"Melite pitch, twelve to the inch"
        + ESC
        + b"P, "
        + ESC
        + b"W\x01wide"
        + ESC
        + b"W\x00, "
        + ESC
        + b"p\x01proportional spacing"
        + ESC
        + b"p\x00,"
        + CRLF
        + b"E = mc"
        + ESC
        + b"S\x002"
        + ESC
        + b"T, H"
        + ESC
        + b"S\x012"
        + ESC
        + b"TO"
        + CRLF
        + ESC
        + b"!\x38Master select: emphasized, double-strike, wide"
        + ESC
        + b"!\x00"
        + CRLF
        + CRLF
        + b"".join(
            ESC + b"3" + bytes([n]) + b"Line spacing " + str(n).encode() + b"/216 inch" + CRLF
            for n in (18, 24, 30, 36)
        )
        + ESC
        + b"2"
    )


def bbc_listing() -> bytes:
    lines = [
        b"   10 REM Papyrium test listing",
        b"   20 MODE 7",
        b'   30 PRINT "HELLO, WORLD"',
        b"   40 FOR I% = 1 TO 10",
        b"   50   PRINT I%, I% * I%, SQR(I%)",
        b"   60 NEXT",
        b'   70 VDU 2: PRINT "PRINTED": VDU 3',
        b"   80 END",
    ]
    return BBC.join(lines) + BBC + b"\x0c"


def graphics() -> bytes:
    out = bytearray(ESC + b"@" + b"Bit-image graphics" + CRLF + ESC + b"A\x08")
    # A sine wave in each density.
    for command, columns in ((b"K", 240), (b"L", 480), (b"Z", 960)):
        data = bytes(
            1 << int(3.5 + 3.5 * math.sin(i * 12 / columns * math.pi)) for i in range(columns)
        )
        out += ESC + command + bytes([columns % 256, columns // 256]) + data + CRLF
    # A filled circle drawn as 72 dpi bit-image strips (ESC * 5).
    radius = 60
    for strip in range(0, 2 * radius, 8):
        data = bytearray()
        for x in range(2 * radius):
            column = 0
            for pin in range(8):
                y = strip + pin
                if (x - radius + 0.5) ** 2 + (y - radius + 0.5) ** 2 <= radius * radius:
                    column |= 0x80 >> pin
            data.append(column)
        out += ESC + b"*\x05" + bytes([len(data) % 256, len(data) // 256]) + data + CRLF
    # Nine-pin graphics: a staircase reaching the ninth pin.
    steps = bytearray()
    for pin in range(9):
        pattern = 1 << (8 - pin)
        steps += bytes([pattern >> 1, (pattern & 1) << 7]) * 8
    out += ESC + b"^\x00" + bytes([72, 0]) + steps + CRLF
    out += ESC + b"2"
    return bytes(out)


def international() -> bytes:
    out = bytearray(ESC + b"@")
    names = [
        b"USA",
        b"France",
        b"Germany",
        b"UK",
        b"Denmark",
        b"Sweden",
        b"Italy",
        b"Spain",
        b"Japan",
    ]
    for number, name in enumerate(names):
        out += ESC + b"R" + bytes([number]) + name.ljust(10) + b"# $ @ [ \\ ] ^ ` { | } ~" + CRLF
    return bytes(out)


def pages_and_layout() -> bytes:
    out = bytearray(ESC + b"@")
    # New margins apply from the next carriage return.
    out += ESC + b"l\x05" + ESC + b"Q\x32" + b"\r"
    out += b"Margins at columns 5 and 50 wrap this long line of text automatically "
    out += b"when it reaches the right margin, as the printer would." + CRLF
    out += ESC + b"D\x0a\x14\x1e\x00" + b"\tTab 10\tTab 20\tTab 30" + CRLF
    out += b"Overstrike: O\x08/" + CRLF
    out += b"DEL: ABC\x7f\x7fx" + CRLF
    # CAN discards the whole unprinted line, so only "kept" prints, at the margin.
    out += b"CAN: gone\x18kept" + CRLF
    out += b"\x0c" + b"Second page, after a form feed." + CRLF
    # A three-inch form: the form feed moves three inches, on the same sheet.
    out += ESC + b"C\x00\x03" + b"A three inch form starts here." + CRLF
    out += b"\x0c" + b"The next form, three inches on." + CRLF
    return bytes(out)


CAPTURES = {
    "text-styles": text_styles,
    "bbc-listing": bbc_listing,
    "graphics": graphics,
    "international": international,
    "pages-and-layout": pages_and_layout,
}

if __name__ == "__main__":
    here = Path(__file__).parent
    for name, build in CAPTURES.items():
        (here / f"{name}.prn").write_bytes(build())
