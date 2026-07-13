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
        f"- Copper-clearance violations: `{len(clearances)}`",
        f"- Track-crossing violations: `{len(crossings)}`",
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
    collision_refs = sorted({
        ref for violation in unique.values() for item in violation.get("items", [])
        if (ref := item_ref(str(item.get("description", ""))))
    })
    lines += [
        "",
        "## Revision disposition",
        "",
        "The former ten collision pairs came from placing the `.006` dashed VT3/VT4 RF option",
        "on top of independently registered `.009` FDC parts. Complete `.009` assembly-drawing",
        "coverage and the owner-board component tiles show only VT1/VT2, while the archived group",
        "BOM assigns the adjustable trimmer and extra RF transistors to `.006`. The legacy-only",
        "population is therefore DNP on this target; reused C9/C10/C11/C12/C15 retain their `.009`",
        "factory positions with explicit continuity-boundary nets.",
        "",
        "R33 and R66 retain their independently photo-registered centres and orientations. Their",
        "nearest pads are 1.721 mm centre-to-centre; using 1.50 mm copper around the original-style",
        "0.80 mm drills preserves a 0.35 mm annulus and provides 0.221 mm copper clearance without",
        "moving either component.",
        "",
        f"- Guarded legacy-DNP references: `{len(legacy_dnp)}`",
        f"- Current collision references: `{', '.join(collision_refs) if collision_refs else 'none'}`",
        "- Evidence: `ref/photos/dgsh5-109-009-sb/rf-option-disposition.json`",
    ]
    if shorts or clearances or crossings:
        lines += [
            "",
            "The source PCB is not eligible for routed-copper adoption while any short remains.",
            "New collisions must be fixed from target-revision placement evidence, not waived.",
        ]
    else:
        lines += ["", "The source PCB has no copper short, clearance, or track-crossing violation and passes this gate."]
    OUTPUT.write_text("\n".join(lines) + "\n")
    print(f"source PCB DRC: {status}; shorts={len(shorts)}, clearances={len(clearances)}, crossings={len(crossings)}, unique={len(unique)}")
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")
    return 0 if not shorts else 1


if __name__ == "__main__":
    raise SystemExit(main())
