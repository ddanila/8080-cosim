#!/usr/bin/env python3
"""Run source-PCB DRC and report electrical placement blockers correctly."""
from __future__ import annotations

import json
import hashlib
import subprocess
import tempfile
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "kicad/juku.kicad_pcb"
OUTPUT = ROOT / "docs/source-pcb-drc.md"


def main() -> int:
    cli = subprocess.check_output(
        [str(ROOT / "scripts/find-kicad-cli.sh")], text=True
    ).strip()
    with tempfile.TemporaryDirectory(prefix="juku-source-drc-") as directory:
        report_path = Path(directory) / "drc.json"
        subprocess.run(
            [cli, "pcb", "drc", "--format", "json", "--output", str(report_path), str(BOARD)],
            check=True,
            stdout=subprocess.DEVNULL,
        )
        report = json.loads(report_path.read_text())

    violations = report.get("violations", [])
    counts = Counter(item.get("type", "unknown") for item in violations)
    shorts = [item for item in violations if item.get("type") == "shorting_items"]
    unique: dict[tuple[str, ...], dict] = {}
    for violation in shorts:
        key = tuple(sorted(str(item.get("description", "")) for item in violation.get("items", [])))
        unique.setdefault(key, violation)

    status = "PASS" if not shorts else "PLACEMENT HOLD"
    lines = [
        "# Source PCB DRC",
        "",
        f"Status: **{status}**",
        "",
        "This report parses KiCad's `violations` array. `shorting_items` is a",
        "violation type, not a top-level JSON member; checking",
        "`report.get('shorting_items')` incorrectly reports zero.",
        "",
        "## Command",
        "",
        "```sh",
        "python3 kicad/report_source_pcb_drc.py",
        "```",
        "",
        "## Summary",
        "",
        f"- Board SHA256: `{hashlib.sha256(BOARD.read_bytes()).hexdigest()}`",
        f"- Total violations: `{len(violations)}`",
        f"- Unconnected items: `{len(report.get('unconnected_items', []))}`",
        f"- Short violations: `{len(shorts)}`",
        f"- Unique colliding pad/item pairs: `{len(unique)}`",
        "",
        "## Violation types",
        "",
        "| Type | Count |",
        "| --- | ---: |",
    ]
    lines.extend(f"| `{name}` | {count} |" for name, count in sorted(counts.items()))
    lines += ["", "## Unique short collisions", "", "| Nets | Items |", "| --- | --- |"]
    for violation in unique.values():
        description = str(violation.get("description", "")).replace("|", "/")
        items = "; ".join(str(item.get("description", "")).replace("|", "/")
                          for item in violation.get("items", []))
        lines.append(f"| {description} | {items} |")
    lines += [
        "",
        "The source PCB is not eligible for routed-copper adoption while any",
        "short collision remains. Move parts only from registered target-revision",
        "placement evidence; do not silence these findings with waivers.",
    ]
    OUTPUT.write_text("\n".join(lines) + "\n")
    print(f"source PCB DRC: {status}; shorts={len(shorts)}, unique={len(unique)}")
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
