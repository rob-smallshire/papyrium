"""Write a capture of a short letter in near letter quality, with a line of draft.

Usage: letter.py CAPTURE_PRN
"""

import sys
from pathlib import Path

ESC, CR_LF, FF = b"\x1b", b"\r\n", b"\x0c"


def text(*lines):
    return b"".join(line.encode("ascii") + CR_LF for line in lines)


letter = (
    ESC + b"@" + ESC + b"x\x01"
    + text("Papyrium", "A virtual vintage printer", "", "")
    + text("Dear reader,", "")
    + text(
        "This page was printed by an emulated Brother M-1109 in near",
        "letter quality: each character is struck in two passes, the",
        "second 1/216 inch below the first, so the dots close up into",
        "strokes. Its characters were reconstructed from the",
        "printer's own output, and no ROM was read.",
        "",
    )
    + text("Yours faithfully,", "", "", "The M-1109", "")
    + ESC + b"x\x00"
    + b"In draft, for comparison, with " + ESC + b"4italics" + ESC + b"5, "
    + ESC + b"-\x01underlining" + ESC + b"-\x00 and " + ESC + b"Eemphasis" + ESC + b"F." + CR_LF
    + FF
)  # fmt: skip

Path(sys.argv[1]).write_bytes(letter)
