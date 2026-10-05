#!/usr/bin/env python3
"""Run source-PCB DRC and report electrical placement blockers correctly."""
from __future__ import annotations

import json
import hashlib
import re
import subprocess
import tempfile
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "kicad/juku.kicad_pcb"
OUTPUT = ROOT / "docs/source-pcb-drc.md"
RF_DISPOSITION = ROOT / "ref/photos/dgsh5-109-009-sb/rf-option-disposition.json"


def item_ref(description: str) -> str | None:
    match = re.search(r"\bof ([A-Z]+\d+)\b", description)
    return match.group(1) if match else None


def main() -> int:
    disposition = json.loads(RF_DISPOSITION.read_text())
    legacy_dnp = set(disposition["legacy_dnp_refs"])
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
    clearances = [item for item in violations if item.get("type") == "clearance"]
    crossings = [item for item in violations if item.get("type") == "tracks_crossing"]
    unique: dict[tuple[str, ...], dict] = {}
    for violation in shorts:
        key = tuple(sorted(str(item.get("description", "")) for item in violation.get("items", [])))
        unique.setdefault(key, violation)

    status = "PASS" if not (shorts or clearances or crossings) else "PLACEMENT HOLD"
    lines = [
        "# Source PCB DRC",
        "",
        f"Status: **{status}**",
        "",
        "The command runs fresh KiCad DRC on the source PCB. PASS and exit 0 mean",
        "only that shorting_items, clearance, and tracks_crossing violations are",
        "absent. Unconnected items, courtyard, silkscreen, and other violation",
        "types do not fail this placement gate. It does not check routed variants",
        "or authorize fabrication; see [manufacturing readiness](replica-manufacturing-readiness.md).",
        "",
        "## Command",
        "",
        "Run from the repository root with Python 3 and KiCad CLI available.",
        "`scripts/find-kicad-cli.sh` selects the CLI; set `KICAD_CLI` to choose",
        "an executable explicitly. Python uses only the standard library.",
        "The raw DRC JSON is temporary and removed on exit. The writer replaces",
        "this report, including when the placement gate returns exit status 1.",
        "",
        "```sh",
        "python3 kicad/report_source_pcb_drc.py",
        "```",
        "",
        "## Summary",
        "",
        f"- Board SHA256: `{hashlib.sha256(BOARD.read_bytes()).hexdigest()}`",
        f"- DRC violations excluding unconnected items: `{len(violations)}`",
        f"- Unconnected items: `{len(report.get('unconnected_items', []))}`",
        f"- Short violations: `{len(shorts)}`",
        f"- Copper-clearance violations: `{len(clearances)}`",
        f"- Track-crossing violations: `{len(crossings)}`",
        f"- Unique short-collision item groups: `{len(unique)}`",
        "",
        "## Violation types",
        "",
        "| Type | Count |",
        "| --- | ---: |",
    ]
    lines.extend(f"| `{name}` | {count} |" for name, count in sorted(counts.items()))
    if unique:
        lines += ["", "## Unique short collisions", "", "| Nets | Items |", "| --- | --- |"]
    for violation in unique.values():
        description = str(violation.get("description", "")).replace("|", "/")
        items = "; ".join(str(item.get("description", "")).replace("|", "/")
                          for item in violation.get("items", []))
        lines.append(f"| {description} | {items} |")
    collision_refs = sorted({
        ref for violation in unique.values() for item in violation.get("items", [])
        if (ref := item_ref(str(item.get("description", ""))))
    })
    lines += [
        "",
        "## Revision disposition",
        "",
        "The `.006` RF option is excluded from this `.009` target; the evidence",
        "record below supplies the legacy-DNP reference list. For current",
        "component identity and placement boundaries, see",
        "[video analog evidence](video-analog-boundary.md) and",
        "[photo placement](analog-cluster-photo-placement.md). This DRC command",
        "does not verify the photo registrations or component markings.",
        "",
        f"- Recorded legacy-DNP references: `{len(legacy_dnp)}`",
        f"- Current short-collision references: `{', '.join(collision_refs) if collision_refs else 'none'}`",
        "- Evidence: `ref/photos/dgsh5-109-009-sb/rf-option-disposition.json`",
    ]
    if shorts or clearances or crossings:
        lines += [
            "",
            "The source PCB is not eligible for routed-copper adoption while any short remains.",
            "Fix new collisions using target-revision placement evidence.",
        ]
    else:
        lines += ["", "The source PCB has no copper short, clearance, or track-crossing violation and passes this gate."]
    OUTPUT.write_text("\n".join(lines) + "\n")
    print(f"source PCB DRC: {status}; shorts={len(shorts)}, clearances={len(clearances)}, crossings={len(crossings)}, unique={len(unique)}")
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")
    return 0 if not (shorts or clearances or crossings) else 1


if __name__ == "__main__":
    raise SystemExit(main())
