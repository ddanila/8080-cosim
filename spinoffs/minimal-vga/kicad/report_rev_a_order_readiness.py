#!/usr/bin/env python3
import csv
import sys
from pathlib import Path


REQUIRED_ARTIFACTS = [
    "erc-readiness.md",
    "fab-readiness.md",
    "fab-notes.md",
    "rev-a.engineering-bom.csv",
    "gerbers/rev-a-physical-F_Cu.gtl",
    "gerbers/rev-a-physical-In1_Cu.g1",
    "gerbers/rev-a-physical-In2_Cu.g2",
    "gerbers/rev-a-physical-B_Cu.gbl",
    "gerbers/rev-a-physical-F_Mask.gts",
    "gerbers/rev-a-physical-B_Mask.gbs",
    "gerbers/rev-a-physical-F_Silkscreen.gto",
    "gerbers/rev-a-physical-B_Silkscreen.gbo",
    "gerbers/rev-a-physical-Edge_Cuts.gm1",
    "gerbers/rev-a-physical-job.gbrjob",
    "drill/rev-a-physical.drl",
    "assembly/assembly-readiness.md",
    "assembly/socket-fit-readiness.md",
    "assembly/mechanical-fit-readiness.md",
    "assembly/manual-row-readiness.md",
    "assembly/cpn-consistency.md",
    "assembly/jlcpcb-bom-draft.csv",
    "assembly/jlcpcb-cpl-draft.csv",
    "assembly/manual-assembly.csv",
    "assembly/post-assembly-insertion.csv",
    "assembly/rev-a-position.csv",
    "assembly/rev-a-jlcpcb-cpn-checklist.csv",
    "assembly/rev-a-assembly-orientation-notes.md",
    "review/rev-a-physical-schematic.pdf",
    "review/rev-a-assembly-front.pdf",
    "review/rev-a-assembly-back.pdf",
    "upload/vjuga-rev-a-gerbers-drill.zip",
    "upload/vjuga-rev-a-jlcpcb-bom.csv",
    "upload/vjuga-rev-a-jlcpcb-cpl.csv",
    "upload/vjuga-rev-a-manual-assembly.csv",
    "upload/vjuga-rev-a-post-assembly-insertion.csv",
    "upload/vjuga-rev-a-assembly-notes.md",
    "upload/README-upload.md",
    "upload/SHA256SUMS.txt",
    "upload/package-manifest.md",
]

OPTIONAL_REVIEW_ARTIFACTS = [
    "review/rev-a-top-bare.png",
    "review/rev-a-top-populated.png",
    "review/vjuga-placement-top.png",
    "review/vjuga-placement-top.svg",
]

HUMAN_GATES = [
    "Independent Gerber/drill inspection in an external viewer.",
    "Full schematic review against the intended Z80, ROM, DRAM, refresh, keyboard, and VGA behavior.",
    "Trace geometry, via count, power width, and return-path review on the autorouted baseline.",
    "Decision on whether to restore GND/+5V pours before ordering.",
    "Socket/header footprint fit check against the exact purchased sockets and connectors.",
    "Mechanical-fit review for J1, R30, and R31 before factory population.",
    "Order-time JLCPCB/LCSC CPN stock and footprint confirmation for every factory-mounted row.",
    "Confirmation that the selected assembly service will mount the intended through-hole sockets/connectors.",
    "Manual-row decisions for TVS protection, keyboard header, oscillator, reset supervisor, and configuration links.",
]


def read_text(path):
    if not path.exists():
        return ""
    return path.read_text(errors="replace")


def csv_rows(path):
    if not path.exists():
        return []
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def designator(row):
    return row.get("Designator") or row.get("Reference") or row.get("Ref") or ""


def description(row):
    return row.get("Description") or row.get("Value") or row.get("Device") or row.get("Comment") or ""


def artifact_status(out_dir, names):
    missing = []
    present = []
    for name in names:
        path = out_dir / name
        if path.exists() and path.stat().st_size > 0:
            present.append(name)
        else:
            missing.append(name)
    return present, missing


def has_ready_line(text, label):
    return f"Status: **{label}**" in text


