#!/usr/bin/env python3
"""Shared parser for the vendored WD1772 PLA/PLM text dump."""
from __future__ import annotations

import hashlib
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "ref" / "wd1772-vg93" / "wd1772pla.txt"
ROW_RE = re.compile(r"^(A\d{2})\|(R\d{3})\|([01]{19})\|([019]{19})$")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_rows() -> tuple[list[dict[str, object]], list[str], int]:
    rows: list[dict[str, object]] = []
    ignored: list[str] = []
    section = 1
    for raw in SOURCE.read_text().splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("---+"):
            section += 1
            continue
        match = ROW_RE.match(line)
        if not match:
            ignored.append(line)
            continue
        a_id, r_id, inputs, outputs = match.groups()
        rows.append(
            {
                "index": len(rows),
                "section": section,
                "a": a_id,
                "r": r_id,
                "inputs": inputs,
                "outputs": outputs,
                "ambiguous_output_columns": [
                    index for index, value in enumerate(outputs) if value == "9"
                ],
            }
        )
    return rows, ignored, section


def validate_shape(
    rows: list[dict[str, object]], ignored: list[str]
) -> tuple[list[int], list[int], list[str], list[str], list[dict[str, object]], list[str]]:
    input_widths = sorted({len(str(row["inputs"])) for row in rows})
    output_widths = sorted({len(str(row["outputs"])) for row in rows})
    input_chars = sorted(set("".join(str(row["inputs"]) for row in rows)))
    output_chars = sorted(set("".join(str(row["outputs"]) for row in rows)))
    rows_with_9 = [row for row in rows if row["ambiguous_output_columns"]]

    failures = []
    if len(rows) != 120:
        failures.append(f"expected 120 data rows, found {len(rows)}")
    if input_widths != [19]:
        failures.append(f"expected 19 input bits, found widths {input_widths}")
    if output_widths != [19]:
        failures.append(f"expected 19 output bits, found widths {output_widths}")
    if input_chars != ["0", "1"]:
        failures.append(f"unexpected input character set: {input_chars}")
    if output_chars != ["0", "1", "9"]:
        failures.append(f"unexpected output character set: {output_chars}")
    if len(rows_with_9) != 1:
        failures.append(f"expected exactly one row with 9 markers, found {len(rows_with_9)}")
    if len(ignored) != 3:
        failures.append(f"expected 3 footer guide rows, found {len(ignored)}")
    return input_widths, output_widths, input_chars, output_chars, rows_with_9, failures
