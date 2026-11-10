"""Read a scan of the KX-P1080U's internal ROM hex dump back into bytes.

The patched EPROM (dump_patch.py) prints the CPU's internal ROM as lines of
``AAAA: XX XX ... XX  CS``: an address, sixteen bytes and their sum modulo
256, at 10 characters to the inch, 60 lines to a page. General OCR reads
dense hex badly, so this reads the printout by its layout: it finds each
line, fits the line's character grid by least squares to the glyphs on it,
and matches every cell against templates of the sixteen digits learnt from
the scan itself, first from the line addresses, which are known from the
lines' order, then from every line whose checksum holds.

A line is accepted only if its reading's checksum holds and its address is
the one expected; a checksum is never used to correct a reading, since two
misreads can cancel. Every accepted cell is then read again by a vote of
its five nearest neighbours among the other lines' cells, and any
disagreement is reported. Lines not accepted are listed to be read by eye
from the scan and given in a hand readings file, in the dump's own format,
whose checksums are checked in turn.

Usage:
    uv run --with numpy --with pillow python tools/kx-p1080-rom/read_dump_scan.py \\
        SCAN_PDF_FILEPATH [HAND_READINGS_FILEPATH]

Writes KX-P1080U-internal.txt, the transcript, each line marked as read
from the scan, by hand or missing, beside the scan; and, if no line is
missing, or with --fill-missing FF to fill missing lines with that byte,
KX-P1080U-internal.bin. See docs/panasonic-kx-p1080-rom-recovery.md.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image

HEX = "0123456789ABCDEF"
SIZE = 0x1000
LINE_BYTES = 16
#: Character positions on a line: four address digits, the colon at 4, a
#: space then two digits for each byte, two spaces, then the checksum.
DIGIT_SLOTS = [0, 1, 2, 3] + [6 + 3 * i + k for i in range(16) for k in (0, 1)] + [55, 56]
INK = 70  # darkness, 0-255, counted as ink
CELL_HEIGHT, CELL_WIDTH, WINDOW = 44, 50, 30
#: The offsets tried, rows and columns, of a window WINDOW wide within a
#: cell centred on its place in the fitted grid.
SHIFTS = [(dy, dx) for dy in range(-3, 4) for dx in range(4, 17)]
CENTRE = SHIFTS.index((0, 10))


def render(pdf_filepath: Path, dirpath: Path) -> list[Path]:
    subprocess.run(
        ["pdftoppm", "-r", "300", "-gray", "-png", str(pdf_filepath), str(dirpath / "p")],
        check=True,
    )
    return sorted(dirpath.glob("p-*.png"))


def rows_of(ink: np.ndarray) -> list[tuple[int, int]]:
    """The bands of the page holding a line of print."""
    counts = (ink > INK).sum(1)
    rows, start = [], None
    for y, count in enumerate(counts):
        if count > 15 and start is None:
            start = y
        elif count <= 15 and start is not None:
            if y - start > 10:
                rows.append((start, y))
            start = None
    return rows


def glyph_centres(band: np.ndarray) -> list[float]:
    columns = (band > INK).sum(0) >= 2
    centres, x = [], 0
    while x < len(columns):
        if columns[x]:
            start = x
            while x < len(columns) and (columns[x] or columns[x + 1 : x + 4].any()):
                x += 1
            if x - start >= 4:
                centres.append((start + x) / 2)
        x += 1
    return centres


def fit_grid(centres: list[float]) -> tuple[float, float]:
    """The line's left edge and pitch, by least squares over its glyphs."""
    origin, pitch = centres[0] - 15, 30.0
    for _ in range(5):
        pairs = []
        for centre in centres:
            slot = round((centre - origin) / pitch - 0.5)
            if abs((centre - origin) / pitch - 0.5 - slot) < 0.3:
                pairs.append((slot, centre))
        slots = np.array([slot for slot, _ in pairs], float)
        positions = np.array([centre for _, centre in pairs])
        design = np.vstack([np.ones_like(slots), slots + 0.5]).T
        (origin, pitch), *_ = np.linalg.lstsq(design, positions, rcond=None)
    return origin, pitch


