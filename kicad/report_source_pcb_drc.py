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
COLLISION_DISPOSITION = {
    "L1": ("VD3", "L1 is still an unregistered three-pad tapped-coil stand-in; the factory/photo-proven VD3 centre now disproves this placeholder location, so locate the actual coil holes before moving it"),
    "R68": ("D102", "R68 placement is only an approximate analog-grid seed; locate the physical SND_MIX resistor from target-board imagery or continuity"),
    "R69": ("D102", "R69 placement is only an approximate analog-grid seed; locate the physical D34_SIG resistor from target-board imagery or continuity"),
    "R73": ("D97", "R73 is a three-terminal RF-bias trimmer, not a lower-FDC-row part; register its physical body before moving it"),
    "R74": ("D102", "R74 placement is only an approximate analog-grid seed; locate the physical VT3 emitter resistor from target-board imagery or continuity"),
    "C13": ("D95", "the assembly-drawing site formerly read as C13 is proved to be C63; the real C13 position still requires target-board evidence"),
}


def item_ref(description: str) -> str | None:
    match = re.search(r"\bof ([A-Z]+\d+)\b", description)
    return match.group(1) if match else None


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
        "## Placement disposition",
        "",
        "The D95/D97/D102 package centres and VD3 body centre are registered by independent owner-photo",
        "fits and the factory assembly drawing. Each collision instead involves a",
        "passive whose current coordinate is explicitly approximate; moving an IC to",
        "clear one of these shorts would regress known-good placement.",
        "",
        "| Approximate part | Fixed registered anchor | Required evidence |",
        "| --- | --- | --- |",
    ]
    seen_approximate: set[str] = set()
    for violation in unique.values():
        refs = {ref for item in violation.get("items", [])
                if (ref := item_ref(str(item.get("description", ""))))}
        for ref in sorted(refs & COLLISION_DISPOSITION.keys()):
            if ref in seen_approximate:
                continue
            seen_approximate.add(ref)
            anchor, evidence = COLLISION_DISPOSITION[ref]
            lines.append(f"| `{ref}` | `{anchor}` | {evidence} |")
    unexpected = sorted({
        ref for violation in unique.values() for item in violation.get("items", [])
        if (ref := item_ref(str(item.get("description", ""))))
        and ref not in COLLISION_DISPOSITION
        and ref not in {anchor for anchor, _ in COLLISION_DISPOSITION.values()}
    })
    lines += [
        "",
        f"- Classified approximate collision parts: `{len(seen_approximate)}/{len(COLLISION_DISPOSITION)}`",
        f"- Unexpected collision references: `{', '.join(unexpected) if unexpected else 'none'}`",
    ]
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
