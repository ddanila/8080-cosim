#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path


CHECK_COMMAND = ["spinoffs/minimal-vga/sim/check.sh"]

EXPECTED_MARKERS = [
    ("Main-project ROM regression (not VJUGA boot)", "BOOT-CHECK: PASS"),
    ("T80 minimal top", "[Z80-MIN] PASS"),
    ("Schematic/HDL LVS", "==> IN SYNC"),
    ("Rev A physical schematic target", "Rev A physical spec check: PASS"),
    ("Rev A PCB scaffold", "Rev A PCB scaffold check: PASS"),
    ("Fabrication DRC readiness", "Status: **READY**"),
    ("DRAM row/column model", "[DRAM-UNIT] PASS"),
]


def fenced_log(text):
    lines = ["```text"]
    lines.extend(text.rstrip().splitlines())
    lines.append("```")
    return lines


def build_report(returncode, output):
    missing = [name for name, marker in EXPECTED_MARKERS if marker not in output]
    status = (
        "SMOKE TESTS PASS / REAL VJUGA BOOT UNPROVEN"
        if returncode == 0 and not missing
        else "SMOKE TESTS FAILED"
    )
    lines = [
        "# Rev A behavioral readiness",
        "",
        f"Status: **{status}**",
        "",
        "This report captures current smoke, structural, and package checks. The",
        "main-project ROM/cosim regression protects shared code but does not run",
        "the VJUGA top. VJUGA itself still executes only its synthetic T80 ROM.",
        "",
        "## Summary",
        "",
        f"- Command: `{' '.join(CHECK_COMMAND)}`",
        f"- Exit code: {returncode}",
        f"- Expected markers found: {len(EXPECTED_MARKERS) - len(missing)}",
        f"- Expected markers missing: {len(missing)}",
        "",
        "## Markers",
        "",
        "| Check | Marker | Status |",
        "| --- | --- | --- |",
    ]
    for name, marker in EXPECTED_MARKERS:
        marker_status = "PASS" if marker in output else "FAIL"
        lines.append(f"| {name} | `{marker}` | {marker_status} |")

    if missing:
        lines.extend(["", "## Missing Markers", ""])
        lines.extend(f"- {name}" for name in missing)

    lines.extend(["", "## Log", ""])
    lines.extend(fenced_log(output))
    lines.append("")
    return "\n".join(lines), status


def main():
    out_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "fab/minimal-vga")
    result = subprocess.run(
        CHECK_COMMAND,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    report, status = build_report(result.returncode, result.stdout)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "behavioral-readiness.md"
    path.write_text(report)
    print(report)
    print(f"Wrote {path}")
    return 0 if status == "SMOKE TESTS PASS / REAL VJUGA BOOT UNPROVEN" else 3


if __name__ == "__main__":
    raise SystemExit(main())
