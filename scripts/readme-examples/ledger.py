"""Write a capture of a 132-column ledger report, printed condensed.

Usage: ledger.py CAPTURE_PRN
"""

import random
import sys
from pathlib import Path

ESC, SI, FF = b"\x1b", b"\x0f", b"\x0c"
ACCOUNTS = [
    "OFFICE SUPPLIES", "POSTAGE", "TELEPHONE", "RENT AND RATES", "ELECTRICITY",
    "COMPUTER EQUIPMENT", "SOFTWARE LICENCES", "TRAVEL", "SUBSISTENCE", "PRINTING",
    "STATIONERY", "INSURANCE", "BANK CHARGES", "SUNDRY EXPENSES", "SALARIES",
    "NATIONAL INSURANCE", "PENSIONS", "TRAINING", "SUBSCRIPTIONS", "REPAIRS AND RENEWALS",
    "MOTOR EXPENSES", "ADVERTISING", "ENTERTAINMENT", "LEGAL FEES", "AUDIT FEES",
]  # fmt: skip
MONTHS = ["APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT"]


def line(text=""):
    assert len(text) <= 132, text
    return text.encode("ascii") + b"\r\n"


def ledger():
    rng = random.Random(1985)
    data = bytearray(ESC + b"@" + SI)
    data += line(
        f"ACME WIDGETS LTD{' ' * 31}NOMINAL LEDGER - DEPARTMENTAL SUMMARY"
        f"{' ' * 26}RUN 24/10/85  PAGE   1"
    )
    data += line(f"REPORT NL0420{' ' * 41}PERIOD 07 ENDING 31/10/85{' ' * 38}OPERATOR RJS")
    data += line("-" * 132)
    data += line(
        "A/C  DESCRIPTION          "
        + "".join(f"{month:>10}" for month in MONTHS)
        + "    YEAR TO DATE      BUDGET    VAR%"
    )
    data += line("-" * 132)
    for n in range(51):
        name = ACCOUNTS[n % len(ACCOUNTS)]
        figures = [rng.randint(50, 99999) / 100 for _ in MONTHS]
        total = sum(figures)
        budget = total * rng.uniform(0.85, 1.15)
        variance = (total - budget) / budget * 100
        data += line(
            f"{4000 + n * 10:4d} {name:<21}"
            + "".join(f"{figure:10.2f}" for figure in figures)
            + f"{total:16.2f}{budget:12.0f}{variance:+8.1f}"
        )
    data += line("-" * 132)
    return bytes(data + FF)


Path(sys.argv[1]).write_bytes(ledger())
