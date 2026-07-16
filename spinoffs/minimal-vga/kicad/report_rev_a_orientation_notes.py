#!/usr/bin/env python3
import csv
import re
import sys
from pathlib import Path


REQUIRED_SECTIONS = (
    "## Factory Assembly Intent",
    "## Manual / Non-Factory Placements",
    "## Socket Orientation",
    "## Post-Assembly IC Insertion",
    "## Polarized Parts",
    "## Connector Notes",
)

REQUIRED_PHRASES = (
    "Do not factory-populate the socketed ICs themselves",
    "manual-assembly.csv",
    "Install every DIP socket with its notch/key matching the silkscreen notch",
    "`U..` refdes is placed on the keyed short side",
    "chip name printed inside each DIP outline follows the long axis",
)

POLARIZED_COVERAGE = ("D1", "D2`-`D7", "C50")
CONNECTOR_COVERAGE = ("J1", "J3", "J30", "J40", "J90`-`J93", "U40")
POST_INSERTION_COVERAGE = (
    "Z0840004PSC",
    "27C256",
    "KM4164B-10",
    "`U10`-`U17`",
    "GAL/PAL",
    "К556РТ4",
    "К155РЕ3",
    "`U6`",
    "82C55",
    "socketed 74HCT logic",
)


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_text(path):
    return path.read_text(encoding="utf-8", errors="replace")


def normalized(text):
    return re.sub(r"\s+", " ", text).strip().lower()


def contains_ref(text, ref):
    return f"`{ref}`" in text or ref in text


def build_report(out_dir):
    assembly_notes = out_dir / "assembly" / "rev-a-assembly-orientation-notes.md"
    upload_notes = out_dir / "upload" / "vjuga-rev-a-assembly-notes.md"
    manual_csv = out_dir / "assembly" / "manual-assembly.csv"
    post_csv = out_dir / "assembly" / "post-assembly-insertion.csv"
    upload_readme = out_dir / "upload" / "README-upload.md"
    sha256_file = out_dir / "upload" / "SHA256SUMS.txt"

    failures = []
    paths = [assembly_notes, upload_notes, manual_csv, post_csv, upload_readme, sha256_file]
    for path in paths:
        if not path.exists() or path.stat().st_size == 0:
            failures.append(f"missing required orientation-note input: {path.relative_to(out_dir)}")

    notes_text = read_text(assembly_notes) if assembly_notes.exists() else ""
    upload_text = read_text(upload_notes) if upload_notes.exists() else ""
    readme_text = read_text(upload_readme) if upload_readme.exists() else ""
    sha_text = read_text(sha256_file) if sha256_file.exists() else ""

    if notes_text and upload_text and notes_text != upload_text:
        failures.append("upload assembly notes differ from assembly/rev-a-assembly-orientation-notes.md")
    if "upload/vjuga-rev-a-assembly-notes.md" not in sha_text:
        failures.append("SHA256SUMS.txt does not cover upload/vjuga-rev-a-assembly-notes.md")
    if "assembly notes" not in normalized(readme_text):
        failures.append("upload README does not tell the user to review assembly notes")

    section_rows = []
    for section in REQUIRED_SECTIONS:
        present = section in notes_text
        section_rows.append({"Item": section, "Status": "PASS" if present else "FAIL"})
        if not present:
            failures.append(f"missing notes section: {section}")

    phrase_rows = []
    for phrase in REQUIRED_PHRASES:
        present = phrase in notes_text
        phrase_rows.append({"Item": phrase, "Status": "PASS" if present else "FAIL"})
        if not present:
            failures.append(f"missing notes phrase: {phrase}")

    manual_refs = [row.get("Designator", "") for row in read_csv(manual_csv)] if manual_csv.exists() else []
    manual_rows = []
    for ref in manual_refs:
        present = contains_ref(notes_text, ref)
        manual_rows.append({"Item": ref, "Status": "PASS" if present else "FAIL"})
        if not present:
            failures.append(f"manual row {ref} is not called out in assembly notes")

    post_refs = [row.get("Designator", "") for row in read_csv(post_csv)] if post_csv.exists() else []
    coverage_rows = []
    for item in POST_INSERTION_COVERAGE:
        present = item in notes_text
        coverage_rows.append({"Item": item, "Status": "PASS" if present else "FAIL"})
        if not present:
            failures.append(f"post-assembly insertion coverage missing: {item}")
    for item in POLARIZED_COVERAGE:
        present = item in notes_text
        coverage_rows.append({"Item": item, "Status": "PASS" if present else "FAIL"})
        if not present:
            failures.append(f"polarized part coverage missing: {item}")
    for item in CONNECTOR_COVERAGE:
        present = item in notes_text
        coverage_rows.append({"Item": item, "Status": "PASS" if present else "FAIL"})
        if not present:
            failures.append(f"connector/orientation coverage missing: {item}")

    status = "READY" if not failures else "NOT READY"
    lines = [
        "# Rev A orientation-notes readiness",
        "",
        f"Package: `{out_dir}`",
        f"Status: **{status}**",
        "",
        "This report verifies that the assembly/orientation notes shipped with",
        "the upload package cover the Rev A manual rows, socket orientation,",
        "post-assembly IC insertion, polarized parts, and connector notes. It",
        "does not replace checking the notes against the final vendor order UI.",
        "",
        "## Summary",
        "",
        f"- Notes source present: {'yes' if assembly_notes.exists() else 'no'}",
        f"- Upload notes copy present: {'yes' if upload_notes.exists() else 'no'}",
        f"- Upload notes match source: {'yes' if notes_text and upload_text and notes_text == upload_text else 'no'}",
        f"- Manual rows referenced: {sum(1 for row in manual_rows if row['Status'] == 'PASS')} / {len(manual_refs)}",
        f"- Post-assembly insertion CSV rows: {len(post_refs)}",
        f"- Required sections checked: {len(REQUIRED_SECTIONS)}",
        f"- Required coverage items checked: {len(coverage_rows)}",
        f"- Orientation-note failures: {len(failures)}",
        "",
        "## Required Sections",
        "",
        "| Item | Status |",
        "| --- | --- |",
    ]
    for row in section_rows:
        lines.append("| {Item} | {Status} |".format(**row))
    lines.extend(["", "## Required Phrases", "", "| Item | Status |", "| --- | --- |"])
    for row in phrase_rows:
        safe = {key: str(value).replace("|", "/") for key, value in row.items()}
        lines.append("| {Item} | {Status} |".format(**safe))
    lines.extend(["", "## Manual Rows", "", "| Item | Status |", "| --- | --- |"])
    for row in manual_rows:
        lines.append("| {Item} | {Status} |".format(**row))
    lines.extend(["", "## Coverage Items", "", "| Item | Status |", "| --- | --- |"])
    for row in coverage_rows:
        lines.append("| {Item} | {Status} |".format(**row))
    if failures:
        lines.extend(["", "## Failures", ""])
        lines.extend(f"- {failure}" for failure in failures)
    lines.append("")
    return "\n".join(lines), not failures


def main():
    out_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "fab/minimal-vga")
    report, ready = build_report(out_dir)
    report_path = out_dir / "assembly" / "orientation-notes-readiness.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report)
    print(report)
    print(f"Wrote {report_path}")
    return 0 if ready else 3


if __name__ == "__main__":
    raise SystemExit(main())
