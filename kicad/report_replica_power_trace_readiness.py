#!/usr/bin/env python3
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOARD = ROOT / "kicad" / "juku_routed.kicad_pcb"
DEFAULT_REPORT = ROOT / "docs" / "replica-power-trace-readiness.md"

POWER_NETS = ["GND", "P5V", "P12V", "M12V", "M5V_DERIVED"]
EXPECTED_POWER_SEGMENTS = 710
EXPECTED_WIDENED_SEGMENTS = 377
BASELINE_WIDTH_MM = 0.20
MAX_WIDTH_MM = 1.00


def repo_relative(path):
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def table_row(values):
    return "| " + " | ".join(str(value).replace("|", "/") for value in values) + " |"


def iter_segment_blocks(text):
    for match in re.finditer(r"\(segment\s+.*?\n\s*\)", text, re.S):
        yield match.group(0)


def first_pair(block, name):
    match = re.search(rf"\({name}\s+([-0-9.]+)\s+([-0-9.]+)\)", block)
    if not match:
        return None
    return float(match.group(1)), float(match.group(2))


def first_value(block, name):
    match = re.search(rf"\({name}\s+([-0-9.]+)\)", block)
    return float(match.group(1)) if match else None


def first_string(block, name):
    match = re.search(rf'\({name}\s+"([^"]+)"\)', block)
    return match.group(1) if match else None


def parse_segments(board):
    text = board.read_text(errors="replace")
    rows = []
    for block in iter_segment_blocks(text):
        start = first_pair(block, "start")
        end = first_pair(block, "end")
        width = first_value(block, "width")
        layer = first_string(block, "layer")
        net = first_string(block, "net")
        if not start or not end or width is None or not layer or not net:
            continue
        length = math.hypot(end[0] - start[0], end[1] - start[1])
        rows.append({
            "net": net,
            "layer": layer,
            "width": width,
            "length": length,
        })
    return rows


def fmt_mm(value):
    return f"{value:.3f}"


def fmt_width(value):
    return f"{value:.4f}".rstrip("0").rstrip(".")


def build_report(board):
    rows = parse_segments(board)
    power_rows = [row for row in rows if row["net"] in POWER_NETS]
    by_net = defaultdict(list)
    for row in power_rows:
        by_net[row["net"]].append(row)

    failures = []
    if len(power_rows) != EXPECTED_POWER_SEGMENTS:
        failures.append(
            f"Expected {EXPECTED_POWER_SEGMENTS} routed power segments, found {len(power_rows)}."
        )
    widened = sum(1 for row in power_rows if row["width"] > BASELINE_WIDTH_MM + 1e-9)
    if widened != EXPECTED_WIDENED_SEGMENTS:
        failures.append(
            f"Expected {EXPECTED_WIDENED_SEGMENTS} widened power segments, found {widened}."
        )
    for net in POWER_NETS:
        if not by_net[net]:
            failures.append(f"Missing routed power net `{net}`.")

    too_narrow = [row for row in power_rows if row["width"] < BASELINE_WIDTH_MM - 1e-9]
    too_wide = [row for row in power_rows if row["width"] > MAX_WIDTH_MM + 1e-9]
    if too_narrow:
        failures.append(f"{len(too_narrow)} power segments are below {BASELINE_WIDTH_MM:.2f} mm.")
    if too_wide:
        failures.append(f"{len(too_wide)} power segments exceed {MAX_WIDTH_MM:.2f} mm.")

    status = "READY" if not failures else "NOT READY"
    total_len = sum(row["length"] for row in power_rows)
    widened_len = sum(row["length"] for row in power_rows if row["width"] > BASELINE_WIDTH_MM + 1e-9)
    width_counts = Counter(round(row["width"], 4) for row in power_rows)

    lines = [
        "# Replica power-trace readiness",
        "",
        f"Board: `{repo_relative(board)}`",
        f"Status: **{status}**",
        "",
        "This report records the routed main-board power traces after",
        "`kicad/widen_power_v2.py`. It is a fabrication-readiness guard for the",
        "authentic 2-layer board: the freerouted 0.20 mm baseline remains where",
        "clearance constrained widening, while all geometry is still checked by",
        "the KiCad DRC gate in `kicad/report_order_readiness.py`.",
        "",
        "## Summary",
        "",
        f"- Routed power segments: {len(power_rows)}",
        f"- Widened power segments (`>{BASELINE_WIDTH_MM:.2f} mm`): {widened}",
        f"- Total routed power length: {fmt_mm(total_len)} mm",
        f"- Widened routed power length: {fmt_mm(widened_len)} mm",
        f"- Width clamp: {BASELINE_WIDTH_MM:.2f} mm to {MAX_WIDTH_MM:.2f} mm",
        "",
        "## Nets",
        "",
        "| Net | Segments | Widened | Min width mm | Max width mm | Total length mm | Widened length mm | Layers |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for net in POWER_NETS:
        items = by_net[net]
        widths = [row["width"] for row in items]
        layers = sorted({row["layer"] for row in items})
        net_widened = [row for row in items if row["width"] > BASELINE_WIDTH_MM + 1e-9]
        lines.append(table_row([
            net,
            len(items),
            len(net_widened),
            fmt_mm(min(widths)) if widths else "-",
            fmt_mm(max(widths)) if widths else "-",
            fmt_mm(sum(row["length"] for row in items)),
            fmt_mm(sum(row["length"] for row in net_widened)),
            ", ".join(layers) if layers else "-",
        ]))

    lines.extend([
        "",
        "## Width Histogram",
        "",
        "| Width mm | Segments |",
        "| ---: | ---: |",
    ])
    for width, count in sorted(width_counts.items()):
        lines.append(table_row([fmt_width(width), count]))

    lines.extend(["", "## Disposition", ""])
    if failures:
        lines.append("Do not use this routed package until the failures below are resolved.")
        lines.extend(["", "## Failures", ""])
        lines.extend(f"- {failure}" for failure in failures)
    else:
        lines.append(
            "The routed power nets match the reviewed v76 widening envelope: "
            "710 power segments present, 377 widened where local clearance allowed, "
            "no power segment below the routed baseline, and no widened segment above "
            "the 1.00 mm clamp. KiCad DRC remains the clearance authority."
        )
    lines.append("")
    return "\n".join(lines), not failures


def main():
    board = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT_BOARD
    report_path = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else DEFAULT_REPORT
    report, ready = build_report(board)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report)
    print(report)
    print(f"Wrote {repo_relative(report_path)}")
    return 0 if ready else 3


if __name__ == "__main__":
    raise SystemExit(main())
