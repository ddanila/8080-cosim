#!/usr/bin/env python3
import csv
import re
import sys
from pathlib import Path

import pcbnew


DESIGNATOR_RE = re.compile(r"^([A-Z]+)([0-9]+)$")
DIP_RE = re.compile(r"\bDIP[- ]?(\d+)\b", re.IGNORECASE)
WIDTH_RE = re.compile(r"\bW([0-9]+(?:\.[0-9]+)?)mm\b", re.IGNORECASE)
FOOTPRINT_RE = re.compile(r"^DIP-(\d+)_W([0-9]+(?:\.[0-9]+)?)mm_Socket$")


def natural_key(ref):
    match = DESIGNATOR_RE.match(ref)
    if not match:
        return (ref, 0)
    prefix, number = match.groups()
    return (prefix, int(number))


def expand_designators(field):
    refs = []
    for token in field.replace(";", ",").split(","):
        token = token.strip().upper()
        if not token:
            continue
        if "-" not in token:
            refs.append(token)
            continue
        start, end = [part.strip() for part in token.split("-", 1)]
        start_match = DESIGNATOR_RE.match(start)
        end_match = DESIGNATOR_RE.match(end)
        if not start_match or not end_match:
            refs.append(token)
            continue
        start_prefix, start_number = start_match.groups()
        end_prefix, end_number = end_match.groups()
        if start_prefix != end_prefix:
            refs.append(token)
            continue
        for number in range(int(start_number), int(end_number) + 1):
            refs.append(f"{start_prefix}{number}")
    return refs


def load_bom(path):
    by_ref = {}
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            for ref in expand_designators(row["Designator"]):
                by_ref[ref] = row
    return by_ref


def footprint_name(fp):
    return str(fp.GetFPID().GetLibItemName())


def parse_expected(row):
    text = " ".join(
        [
            row.get("Candidate MPN", ""),
            row.get("Package", ""),
            row.get("Notes", ""),
        ]
    )
    pins = None
    width = None
    dip_match = DIP_RE.search(text)
    if dip_match:
        pins = int(dip_match.group(1))
    width_match = WIDTH_RE.search(text)
    if width_match:
        width = float(width_match.group(1))
    return pins, width


def parse_socket_footprint(name):
    match = FOOTPRINT_RE.match(name)
    if not match:
        return None, None
    return int(match.group(1)), float(match.group(2))


def socket_rows(board, bom):
    rows = []
    failures = []
    for fp in sorted(board.Footprints(), key=lambda item: natural_key(item.GetReference().upper())):
        ref = fp.GetReference().upper()
        if not ref.startswith("U"):
            continue
        name = footprint_name(fp)
        if not name.startswith("DIP-") or not name.endswith("_Socket"):
            continue
        source = bom.get(ref, {})
        expected_pins, expected_width = parse_expected(source)
        actual_pins, actual_width = parse_socket_footprint(name)
        pad_count = len(list(fp.Pads()))

        row_failures = []
        if actual_pins is None:
            row_failures.append("footprint name is not a recognized DIP socket")
        if expected_pins is None:
            row_failures.append("BOM does not state expected DIP pin count")
        elif actual_pins != expected_pins:
            row_failures.append(f"expected DIP-{expected_pins}, got DIP-{actual_pins}")
        if actual_pins is not None and pad_count != actual_pins:
            row_failures.append(f"footprint has {pad_count} pads, expected {actual_pins}")
        if expected_width is None:
            row_failures.append("BOM notes do not state expected socket width")
        elif actual_width is None:
            row_failures.append(f"expected W{expected_width:.2f}mm, got unknown width")
        elif abs(actual_width - expected_width) > 0.01:
            row_failures.append(f"expected W{expected_width:.2f}mm, got W{actual_width:.2f}mm")

        failures.extend(f"{ref}: {failure}" for failure in row_failures)
        rows.append(
            {
                "Designator": ref,
                "Device": source.get("Value", fp.GetValue()),
                "Expected": (
                    f"DIP-{expected_pins} W{expected_width:.2f}mm"
                    if expected_pins is not None and expected_width is not None
                    else "incomplete"
                ),
                "Footprint": name,
                "Pads": str(pad_count),
                "Status": "FAIL" if row_failures else "PASS",
            }
        )
    return rows, failures


def table(rows):
    columns = ["Designator", "Device", "Expected", "Footprint", "Pads", "Status"]
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row[column] for column in columns) + " |")
    return lines


def build_report(board_path, bom_path):
    board = pcbnew.LoadBoard(str(board_path))
    bom = load_bom(bom_path)
    rows, failures = socket_rows(board, bom)
    status = "NOT READY" if failures else "READY"
    lines = [
        "# Rev A socket-fit readiness",
        "",
        f"Board: `{board_path}`",
        f"Engineering BOM: `{bom_path}`",
        f"Status: **{status}**",
        "",
        "## Summary",
        "",
        f"- Socketed IC footprints checked: {len(rows)}",
        f"- Socket fit failures: {len(failures)}",
        "",
        "## Socket Rows",
        "",
    ]
    lines.extend(table(rows))
    if failures:
        lines.extend(["", "## Failures", ""])
        lines.extend(f"- {failure}" for failure in failures)
    lines.append("")
    return "\n".join(lines), not failures


def main():
    board_path = Path(sys.argv[1] if len(sys.argv) > 1 else "spinoffs/minimal-vga/kicad/rev-a-physical.kicad_pcb")
    bom_path = Path(sys.argv[2] if len(sys.argv) > 2 else "spinoffs/minimal-vga/kicad/rev-a.bom.csv")
    out_dir = Path(sys.argv[3] if len(sys.argv) > 3 else "fab/minimal-vga")
    report, ready = build_report(board_path, bom_path)
    report_path = out_dir / "assembly" / "socket-fit-readiness.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report)
    print(report)
    print(f"Wrote {report_path}")
    return 0 if ready else 3


if __name__ == "__main__":
    raise SystemExit(main())
