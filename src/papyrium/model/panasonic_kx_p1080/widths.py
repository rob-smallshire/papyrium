"""The KX-P1080U's proportional widths, from its firmware.

Written by tools/kx-p1080-rom/extract.py from the EPROM's tables at $5C00
and $5C80 (draft upright and italic) and $5D70 and $5DF0 (NLQ): one byte
for each code 0-127, the width in 1/120 inch in the low nibble and in the
high nibble where printing starts: with bit 3 clear, that many 1/120 inch
columns into the character, moving it left; with it set, bits 0-2
columns before it, moving it right.
"""

WIDTH_TABLES = {
    "upright": bytes.fromhex(
        "9c9c0b0a18189c359c9c0b9c9c9c9c9b0a9b9c9c9c9c189c9c9c9c0a0b9c9c9c"
        "0c35189c9c9c9c2527179c9c179c160a9c199c9c9c9c9c9c9c9c16169a9c1a9c"
        "9c9c9c9c9c9c9c9c9c180b9c9c9c9c9c9c9c9c9c9c9c9c9c0a9c0a189a189c9c"
        "459c9b9b9b9c1a9b9b08190a089c9b9c9b9b9b9c9b9c9c9c0a9c9a0935199c9c"
    ),
    "italic": bytes.fromhex(
        "9b9b9b9b08189c1a9b9c9c9c9c9c9b9b9c9b9c9c9c9b199c9c9c9b9b9c9c9b9c"
        "0c1a0a9c0b9c9c1628189c9c089c270a9c199c9c0c9c0b9c9c0b18090a0b190b"
        "9c9c9c9c9c9c9c9c9c1a9c9c0a9c9c9c9c9c9c9c9c9c9c9c9c9c9c9b270b0a9c"
        "250b0b0b9c0b0c0b0b190a1b090b0a0b0b0b0a0b1a0b1a9c9c9c9c1a190a9c9c"
    ),
    "upright_nlq": bytes.fromhex(
        "0c9c0b0a18180c359c9c0b9c9c9c0c0b0a9b9c9c9c9c289c9c9c0c0a0b9c9c9c"
        "0c35189c9c9c9c3527279c9c179c260a9c199c9c9c9c9c9c9c9c26160a9c0a9c"
        "9c0c9c9c9c9c9c9c9c180b9c9c9c9c9c9c9c9c9c9c9c0c0c0a9c0a180a189c0c"
        "259c0b0b9b9c0a0b0b18090a180c0b9c0b0b9b9c0b9c9c0c0a9c0a0935099c0c"
    ),
    "italic_nlq": bytes.fromhex(
        "1b0b1b0b18380c1a9b0c0c0c9c9c0b1b0c9b9c0c0c0b399c0c0c1b0b0c9c0b0c"
        "0c1a2a0c0b0c0c4628280c0c080c271a0c190c0c0c0c0b0c0c0b28192a0b191b"
        "0c0c0c0c0c0c0c0c0c0a0c9c0a0c0c0c9c0c9c0c1c1c1c1c0c1c0c0b270b2a0c"
        "459b0b0b9c0b0c1b0b190a9b190b0a0b0b1b0a0b1a0b1a1c0c0c0c1a191a1c0c"
    ),
}
