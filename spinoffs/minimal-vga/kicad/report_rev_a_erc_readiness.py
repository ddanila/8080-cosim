#!/usr/bin/env python3
import json
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path


def run_erc(schematic, out_dir):
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "erc-report.json"
    cmd = [
        os.environ.get("KICAD_CLI", "kicad-cli"),
        "sch",
        "erc",
        "--severity-error",
        "--format",
        "json",
        "--output",
        str(json_path),
        str(schematic),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)
    return json_path


def all_violations(erc):
    violations = list(erc.get("violations", []))
    for sheet in erc.get("sheets", []):
        violations.extend(sheet.get("violations", []))
    return violations


def item_texts(violation):
    return [item.get("description", "") for item in violation.get("items", [])]


def symbol_refs(violations):
    refs = Counter()
    for violation in violations:
        for text in item_texts(violation):
            match = re.search(r"\bSymbol\s+(\S+)\s+Pin\s+(\S+)", text)
            if match:
                refs[match.group(1)] += 1
    return refs


def sample_lines(violations, limit=12):
    lines = []
    for violation in violations[:limit]:
        items = "; ".join(item_texts(violation))
        lines.append(
            f"- `{violation.get('type', 'unknown')}`: "
            f"{violation.get('description', 'No description')} ({items})"
        )
    return lines


def build_report(schematic, erc):
    violations = all_violations(erc)
    by_type = Counter(item.get("type", "unknown") for item in violations)
    by_severity = Counter(item.get("severity", "unknown") for item in violations)
    refs = symbol_refs(violations)
    status = "NOT READY" if violations else "READY"

    lines = [
        "# Rev A schematic ERC readiness",
        "",
        f"Schematic: `{schematic}`",
        f"Status: **{status}**",
        "",
        "## ERC Summary",
        "",
        f"- ERC violations: {len(violations)}",
    ]
    for severity, count in sorted(by_severity.items()):
        lines.append(f"- `{severity}` severity: {count}")

    if by_type:
        lines.extend(["", "## Violation Types", ""])
        for typ, count in sorted(by_type.items()):
            lines.append(f"- `{typ}`: {count}")

    if refs:
        lines.extend(["", "## Top Affected References", ""])
        for ref, count in refs.most_common(16):
            lines.append(f"- `{ref}`: {count}")

    if violations:
        lines.extend(["", "## First Findings", ""])
        lines.extend(sample_lines(violations))

    lines.extend(["", "## Manufacturing Gate", ""])
    if status == "READY":
        lines.append(
            "KiCad ERC has zero error-level violations. Human schematic review "
            "still applies before ordering."
        )
    else:
        lines.append(
            "The schematic is not ERC-clean yet. Treat this as an order blocker "
            "until remaining unused pins, one-node labels, and intentional "
            "no-connects are resolved or explicitly marked."
        )
    lines.append("")
    return "\n".join(lines)


def main():
    schematic = Path(
        sys.argv[1]
        if len(sys.argv) > 1
        else "spinoffs/minimal-vga/kicad/rev-a-physical.kicad_sch"
    )
    out_dir = Path(sys.argv[2] if len(sys.argv) > 2 else "fab/minimal-vga")
    json_path = run_erc(schematic, out_dir)
    erc = json.loads(json_path.read_text())
    report = build_report(schematic, erc)
    report_path = out_dir / "erc-readiness.md"
    report_path.write_text(report + "\n")
    print(report)
    print(f"Wrote {report_path}")
    if all_violations(erc):
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
