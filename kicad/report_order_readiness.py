#!/usr/bin/env python3
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOARD = ROOT / "kicad" / "juku_routed.kicad_pcb"
DEFAULT_OUT_DIR = ROOT / "fab" / "gerbers"
FAB_REPORT = ROOT / "kicad" / "report_fab_readiness.py"

BLOCKING_DRC_TYPES = {
    "clearance",
    "shorting_items",
    "copper_edge_clearance",
    "lib_footprint_issues",
}
REVIEW_ONLY_DRC_TYPES = {
    "courtyards_overlap",
    "pth_inside_courtyard",
    "silk_over_copper",
    "silk_overlap",
    "text_thickness",
}


def repo_relative(path):
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def table_row(values):
    return "| " + " | ".join(str(value).replace("|", "/") for value in values) + " |"


def run_fab_readiness(board, out_dir):
    subprocess.run([str(FAB_REPORT), str(board), str(out_dir)], check=True)
    return out_dir / "juku_routed-drc.json"


def build_report(board, out_dir, drc):
    violations = drc.get("violations", [])
    unconnected = drc.get("unconnected_items", [])
    counts = Counter(v.get("type", "unknown") for v in violations)
    blocking_counts = Counter({name: counts.get(name, 0) for name in BLOCKING_DRC_TYPES})
    blocking_counts["unconnected_items"] = len(unconnected)
    unknown_types = sorted(set(counts) - BLOCKING_DRC_TYPES - REVIEW_ONLY_DRC_TYPES)

    machine_ready = (
        not any(blocking_counts.values())
        and not unknown_types
    )
    status = "MACHINE READY" if machine_ready else "NOT READY"

    lines = [
        "# Main board order readiness",
        "",
        f"Board: `{repo_relative(board)}`",
        f"Fabrication package: `{repo_relative(out_dir)}`",
        f"Status: **{status}**",
        "",
        "This gate separates machine-checkable fabrication blockers from dense",
        "placement and silkscreen findings that require human visual review or",
        "explicit waiver before placing an order.",
        "",
        "## Machine Blockers",
        "",
        "| Type | Count |",
        "| --- | ---: |",
    ]
    for name in sorted(blocking_counts):
        lines.append(table_row([name, blocking_counts[name]]))

    if unknown_types:
        lines.extend(["", "## Unknown DRC Types", ""])
        lines.extend(f"- `{name}`: {counts[name]}" for name in unknown_types)

    lines.extend([
        "",
        "## Review-Only DRC Types",
        "",
        "| Type | Count |",
        "| --- | ---: |",
    ])
    for name in sorted(REVIEW_ONLY_DRC_TYPES):
        if counts.get(name, 0):
            lines.append(table_row([name, counts[name]]))

    lines.extend(["", "## Disposition", ""])
    if machine_ready:
        lines.append(
            "Machine blockers are clear: no clearance, short, unconnected, "
            "copper-edge, or footprint-library findings remain. The package can "
            "proceed to human Gerber/assembly review of the listed review-only "
            "classes."
        )
    else:
        lines.append(
            "Do not order until all machine blockers and unknown DRC classes above "
            "are resolved or deliberately reclassified."
        )
    lines.append("")
    return "\n".join(lines), machine_ready


def main():
    board = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT_BOARD
    out_dir = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else DEFAULT_OUT_DIR
    drc_path = run_fab_readiness(board, out_dir)
    drc = json.loads(drc_path.read_text())
    report, machine_ready = build_report(board, out_dir, drc)
    report_path = out_dir / "order-readiness.md"
    report_path.write_text(report)
    print(report)
    print(f"Wrote {repo_relative(report_path)}")
    return 0 if machine_ready else 3


if __name__ == "__main__":
    raise SystemExit(main())
