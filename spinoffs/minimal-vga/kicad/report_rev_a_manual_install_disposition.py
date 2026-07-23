#!/usr/bin/env python3
import csv
import sys
from pathlib import Path


EXPECTED_MANUAL = {
    "D1": "Manual-install exact Littelfuse P4KE6.8A-B/C1666224 in the corrected DO-41 footprint; cathode band to pad 1/VCC, then inspect lead forming and qualify the transient waveform.",
    "J30": "Manual-install the 1x15 keyboard bring-up header when keyboard wiring is needed; it is not required for first power/clock/ROM-fetch checks.",
    "R6": "Manual-install a 0R/jumper link for PWR_OK-to-VCC when using the simple Rev A power-good indication path.",
    "R15": "Manual-install a 0R/jumper link so the 74148 keyboard encoder enable is active by default.",
    "U50": "Manual-install a DIP-14-compatible 5V oscillator before any powered logic bring-up.",
    "U51": "Manual-install an F-bondout reset supervisor matching 1=VSS, 2=RST, 3=VDD; do not substitute D-bondout MCP130 parts.",
}

for ref, purpose in {
    "J94": "decode-mode selector",
    "J95": "decode observability header",
    "J96": "clock selector",
    "J97": "framebuffer address header",
    "J98": "Z80 control header",
}.items():
    EXPECTED_MANUAL[ref] = (
        f"Manual-install the {purpose} after checking pin 1, silkscreen orientation, and its safe default state."
    )

for number in range(32, 44):
    EXPECTED_MANUAL[f"R{number}"] = (
        "Manual-install a verified 4.7k axial pull-up for the open-collector decode-PROM output."
    )

EXPECTED_POST_INSERTION = {
    "U1",
    "U2",
    "U3",
    "U4",
    "U5",
    "U6",
    "U10",
    "U11",
    "U12",
    "U13",
    "U14",
    "U15",
    "U16",
    "U17",
    "U20",
    "U21",
    "U22",
    "U24",
    "U30",
    "U31",
    "U41",
}


def read_csv(path):
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def cell(row, name):
    return (row.get(name) or "").strip()


def table_row(values):
    return "| " + " | ".join(str(value).replace("|", "/") if value else "-" for value in values) + " |"


def same_file(left, right):
    return left.exists() and right.exists() and left.read_bytes() == right.read_bytes()


def build_report(out_dir):
    assembly_manual = out_dir / "assembly" / "manual-assembly.csv"
    upload_manual = out_dir / "upload" / "vjuga-rev-a-manual-assembly.csv"
    assembly_post = out_dir / "assembly" / "post-assembly-insertion.csv"
    upload_post = out_dir / "upload" / "vjuga-rev-a-post-assembly-insertion.csv"
    upload_notes = out_dir / "upload" / "vjuga-rev-a-assembly-notes.md"

    manual_rows = read_csv(assembly_manual)
    upload_manual_rows = read_csv(upload_manual)
    post_rows = read_csv(assembly_post)
    upload_post_rows = read_csv(upload_post)
    notes = upload_notes.read_text(errors="replace") if upload_notes.exists() else ""

    failures = []
    manual_refs = {cell(row, "Designator") for row in manual_rows}
    upload_manual_refs = {cell(row, "Designator") for row in upload_manual_rows}
    post_refs = {cell(row, "Designator") for row in post_rows}
    upload_post_refs = {cell(row, "Designator") for row in upload_post_rows}

    if manual_refs != set(EXPECTED_MANUAL):
        failures.append(
            "Manual rows differ from Rev A disposition: "
            f"expected {', '.join(sorted(EXPECTED_MANUAL))}; found {', '.join(sorted(manual_refs))}"
        )
    if post_refs != EXPECTED_POST_INSERTION:
        failures.append(
            "Post-assembly insertion rows differ from Rev A policy: "
            f"expected {len(EXPECTED_POST_INSERTION)}, found {len(post_refs)}"
        )
    if upload_manual_refs != manual_refs or not same_file(assembly_manual, upload_manual):
        failures.append("Upload manual-assembly CSV does not exactly match generated assembly/manual-assembly.csv.")
    if upload_post_refs != post_refs or not same_file(assembly_post, upload_post):
        failures.append("Upload post-assembly insertion CSV does not exactly match generated assembly/post-assembly-insertion.csv.")
    if not upload_notes.exists() or upload_notes.stat().st_size == 0:
        failures.append("Upload assembly notes are missing or empty.")

    for ref in EXPECTED_MANUAL:
        row = next((item for item in manual_rows if cell(item, "Designator") == ref), {})
        if cell(row, "Action") != "Manual":
            failures.append(f"{ref}: expected Action=Manual.")
        if "manual" not in cell(row, "Sourcing").lower():
            failures.append(f"{ref}: expected manual/owner sourcing.")
        if f"`{ref}`" not in notes and ref not in notes:
            failures.append(f"{ref}: upload assembly notes do not mention the manual row.")

    for ref in EXPECTED_POST_INSERTION:
        row = next((item for item in post_rows if cell(item, "Designator") == ref), {})
        if "owner-supplied" not in cell(row, "Action").lower():
            failures.append(f"{ref}: expected owner-supplied post-assembly insertion action.")

    status = "READY" if not failures else "NOT READY"
    lines = [
        "# Rev A manual-install disposition",
        "",
        f"Package: `{out_dir}`",
        f"Status: **{status}**",
        "",
        "This report freezes the Rev A decision to keep 23 mechanically or",
        "sourcing-sensitive rows out of factory assembly and install them manually",
        "during bring-up. It also verifies that the upload bundle carries the same",
        "manual and post-assembly insertion CSVs generated by the assembly exporter.",
        "",
        "## Summary",
        "",
        f"- Manual install rows: {len(manual_rows)}",
        f"- Post-assembly socket insertions: {len(post_rows)}",
        f"- Upload manual CSV matches source: {'yes' if same_file(assembly_manual, upload_manual) else 'no'}",
        f"- Upload post-insertion CSV matches source: {'yes' if same_file(assembly_post, upload_post) else 'no'}",
        f"- Disposition failures: {len(failures)}",
        "",
        "## Manual Install Rows",
        "",
        "| Designator | Value | Footprint | Rev A disposition |",
        "| --- | --- | --- | --- |",
    ]

    for row in sorted(manual_rows, key=lambda item: cell(item, "Designator")):
        ref = cell(row, "Designator")
        lines.append(
            table_row(
                [
                    ref,
                    cell(row, "Value"),
                    cell(row, "Footprint"),
                    EXPECTED_MANUAL.get(ref, "No Rev A disposition recorded."),
                ]
            )
        )

    lines.extend(
        [
            "",
            "## Post-Assembly Socket Insertions",
            "",
            "| Designator | Device | Socket | Action |",
            "| --- | --- | --- | --- |",
        ]
    )
    for row in sorted(post_rows, key=lambda item: cell(item, "Designator")):
        lines.append(table_row([cell(row, "Designator"), cell(row, "Device"), cell(row, "Socket"), cell(row, "Action")]))

    if failures:
        lines.extend(["", "## Failures", ""])
        lines.extend(f"- {failure}" for failure in failures)

    lines.append("")
    return "\n".join(lines), status


def main():
    out_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "fab/minimal-vga")
    report, status = build_report(out_dir)
    path = out_dir / "assembly" / "manual-install-disposition.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report)
    print(report)
    print(f"Wrote {path}")
    return 0 if status == "READY" else 3


if __name__ == "__main__":
    raise SystemExit(main())