def cells_of(page_filepaths: list[Path]) -> tuple[np.ndarray, list[int]]:
    """Every line's 38 digit cells, and the page each line is on."""
    lines, pages = [], []
    for page, filepath in enumerate(page_filepaths):
        ink = 255 - np.asarray(Image.open(filepath).convert("L"), dtype=float)
        for top, bottom in rows_of(ink):
            middle = (top + bottom) // 2
            band = ink[middle - CELL_HEIGHT // 2 : middle + CELL_HEIGHT // 2]
            origin, pitch = fit_grid(glyph_centres(band))
            cells = []
            for slot in DIGIT_SLOTS:
                x = int(round(origin + (slot + 0.5) * pitch)) - CELL_WIDTH // 2
                cells.append(np.pad(band, ((0, 0), (0, CELL_WIDTH)))[:, x : x + CELL_WIDTH])
            lines.append(cells)
            pages.append(page)
    return np.array(lines), pages


def _normalised(vector: np.ndarray) -> np.ndarray:
    vector = vector - vector.mean()
    norm = np.linalg.norm(vector)
    return vector / norm if norm else vector


def views(cells: np.ndarray) -> np.ndarray:
    """Each cell's window at every offset, normalised: lines x 38 x offsets
    x pixels."""
    result = np.empty((*cells.shape[:2], len(SHIFTS), 38 * WINDOW), np.float32)
    for line in range(cells.shape[0]):
        for k in range(cells.shape[1]):
            for s, (dy, dx) in enumerate(SHIFTS):
                window = np.roll(cells[line, k], dy, 0)[3:41, dx : dx + WINDOW]
                result[line, k, s] = _normalised(window.ravel())
    return result


def templates(view: np.ndarray, labels: dict[int, str], previous=None) -> dict:
    """The mean of each digit's labelled cells on a page, each aligned to
    the last template first."""
    samples: dict[str, list] = {digit: [] for digit in HEX}
    for line, text in labels.items():
        for k, digit in enumerate(text):
            if digit == "?":
                continue
            best = (view[line, k] @ previous[digit]).argmax() if previous else CENTRE
            samples[digit].append(view[line, k, best])
    return {digit: _normalised(np.mean(s, 0)) for digit, s in samples.items() if s}


def read(view: np.ndarray, digit_templates: dict) -> list[str]:
    digits = list(digit_templates)
    matrix = np.array([digit_templates[digit] for digit in digits])
    return [
        "".join(digits[i] for i in (view[line] @ matrix.T).max(1).argmax(1))
        for line in range(view.shape[0])
    ]


def checks(text: str, address: int) -> bool:
    data = bytes.fromhex(text[4:36])
    return text[:4] == f"{address:04X}" and sum(data) & 0xFF == int(text[36:], 16)


def transcribe(page_filepaths: list[Path]) -> tuple[dict[int, str], list[str]]:
    """The accepted lines' readings by address, and the cross-check's disagreements."""
    cells, pages = cells_of(page_filepaths)
    print(f"{len(pages)} lines on {len(page_filepaths)} pages", file=sys.stderr)
    accepted: dict[int, str] = {}
    aligned, aligned_digits, aligned_lines = [], [], []
    page_views = {}
    for page in sorted(set(pages)):
        lines = [line for line, on in enumerate(pages) if on == page]
        view = views(cells[lines])
        page_views[page] = (lines, view)
        addresses = [LINE_BYTES * line for line in lines]
        labels = {i: f"{address:04X}" + "?" * 34 for i, address in enumerate(addresses)}
        digit_templates = None
        for _ in range(6):
            digit_templates = templates(view, labels, digit_templates)
            digit_templates = templates(view, labels, digit_templates)
            readings = read(view, digit_templates)
            good = {i: text for i, text in enumerate(readings) if checks(text, addresses[i])}
            labels = {i: good.get(i, f"{a:04X}" + "?" * 34) for i, a in enumerate(addresses)}
        for i, text in good.items():
            accepted[addresses[i]] = text
            for k, digit in enumerate(text):
                aligned.append(view[i, k][(view[i, k] @ digit_templates[digit]).argmax()])
                aligned_digits.append(digit)
                aligned_lines.append(addresses[i])
    # Every accepted cell again, by its five nearest neighbours among the
    # other lines' cells.
    samples, digits, owners = np.array(aligned), np.array(aligned_digits), np.array(aligned_lines)
    disagreements = []
    for lines, view in page_views.values():
        for i, line in enumerate(lines):
            address = LINE_BYTES * line
            if address not in accepted:
                continue
            for k, digit in enumerate(accepted[address]):
                similarity = (view[i, k] @ samples.T).max(0)
                similarity[owners == address] = -9
                vote = Counter(digits[np.argsort(-similarity)[:5]]).most_common(1)[0][0]
                if vote != digit:
                    disagreements.append(f"{address:04X} digit {k}: {digit}, vote {vote}")
    return accepted, disagreements


def hand_readings(filepath: Path) -> dict[int, str]:
    result = {}
    for number, line in enumerate(filepath.read_text().splitlines(), 1):
        if not line.strip() or line.startswith("#"):
            continue
        address_text, _, rest = line.partition(":")
        words = rest.split()
        text = address_text.strip() + "".join(words[:17])
        address = int(address_text, 16)
        if len(words) < 17 or not checks(text, address):
            raise SystemExit(f"{filepath}:{number}: the checksum does not hold")
        result[address] = text
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("scan", type=Path, help="the scanned printout, a PDF")
    parser.add_argument("hand", type=Path, nargs="?", help="lines read by eye")
    parser.add_argument("--fill-missing", metavar="BYTE", help="fill missing lines, in hex")
    arguments = parser.parse_args()
    with tempfile.TemporaryDirectory() as temp_dirname:
        scanned, disagreements = transcribe(render(arguments.scan, Path(temp_dirname)))
    hand = hand_readings(arguments.hand) if arguments.hand else {}
    for line in disagreements:
        print(f"cross-check disagrees: {line}", file=sys.stderr)
    transcript, image, missing = [], bytearray(SIZE), []
    for address in range(0, SIZE, LINE_BYTES):
        if address in hand:
            text, source = hand[address], "hand"
        elif address in scanned:
            text, source = scanned[address], "scan"
        else:
            missing.append(address)
            fill = arguments.fill_missing or "??"
            text, source = f"{address:04X}" + fill * 16 + "??", "missing"
        data = text[4:36]
        transcript.append(
            f"{address:04X}: " + " ".join(data[i : i + 2] for i in range(0, 32, 2))
            + f"  {text[36:]}  {source}"
        )  # fmt: skip
        if source != "missing" or arguments.fill_missing:
            image[address : address + LINE_BYTES] = bytes.fromhex(data)
    out_dirpath = arguments.scan.parent
    (out_dirpath / "KX-P1080U-internal.txt").write_text("\n".join(transcript) + "\n")
    print(
        f"{len(scanned)} lines read from the scan, {len(hand)} by hand, {len(missing)} missing",
        file=sys.stderr,
    )
    for address in missing:
        print(f"read by eye: {address:04X}", file=sys.stderr)
    if missing and not arguments.fill_missing:
        print("no image written: lines are missing", file=sys.stderr)
        return 1
    (out_dirpath / "KX-P1080U-internal.bin").write_bytes(bytes(image))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
