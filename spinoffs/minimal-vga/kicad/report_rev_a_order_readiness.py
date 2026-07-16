#!/usr/bin/env python3
import csv
import sys
from pathlib import Path


REQUIRED_ARTIFACTS = [
    "source-model-readiness.md",
    "schematic-intent-readiness.md",
    "router-readiness.md",
    "behavioral-readiness.md",
    "erc-readiness.md",
    "fab-readiness.md",
    "routing-geometry-readiness.md",
    "routing-disposition-readiness.md",
    "mounting-hole-readiness.md",
    "diagnostic-led-readiness.md",
    "power-budget-readiness.md",
    "drill-readiness.md",
    "fab-package-integrity.md",
    "external-gerber-review.md",
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
    "assembly/socket-insertion-policy.md",
    "assembly/mechanical-fit-readiness.md",
    "assembly/manual-row-readiness.md",
    "assembly/manual-install-disposition.md",
    "assembly/cpn-consistency.md",
    "assembly/vendor-order-checklist.md",
    "assembly/orientation-notes-readiness.md",
    "order-upload-runbook.md",
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
    "review/tracespace/rev-a-physical.top.svg",
    "review/tracespace/rev-a-physical.bottom.svg",
    "review/tracespace/rev-a-physical-tracespace-top.png",
    "review/tracespace/rev-a-physical-tracespace-bottom.png",
]

