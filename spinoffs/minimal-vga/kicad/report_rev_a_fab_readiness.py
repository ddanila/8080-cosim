#!/usr/bin/env python3
import json
import os
import subprocess
import sys
from collections import Counter
from pathlib import Path


def run_drc(board, out_dir):
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "drc-report.json"
    cmd = [
        os.environ.get("KICAD_CLI", "kicad-cli"),
        "pcb",
        "drc",
        "--severity-error",
        "--format",
        "json",
        "--output",
        str(json_path),
        str(board),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)
    return json_path


def item_nets(items):
    nets = []
    for item in items:
        description = item.get("description", "")
        if "[" not in description or "]" not in description:
            continue
        nets.append(description.split("[", 1)[1].split("]", 1)[0])
    return nets


def build_report(board, drc):
    violations = drc.get("violations", [])
    unconnected = drc.get("unconnected_items", [])
    violation_types = Counter(item.get("type", "unknown") for item in violations)
    unconnected_nets = Counter()
    for item in unconnected:
        for net in item_nets(item.get("items", [])):
            unconnected_nets[net] += 1

    status = "NOT READY" if violations or unconnected else "READY"
    lines = [
        f"# Rev A fabrication readiness",
        "",
        f"Board: `{board}`",
        f"Status: **{status}**",
        "",
        "## DRC Summary",
        "",
        f"- DRC violations: {len(violations)}",
        f"- Unconnected items: {len(unconnected)}",
    ]
    if violation_types:
        lines.extend(["", "## Violation Types", ""])
        for typ, count in sorted(violation_types.items()):
            lines.append(f"- `{typ}`: {count}")
    if unconnected_nets:
        lines.extend(["", "## Top Unconnected Nets", ""])
        for net, count in unconnected_nets.most_common(12):
            lines.append(f"- `{net}`: {count}")
    lines.extend(["", "## Manufacturing Gate", ""])
    if status == "READY":
        lines.append(
            "KiCad DRC has zero error-level violations and zero unconnected "
            "items, so the fabrication exporter may emit Gerbers and drill "
            "files. Human review and sourcing gates still apply before order."
        )
    else:
        lines.append(
            "Gerber export remains blocked until KiCad DRC has zero error-level "
            "violations and zero unconnected items."
        )
    lines.append("")
    return "\n".join(lines)


def main():
    board = Path(sys.argv[1] if len(sys.argv) > 1 else "spinoffs/minimal-vga/kicad/rev-a-physical.kicad_pcb")
    out_dir = Path(sys.argv[2] if len(sys.argv) > 2 else "fab/minimal-vga")
    json_path = run_drc(board, out_dir)
    drc = json.loads(json_path.read_text())
    report = build_report(board, drc)
    report_path = out_dir / "fab-readiness.md"
    report_path.write_text(report + "\n")
    print(report)
    print(f"Wrote {report_path}")


if __name__ == "__main__":
    main()
