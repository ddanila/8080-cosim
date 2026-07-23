#!/usr/bin/env python3
import csv
import sys
from pathlib import Path


EXPECTED_ROWS = {
    "D1": {
        "disposition": "REVIEW REQUIRED - exact manual TVS",
        "evidence": "Littelfuse P4KE6.8A-B/C1666224 is guarded in the corrected DO-41 7.62 mm footprint.",
        "next_action": "Recheck stock, form the leads, verify the cathode band, and qualify the transient waveform on the first article.",
    },
    "J30": {
        "disposition": "REVIEW REQUIRED - exact vertical 1x15 CPN",
        "evidence": "Current footprint is PinHeader_1x15_P2.54mm_Vertical for owner-wired keyboard bring-up.",
        "next_action": "Install manually or select and verify an exact vertical 1x15 assembly-library header.",
    },
    "R6": {
        "disposition": "REVIEW REQUIRED - exact 0R axial CPN",
        "evidence": "Current footprint is DIN0207 axial; this row is a PWR_OK configuration jumper.",
        "next_action": "Install jumper manually or assign a footprint-matched factory 0R axial/link part.",
    },
    "R15": {
        "disposition": "REVIEW REQUIRED - exact 0R axial CPN",
        "evidence": "Current footprint is DIN0207 axial; this row is the keyboard encoder enable jumper.",
        "next_action": "Install jumper manually or assign a footprint-matched factory 0R axial/link part.",
    },
    "U50": {
        "disposition": "REVIEW REQUIRED - oscillator source/footprint",
        "evidence": "Current footprint is Oscillator_DIP-14 feeding the Rev A CLK net.",
        "next_action": "Install manually or change to a stocked, verified 5V oscillator package.",
    },
    "U51": {
        "disposition": "REVIEW REQUIRED - F-bondout reset supervisor",
        "evidence": "Current net order expects MCP130 F-bondout: 1=VSS, 2=RST, 3=VDD.",
        "next_action": "Install matching F-bondout supervisor manually; do not use D-bondout CPNs without rewiring.",
    },
}

for ref, purpose in {
    "J94": "decode-mode selector",
    "J95": "decode observability header",
    "J96": "clock selector",
    "J97": "framebuffer address header",
    "J98": "Z80 control header",
}.items():
    EXPECTED_ROWS[ref] = {
        "disposition": "REVIEW REQUIRED - manual bring-up header",
        "evidence": f"The engineering BOM deliberately assigns the {purpose} to owner-supplied manual assembly.",
        "next_action": "Install manually only after pin-1, silkscreen, and default-state review.",
    }

for number in range(32, 44):
    EXPECTED_ROWS[f"R{number}"] = {
        "disposition": "REVIEW REQUIRED - exact 4.7k axial CPN",
        "evidence": "This is an open-collector decode-PROM pull-up in a DIN0207 axial footprint.",
        "next_action": "Install a verified 4.7k axial part manually or assign a footprint-matched factory CPN.",
    }


def read_rows(path):
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def cell(row, name):
    return (row.get(name) or "").strip()


def table_row(values):
    escaped = [str(value).replace("|", "/") if value else "-" for value in values]
    return "| " + " | ".join(escaped) + " |"


def build_report(out_dir):
    rows = read_rows(out_dir / "assembly" / "manual-assembly.csv")
    refs = {cell(row, "Designator") for row in rows}
    expected_refs = set(EXPECTED_ROWS)
    unknown = sorted(ref for ref in refs if ref not in expected_refs)
    missing = sorted(ref for ref in expected_refs if ref not in refs)
    status = "READY" if not rows else "REVIEW REQUIRED"
    if unknown or missing:
        status = "NOT READY"

    lines = [
        "# Rev A manual-row readiness",
        "",
        f"Status: **{status}**",
        "",
        "This report is generated from `assembly/manual-assembly.csv` and records",
        "why each non-factory row is deliberately outside the JLCPCB assembly BOM.",
        "Known rows may still require human sign-off; unknown or missing rows fail",
        "the machine gate so manual assembly scope cannot drift silently.",
        "",
        "## Summary",
        "",
        f"- Manual/non-factory rows: {len(rows)}",
        f"- Known manual rows: {len(refs - set(unknown))}",
        f"- Unknown manual rows: {len(unknown)}",
        f"- Missing expected manual rows: {len(missing)}",
        "",
        "## Dispositions",
        "",
        "| Designator | Value | Footprint | Disposition | Evidence | Next action |",
        "| --- | --- | --- | --- | --- | --- |",
    ]

    for row in sorted(rows, key=lambda item: cell(item, "Designator")):
        ref = cell(row, "Designator")
        info = EXPECTED_ROWS.get(
            ref,
            {
                "disposition": "NOT READY - unknown manual row",
                "evidence": "This row is not in the Rev A manual-row policy table.",
                "next_action": "Classify this row before order export is considered coherent.",
            },
        )
        lines.append(
            table_row(
                [
                    ref,
                    cell(row, "Value"),
                    cell(row, "Footprint"),
                    info["disposition"],
                    info["evidence"],
                    info["next_action"],
                ]
            )
        )

    if missing:
        lines.extend(["", "## Missing Expected Rows", ""])
        for ref in missing:
            lines.append(f"- `{ref}`")

    if unknown:
        lines.extend(["", "## Unknown Rows", ""])
        for ref in unknown:
            lines.append(f"- `{ref}`")

    lines.append("")
    return "\n".join(lines), status


def main():
    out_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "fab/minimal-vga")
    report, status = build_report(out_dir)
    path = out_dir / "assembly" / "manual-row-readiness.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report)
    print(report)
    print(f"Wrote {path}")
    return 0 if status in {"READY", "REVIEW REQUIRED"} else 3


if __name__ == "__main__":
    raise SystemExit(main())