HUMAN_GATES = [
    "Program and bench-validate the U5/U24 GAL equations on the selected physical devices.",
    "Independent Gerber/drill inspection in an external viewer.",
    "Full schematic review against the intended Z80, ROM, DRAM, refresh, keyboard, and VGA behavior.",
    "Order-time visual routing review against the generated routing geometry and disposition reports.",
    "Confirm the filled In1.Cu GND and In2.Cu VCC planes, island/return paths, and 0.20 mm VCC_RAW routing remain intentional.",
    "Select PCB fabrication only / no assembly in the vendor UI for this first concept sample.",
    "Upload only `upload/vjuga-rev-a-gerbers-drill.zip`; keep BOM/CPL files as later assembly references.",
    "Save vendor Gerber preview, stackup/settings, price, and order-number evidence.",
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
    source_model = read_text(out_dir / "source-model-readiness.md")
    schematic_intent = read_text(out_dir / "schematic-intent-readiness.md")
    router = read_text(out_dir / "router-readiness.md")
    behavioral = read_text(out_dir / "behavioral-readiness.md")
    erc = read_text(out_dir / "erc-readiness.md")
    fab = read_text(out_dir / "fab-readiness.md")
    routing_geometry = read_text(out_dir / "routing-geometry-readiness.md")
    routing_disposition = read_text(out_dir / "routing-disposition-readiness.md")
    mounting_holes = read_text(out_dir / "mounting-hole-readiness.md")
    diagnostic_leds = read_text(out_dir / "diagnostic-led-readiness.md")
    power_budget = read_text(out_dir / "power-budget-readiness.md")
    drill = read_text(out_dir / "drill-readiness.md")
    fab_package_integrity = read_text(out_dir / "fab-package-integrity.md")
    external_gerber_review = read_text(out_dir / "external-gerber-review.md")
    assembly = read_text(out_dir / "assembly" / "assembly-readiness.md")
    socket_fit = read_text(out_dir / "assembly" / "socket-fit-readiness.md")
    socket_insertion = read_text(out_dir / "assembly" / "socket-insertion-policy.md")
    mechanical_fit = read_text(out_dir / "assembly" / "mechanical-fit-readiness.md")
    manual_rows_report = read_text(out_dir / "assembly" / "manual-row-readiness.md")
    manual_install_disposition = read_text(out_dir / "assembly" / "manual-install-disposition.md")
    cpn_consistency = read_text(out_dir / "assembly" / "cpn-consistency.md")
    vendor_order_checklist = read_text(out_dir / "assembly" / "vendor-order-checklist.md")
    orientation_notes = read_text(out_dir / "assembly" / "orientation-notes-readiness.md")
    order_upload_runbook = read_text(out_dir / "order-upload-runbook.md")
    upload_manifest = read_text(out_dir / "upload" / "package-manifest.md")

    gates = [
        (
            "Physical source model",
            has_ready_line(source_model, "READY")
            and "- Required refs missing: 0" in source_model
            and "- Required nets missing: 0" in source_model
            and "- Required pin-binding failures: 0" in source_model
            and "- Unknown net endpoints: 0" in source_model
            and "- Multi-net pin conflicts: 0" in source_model
            and "- No-connect conflicts: 0" in source_model,
            "`source-model-readiness.md` records Rev A ref/net/pin-binding and no-connect policy before schematic export.",
        ),
        (
            "Schematic intent contract",
            has_ready_line(schematic_intent, "READY")
            and "- Checks: 134" in schematic_intent
            and "- Failures: 0" in schematic_intent
            and "Core CPU/ROM/decode" in schematic_intent
            and "DRAM and arbitration" in schematic_intent
            and "Keyboard" in schematic_intent
            and "Video/VGA" in schematic_intent
            and "Power/clock/reset/debug" in schematic_intent,
            "`schematic-intent-readiness.md` verifies the Rev A source model against the intended CPU, ROM, DRAM, keyboard, VGA, power, clock, and reset contracts.",
        ),
        (
            "Headless router fork",
            has_ready_line(router, "READY")
            and "- Failed checks: 0" in router
            and "Headless scheduler honors v1.9 router | PASS" in router
            and "VJUGA route script defaults to v1.9 | PASS" in router,
            "`router-readiness.md` records the custom Freerouting fork and VJUGA headless v1.9 route path.",
        ),
        (
            "Behavioral simulation/LVS",
            has_ready_line(behavioral, "BEHAVIORAL REGRESSIONS PASS")
            and "- Exit code: 0" in behavioral
            and "- Expected markers missing: 0" in behavioral,
            "`behavioral-readiness.md` records both real-ROM VJUGA implementations plus synthetic smoke, U24 timing, readback, LVS, physical, PCB, DRC, and DRAM checks.",
        ),
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
            "Routing geometry summary",
            (
                has_ready_line(routing_geometry, "READY")
                or has_ready_line(routing_geometry, "REVIEW REQUIRED")
            )
            and "- Hard geometry failures: 0" in routing_geometry,
            "`routing-geometry-readiness.md` records track widths, via count, power routing, and zone policy.",
        ),
        (
            "Routing/plane disposition",
            has_ready_line(routing_disposition, "READY")
            and "- Disposition failures: 0" in routing_disposition
            and "VCC_RAW uses the accepted Rev A prototype routing width of 0.20 mm" in routing_disposition
            and "VCC and GND use filled inner-layer planes" in routing_disposition,
            "`routing-disposition-readiness.md` records the filled VCC/GND planes and explicit VCC_RAW routing with measured limits.",
        ),
        (
            "Mounting-hole geometry",
            has_ready_line(mounting_holes, "READY")
            and "- Expected mounting holes: 4" in mounting_holes
            and "- Detected mounting holes: 4" in mounting_holes
            and "- Mounting-hole failures: 0" in mounting_holes,
            "`mounting-hole-readiness.md` verifies the Rev A corner mounting-hole count, diameter, edge web, and local clearance.",
        ),
        (
            "Diagnostic LED loading",
            has_ready_line(diagnostic_leds, "READY")
            and "- Diagnostic LEDs checked: 6" in diagnostic_leds
            and "- Estimated current per lit LED: 1.36 mA" in diagnostic_leds
            and "- Diagnostic LED failures: 0" in diagnostic_leds,
            "`diagnostic-led-readiness.md` verifies diagnostic LED topology, BOM CPNs, and conservative current loading.",
        ),
        (
            "Power/fuse budget",
            has_ready_line(power_budget, "READY")
            and "- Planning budget: 1.81 A" in power_budget
            and "- Fuse hold current: 3.00 A" in power_budget
            and "- Power-budget failures: 0" in power_budget,
            "`power-budget-readiness.md` verifies the +5V planning budget, F1 candidate, and raw-to-fused power-entry topology.",
        ),
        (
            "Excellon drill export",
            has_ready_line(drill, "READY")
            and "- Excellon drill hits: 869" in drill
            and "- PCB pad/via drill features: 869" in drill
            and "- Drill readiness failures: 0" in drill,
            "`drill-readiness.md` compares the exported Excellon drill file against PCB pad/via drill features and documents Edge.Cuts mounting cutouts.",
        ),
        (
            "Fabrication package integrity",
            has_ready_line(fab_package_integrity, "READY")
            and "- Integrity failures: 0" in fab_package_integrity
            and "- Expected fabrication files: 11" in fab_package_integrity,
            "`fab-package-integrity.md` verifies Gerber/drill ZIP contents, deterministic metadata, format markers, and SHA256 entries.",
        ),
        (
            "External Gerber/drill render",
            has_ready_line(external_gerber_review, "READY")
            and "Viewer: `@tracespace/cli`" in external_gerber_review
            and "rev-a-physical.top.svg" in external_gerber_review
            and "rev-a-physical.bottom.svg" in external_gerber_review
            and "## Failures" not in external_gerber_review,
            "`external-gerber-review.md` records a Tracespace render pass over the exported Gerbers and drill file.",
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
            "Socket insertion policy",
            has_ready_line(socket_insertion, "READY")
            and "- Socketed IC footprints: 22" in socket_insertion
            and "- Policy failures: 0" in socket_insertion,
            "`assembly/socket-insertion-policy.md` confirms factory socket mounting and owner-supplied IC post-assembly insertion policy.",
        ),
        (
            "Mechanical fit report",
            (
                has_ready_line(mechanical_fit, "READY")
                or has_ready_line(mechanical_fit, "REVIEW REQUIRED")
            )
            and "- Mechanical fit failures: 0" in mechanical_fit,
            "`assembly/mechanical-fit-readiness.md` reports no hard mechanical mismatches.",
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
            "Manual install disposition",
            has_ready_line(manual_install_disposition, "READY")
            and "- Manual install rows: 23" in manual_install_disposition
            and "- Post-assembly socket insertions: 22" in manual_install_disposition
            and "- Upload manual CSV matches source: yes" in manual_install_disposition
            and "- Upload post-insertion CSV matches source: yes" in manual_install_disposition
            and "- Disposition failures: 0" in manual_install_disposition,
            "`assembly/manual-install-disposition.md` freezes the Rev A manual-install decision and verifies upload CSV parity.",
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
            "Vendor/order checklist",
            (
                has_ready_line(vendor_order_checklist, "READY")
                or has_ready_line(vendor_order_checklist, "REVIEW REQUIRED")
            )
            and "- Factory-mounted designators checked: 96" in vendor_order_checklist
            and "- Unique factory CPNs: 20" in vendor_order_checklist
            and "- Manual-install rows excluded from factory BOM: 23" in vendor_order_checklist
            and "- Post-assembly owner insertions: 22" in vendor_order_checklist
            and "- Vendor checklist failures: 0" in vendor_order_checklist,
            "`assembly/vendor-order-checklist.md` records the upload BOM CPN set, manual exclusions, post-assembly insertions, and order-time vendor/stock review rows.",
        ),
        (
            "Assembly orientation notes",
            has_ready_line(orientation_notes, "READY")
            and "- Manual rows referenced: 23 / 23" in orientation_notes
            and "- Post-assembly insertion CSV rows: 22" in orientation_notes
            and "- Orientation-note failures: 0" in orientation_notes,
            "`assembly/orientation-notes-readiness.md` verifies upload notes cover manual rows, socket orientation, post-assembly insertion, polarized parts, and connector notes.",
        ),
        (
            "Upload package",
            "# VJUGA Rev A upload package manifest" in upload_manifest
            and "- JLCPCB BOM rows:" in upload_manifest
            and "- JLCPCB CPL placements:" in upload_manifest
            and "`upload/vjuga-rev-a-gerbers-drill.zip`" in upload_manifest,
            "`upload/package-manifest.md` records the Gerber ZIP, retained BOM/CPL reference files, notes, and checksums.",
        ),
        (
            "Bare-PCB order-upload runbook",
            has_ready_line(order_upload_runbook, "PACKAGE VERIFIED / DESIGN HOLD")
            and "# VJUGA Rev A bare-PCB order-upload runbook" in order_upload_runbook
            and "Select PCB fabrication only / no assembly" in order_upload_runbook
            and "Upload only `vjuga-rev-a-gerbers-drill.zip`" in order_upload_runbook
            and "- Reference factory BOM rows retained: 29" in order_upload_runbook
            and "- Reference factory CPL placements retained: 96" in order_upload_runbook
            and "- Reference unique factory CPNs retained: 20" in order_upload_runbook
            and "- Manual-install rows retained for later assembly: 23" in order_upload_runbook
            and "- Owner post-assembly socket insertions retained for later assembly: 22" in order_upload_runbook
            and "- Expected ZIP members: 11" in order_upload_runbook
            and "- ZIP members found: 11" in order_upload_runbook
            and "file mode `0644`" in order_upload_runbook,
            "`order-upload-runbook.md` gives the exact bare-PCB upload file, checksum command, reproducible ZIP metadata, retained assembly references, and remaining order-time checks.",
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
    package_verified = not missing_required and not failed_gates
    status = "PACKAGE VERIFIED / DESIGN HOLD" if package_verified else "PACKAGE INVALID"

    lines = [
        "# Rev A bare-PCB order readiness",
        "",
        f"Package: `{out_dir}`",
        f"Status: **{status}**",
        "",
        "This report checks a possible future PCB-only package. A clean machine",
        "gate means only that the artifacts are internally coherent. Functional",
        "design release is blocked; do not upload or order this board.",
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
            f"- Reference manual/non-factory rows: **INFO** - {len(manual_rows)} retained for a later assembled-board path.",
            f"- Reference post-assembly insertions: **INFO** - {len(post_rows)} owner-supplied socketed parts retained for a later assembled-board path.",
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

    lines.extend(["", "## Required Release Work And Human Sign-Off", ""])
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
    return "\n".join(lines), package_verified


def main():
    out_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "fab/minimal-vga")
    report, package_verified = build_report(out_dir)
    report_path = out_dir / "order-readiness.md"
    report_path.write_text(report)
    print(report)
    print(f"Wrote {report_path}")
    return 0 if package_verified else 3


if __name__ == "__main__":
    raise SystemExit(main())