def machine_gate_summary(out_dir):
    erc = read_text(out_dir / "erc-readiness.md")
    fab = read_text(out_dir / "fab-readiness.md")
    assembly = read_text(out_dir / "assembly" / "assembly-readiness.md")
    socket_fit = read_text(out_dir / "assembly" / "socket-fit-readiness.md")
    mechanical_fit = read_text(out_dir / "assembly" / "mechanical-fit-readiness.md")
    manual_rows_report = read_text(out_dir / "assembly" / "manual-row-readiness.md")
    cpn_consistency = read_text(out_dir / "assembly" / "cpn-consistency.md")
    upload_manifest = read_text(out_dir / "upload" / "package-manifest.md")

    gates = [
        (
            "KiCad ERC",
            has_ready_line(erc, "READY") and "- ERC violations: 0" in erc,
            "`erc-readiness.md` reports zero error-level violations.",
        ),
        (
            "KiCad DRC/unconnected",
            has_ready_line(fab, "READY")
            and "- DRC violations: 0" in fab
            and "- Unconnected items: 0" in fab,
            "`fab-readiness.md` reports zero DRC violations and zero unconnected items.",
        ),
        (
            "JLCPCB assembly draft",
            has_ready_line(assembly, "READY")
            and (
                "- Missing LCSC part numbers: 0" in assembly
                or "- BOM rows missing LCSC part numbers: 0" in assembly
            )
            and (
                "- Rows with TBD sourcing/notes: 0" in assembly
                or "- BOM rows with TBD sourcing/notes: 0" in assembly
            ),
            "`assembly/assembly-readiness.md` reports a coherent BOM/CPL draft.",
        ),
        (
            "Socket footprint fit",
            has_ready_line(socket_fit, "READY")
            and "- Socket fit failures: 0" in socket_fit,
            "`assembly/socket-fit-readiness.md` confirms socket pin counts and widths.",
        ),
        (
            "Mechanical fit report",
            (
                has_ready_line(mechanical_fit, "READY")
                or has_ready_line(mechanical_fit, "REVIEW REQUIRED")
            )
            and "- Mechanical fit failures: 0" in mechanical_fit,
            "`assembly/mechanical-fit-readiness.md` reports no hard mechanical mismatches; review rows still need human sign-off.",
        ),
        (
            "Manual row dispositions",
            (
                has_ready_line(manual_rows_report, "READY")
                or has_ready_line(manual_rows_report, "REVIEW REQUIRED")
            )
            and "- Unknown manual rows: 0" in manual_rows_report
            and "- Missing expected manual rows: 0" in manual_rows_report,
            "`assembly/manual-row-readiness.md` records explicit dispositions for every manual/non-factory row.",
        ),
        (
            "CPN consistency",
            (
                has_ready_line(cpn_consistency, "READY")
                or has_ready_line(cpn_consistency, "REVIEW REQUIRED")
            )
            and "- CPN consistency failures: 0" in cpn_consistency,
            "`assembly/cpn-consistency.md` cross-checks generated BOM CPNs against the engineering BOM and sourcing checklist.",
        ),
        (
            "Upload package",
            "# VJUGA Rev A upload package manifest" in upload_manifest
            and "- JLCPCB BOM rows:" in upload_manifest
            and "- JLCPCB CPL placements:" in upload_manifest
            and "`upload/vjuga-rev-a-gerbers-drill.zip`" in upload_manifest,
            "`upload/package-manifest.md` records the Gerber ZIP, BOM/CPL, notes, and checksums.",
        ),
    ]
    return gates


def table_lines(rows, columns):
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for row in rows:
        values = []
        for column in columns:
            value = str(row.get(column, "")).strip()
            values.append(value.replace("|", "/") if value else "-")
        lines.append("| " + " | ".join(values) + " |")
    return lines


def build_report(out_dir):
    present_required, missing_required = artifact_status(out_dir, REQUIRED_ARTIFACTS)
    present_optional, missing_optional = artifact_status(out_dir, OPTIONAL_REVIEW_ARTIFACTS)
    gates = machine_gate_summary(out_dir)
    manual_rows = csv_rows(out_dir / "assembly" / "manual-assembly.csv")
    post_rows = csv_rows(out_dir / "assembly" / "post-assembly-insertion.csv")
    failed_gates = [name for name, passed, _ in gates if not passed]
    machine_ready = not missing_required and not failed_gates
    status = "DRAFT - HUMAN REVIEW REQUIRED" if machine_ready else "NOT READY"

    lines = [
        "# Rev A order readiness",
        "",
        f"Package: `{out_dir}`",
        f"Status: **{status}**",
        "",
        "This report is a machine-generated order checklist. A clean machine gate",
        "means the package is internally coherent; it does not replace human",
        "schematic, Gerber, routing, sourcing, and assembly review.",
        "",
        "## Machine Gates",
        "",
    ]
    for name, passed, detail in gates:
        result = "PASS" if passed else "FAIL"
        lines.append(f"- {name}: **{result}** - {detail}")
    artifact_result = "PASS" if not missing_required else "FAIL"
    lines.append(
        f"- Required fabrication artifacts: **{artifact_result}** - "
        f"{len(present_required)} present, {len(missing_required)} missing."
    )
    optional_result = "PASS" if not missing_optional else "WARN"
    lines.append(
        f"- Optional review previews: **{optional_result}** - "
        f"{len(present_optional)} present, {len(missing_optional)} missing."
    )
    lines.extend(
        [
            f"- Manual/non-factory rows: **INFO** - {len(manual_rows)} rows are intentionally excluded from factory assembly.",
            f"- Post-assembly insertions: **INFO** - {len(post_rows)} owner-supplied socketed parts are listed.",
        ]
    )

    if missing_required:
        lines.extend(["", "## Missing Required Artifacts", ""])
        for name in missing_required:
            lines.append(f"- `{name}`")

    if missing_optional:
        lines.extend(["", "## Missing Optional Review Previews", ""])
        for name in missing_optional:
            lines.append(f"- `{name}`")

    lines.extend(["", "## Required Human Sign-Off Before Upload", ""])
    for gate in HUMAN_GATES:
        lines.append(f"- [ ] {gate}")

    lines.extend(["", "## Manual / Non-Factory Rows", ""])
    if manual_rows:
        wanted = [name for name in ["Designator", "Value", "Description", "Assembly", "Notes"] if name in manual_rows[0]]
        lines.extend(table_lines(manual_rows, wanted))
    else:
        lines.append("No manual assembly rows found.")

    lines.extend(["", "## Post-Assembly Insertions", ""])
    if post_rows:
        for row in post_rows:
            ref = designator(row)
            desc = description(row)
            lines.append(f"- `{ref}`: {desc}" if desc else f"- `{ref}`")
    else:
        lines.append("No post-assembly insertion rows found.")

    lines.append("")
    return "\n".join(lines), machine_ready


def main():
    out_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "fab/minimal-vga")
    report, machine_ready = build_report(out_dir)
    report_path = out_dir / "order-readiness.md"
    report_path.write_text(report)
    print(report)
    print(f"Wrote {report_path}")
    return 0 if machine_ready else 3


if __name__ == "__main__":
    raise SystemExit(main())
