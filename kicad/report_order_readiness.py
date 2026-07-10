#!/usr/bin/env python3
import csv
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOARD = ROOT / "kicad" / "juku_routed.kicad_pcb"
DEFAULT_OUT_DIR = ROOT / "fab" / "gerbers"
FAB_REPORT = ROOT / "kicad" / "report_fab_readiness.py"
WAIVER_REPORT = ROOT / "kicad" / "report_review_waivers.py"
DUAL_BOM_REPORT = ROOT / "kicad" / "report_dual_config_bom.py"
SOURCING_REPORT = ROOT / "kicad" / "report_replica_sourcing_readiness.py"
EXTERNAL_GERBER_REPORT = ROOT / "kicad" / "report_external_gerber_review.py"
UPLOAD_RUNBOOK_REPORT = ROOT / "kicad" / "report_replica_order_upload_runbook.py"
POWER_TRACE_REPORT = ROOT / "kicad" / "report_replica_power_trace_readiness.py"
DRC_DISPOSITION_REPORT = ROOT / "kicad" / "report_replica_drc_disposition.py"
PACKAGE_GEOMETRY_REPORT = ROOT / "kicad" / "report_replica_package_geometry.py"

BLOCKING_DRC_TYPES = {
    "clearance",
    "shorting_items",
    "copper_edge_clearance",
    "lib_footprint_issues",
}
REVIEW_ONLY_DRC_TYPES = {
    "courtyards_overlap",
    "pth_inside_courtyard",
    "silk_over_copper",
    "silk_overlap",
    "text_thickness",
}


def repo_relative(path):
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def table_row(values):
    return "| " + " | ".join(str(value).replace("|", "/") for value in values) + " |"


def run_fab_readiness(board, out_dir):
    subprocess.run([str(FAB_REPORT), str(board), str(out_dir)], check=True)
    return out_dir / "juku_routed-drc.json"


def run_waiver_review(drc_path, out_dir):
    result = subprocess.run([
        str(WAIVER_REPORT),
        str(drc_path),
        str(out_dir / "review-waivers.md"),
    ])
    return result.returncode == 0


def run_dual_config_bom():
    subprocess.run([sys.executable, str(DUAL_BOM_REPORT)], check=True)
    csv_path = ROOT / "docs" / "replica-dual-config-bom.csv"
    with csv_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return {
        "lines": len(rows),
        "positions": sum(int(row["board_positions"]) for row in rows),
        "populate_now": sum(int(row["populate_now"]) for row in rows),
        "leave_empty": sum(int(row["leave_empty"]) for row in rows),
        "actions": sorted({row["action"] for row in rows}),
    }


def run_sourcing_readiness():
    subprocess.run([sys.executable, str(SOURCING_REPORT)], check=True)
    report_path = ROOT / "docs" / "replica-sourcing-readiness.md"
    text = report_path.read_text(errors="replace")
    return {
        "ready": "Status: **SOURCING READY**" in text and "## Failures" not in text,
        "report": report_path,
    }


def design_release_checks():
    checks = [
        (
            "D2 bus/wait PROM wiring and contents",
            ROOT / "docs" / "d2-reconstruction-constraints.md",
            "Status: **D2 RECONSTRUCTION READY**",
        ),
        (
            "D94 timing PROM wiring and contents",
            ROOT / "docs" / "d94-reconstruction-constraints.md",
            "Status: **D94 RECONSTRUCTION READY**",
        ),
        (
            "All placement-only functional IC dispositions",
            ROOT / "docs" / "unmodeled-footprint-inventory.md",
            "Status: **READY FOR DESIGN RELEASE**",
        ),
        (
            "Residual source-risk net dispositions",
            ROOT / "docs" / "replica-bringup-verification-points.md",
            "Status: **DESIGN RELEASE RISKS CLOSED**",
        ),
        (
            "Complete functional sourcing/programming decision",
            ROOT / "docs" / "replica-sourcing-readiness.md",
            "Status: **SOURCING READY**",
        ),
    ]
    rows = []
    for label, path, marker in checks:
        text = path.read_text(errors="replace") if path.exists() else ""
        rows.append({
            "label": label,
            "path": path,
            "ready": bool(text and marker in text),
            "required": marker,
        })
    return rows


def run_power_trace_readiness(board):
    result = subprocess.run([
        sys.executable,
        str(POWER_TRACE_REPORT),
        str(board),
    ], check=False)
    report_path = ROOT / "docs" / "replica-power-trace-readiness.md"
    text = report_path.read_text(errors="replace") if report_path.exists() else ""
    return {
        "ready": result.returncode == 0 and "Status: **READY**" in text and "## Failures" not in text,
        "report": report_path,
    }


def run_drc_disposition(drc_path):
    result = subprocess.run([
        sys.executable,
        str(DRC_DISPOSITION_REPORT),
        str(drc_path),
    ], check=False)
    report_path = ROOT / "docs" / "replica-fab-drc-disposition.md"
    text = report_path.read_text(errors="replace") if report_path.exists() else ""
    return {
        "ready": result.returncode == 0
        and "Status: **READY**" in text
        and "Visual disposition failures: 0" in text
        and "## Failures" not in text,
        "report": report_path,
    }


def run_package_geometry(out_dir):
    result = subprocess.run([
        sys.executable,
        str(PACKAGE_GEOMETRY_REPORT),
        str(out_dir),
    ], check=False)
    report_path = ROOT / "docs" / "replica-package-geometry-readiness.md"
    text = report_path.read_text(errors="replace") if report_path.exists() else ""
    return {
        "ready": result.returncode == 0
        and "Status: **READY**" in text
        and "310.000 x 266.000 mm" in text
        and "310.150 x 266.150 mm" in text
        and "mixed-plating Excellon drill file" in text
        and "## Failures" not in text,
        "report": report_path,
    }


def run_external_gerber_review(out_dir):
    subprocess.run([sys.executable, str(EXTERNAL_GERBER_REPORT), str(out_dir)], check=True)
    report_path = out_dir / "external-gerber-review.md"
    text = report_path.read_text(errors="replace")
    return {
        "ready": "Status: **READY**" in text and "## Failures" not in text,
        "report": report_path,
    }


def run_upload_runbook(out_dir):
    result = subprocess.run([
        sys.executable,
        str(UPLOAD_RUNBOOK_REPORT),
        str(out_dir),
    ], check=False)
    report_path = ROOT / "docs" / "replica-order-upload-runbook.md"
    text = report_path.read_text(errors="replace") if report_path.exists() else ""
    return {
        "ready": result.returncode == 0
        and "Status: **PACKAGE VERIFIED / DESIGN RELEASE SEPARATE**" in text
        and "## Upload ZIP Members" in text
        and "Source match" in text
        and "file mode `0644`" in text
        and "## Failures" not in text,
        "report": report_path,
    }


def build_report(board, out_dir, drc, waiver_accepted, bom, sourcing, power_trace, drc_disposition, package_geometry, external_review, upload_runbook=None):
    violations = drc.get("violations", [])
    unconnected = drc.get("unconnected_items", [])
    counts = Counter(v.get("type", "unknown") for v in violations)
    blocking_counts = Counter({name: counts.get(name, 0) for name in BLOCKING_DRC_TYPES})
    blocking_counts["unconnected_items"] = len(unconnected)
    unknown_types = sorted(set(counts) - BLOCKING_DRC_TYPES - REVIEW_ONLY_DRC_TYPES)

    machine_ready = (
        not any(blocking_counts.values())
        and not unknown_types
    )
    upload_ready = upload_runbook["ready"] if upload_runbook else False
    package_ready = (
        machine_ready
        and waiver_accepted
        and power_trace["ready"]
        and drc_disposition["ready"]
        and package_geometry["ready"]
        and external_review["ready"]
        and upload_ready
    )
    release_checks = design_release_checks()
    design_ready = all(row["ready"] for row in release_checks)
    order_ready = package_ready and design_ready
    if order_ready:
        status = "RELEASED FOR ORDER"
    elif package_ready:
        status = "PACKAGE READY / DESIGN HOLD"
    elif machine_ready:
        status = "PACKAGE INCOMPLETE"
    else:
        status = "NOT READY"

    lines = [
        "# Main board order readiness",
        "",
        f"Board: `{repo_relative(board)}`",
        f"Fabrication package: `{repo_relative(out_dir)}`",
        f"Status: **{status}**",
        "",
        "This gate separates machine-checkable fabrication blockers from dense",
        "placement and silkscreen findings that require human visual review or",
        "explicit waiver before placing an order.",
        "",
        "## Machine Blockers",
        "",
        "| Type | Count |",
        "| --- | ---: |",
    ]
    for name in sorted(blocking_counts):
        lines.append(table_row([name, blocking_counts[name]]))

    if unknown_types:
        lines.extend(["", "## Unknown DRC Types", ""])
        lines.extend(f"- `{name}`: {counts[name]}" for name in unknown_types)

    lines.extend([
        "",
        "## Review-Only DRC Types",
        "",
        "| Type | Count |",
        "| --- | ---: |",
    ])
    for name in sorted(REVIEW_ONLY_DRC_TYPES):
        if counts.get(name, 0):
            lines.append(table_row([name, counts[name]]))

    lines.extend([
        "",
        "## Waiver Gate",
        "",
        f"- Review-only waiver status: **{'ACCEPTED' if waiver_accepted else 'NOT ACCEPTED'}**",
        f"- Waiver report: `{repo_relative(out_dir / 'review-waivers.md')}`",
    ])

    lines.extend([
        "",
        "## External Gerber Review Gate",
        "",
        f"- Independent render status: **{'READY' if external_review['ready'] else 'NOT READY'}**",
        f"- Report: `{repo_relative(external_review['report'])}`",
    ])

    lines.extend([
        "",
        "## Parts / Sourcing Gate",
        "",
        "- Dual-config BOM status: **GENERATED**",
        "- Report: `docs/replica-dual-config-bom.md`",
        "- CSV: `docs/replica-dual-config-bom.csv`",
        f"- Sourcing readiness status: **{'READY' if sourcing['ready'] else 'NOT READY'}**",
        f"- Sourcing report: `{repo_relative(sourcing['report'])}`",
        f"- BOM lines: {bom['lines']}",
        f"- Board component positions: {bom['positions']}",
        f"- Current .009 populated parts: {bom['populate_now']}",
        f"- Empty expansion/authentic-completeness sockets: {bom['leave_empty']}",
        f"- Action classes: {', '.join(bom['actions'])}",
    ])

    lines.extend([
        "",
        "## Design Release Gate",
        "",
        "Package integrity and DRC are necessary but do not authorize fabrication.",
        "The following functional-design checks must all pass:",
        "",
        "| Check | Evidence | Result |",
        "| --- | --- | --- |",
    ])
    for row in release_checks:
        lines.append(table_row([
            row["label"],
            f"`{repo_relative(row['path'])}`",
            "PASS" if row["ready"] else "HOLD",
        ]))

    lines.extend([
        "",
        "## Power Trace Gate",
        "",
        f"- Power trace status: **{'READY' if power_trace['ready'] else 'NOT READY'}**",
        f"- Report: `{repo_relative(power_trace['report'])}`",
    ])

    lines.extend([
        "",
        "## DRC Visual Disposition Gate",
        "",
        f"- DRC disposition status: **{'READY' if drc_disposition['ready'] else 'NOT READY'}**",
        f"- Report: `{repo_relative(drc_disposition['report'])}`",
    ])

    lines.extend([
        "",
        "## Package Geometry Gate",
        "",
        f"- Package geometry status: **{'READY' if package_geometry['ready'] else 'NOT READY'}**",
        f"- Report: `{repo_relative(package_geometry['report'])}`",
    ])

    lines.extend([
        "",
        "## Order Upload Runbook Gate",
        "",
        f"- Upload runbook status: **{'READY' if upload_ready else 'NOT READY'}**",
        f"- Report: `{repo_relative(upload_runbook['report']) if upload_runbook else 'docs/replica-order-upload-runbook.md'}`",
        f"- Upload archive: `{repo_relative(out_dir / 'upload' / 'juku-replica-gerbers-drill.zip')}`",
    ])

    lines.extend(["", "## Disposition", ""])
    if order_ready:
        lines.append(
            "The package and functional design-release checks pass. Run the top-level "
            "pre-payment command and complete final vendor preview review."
        )
    elif package_ready:
        lines.append(
            "The existing Gerber/drill files are internally coherent, but the design "
            "release checks above are on hold. Do not upload or order this package; "
            "close the blockers, regenerate the PCB and package, and rerun every gate."
        )
    elif machine_ready:
        lines.append(
            "Machine blockers are clear: no clearance, short, unconnected, "
            "copper-edge, or footprint-library findings remain. The package can "
            "proceed once the waiver, sourcing, power-trace, DRC-disposition, "
            "package-geometry, external-render, and upload-runbook gates above "
            "are accepted."
        )
    else:
        lines.append(
            "Do not order until all machine blockers and unknown DRC classes above "
            "are resolved or deliberately reclassified."
        )
    lines.append("")
    return "\n".join(lines), package_ready


def main():
    board = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT_BOARD
    out_dir = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else DEFAULT_OUT_DIR
    drc_path = run_fab_readiness(board, out_dir)
    drc = json.loads(drc_path.read_text())
    waiver_accepted = run_waiver_review(drc_path, out_dir)
    bom = run_dual_config_bom()
    sourcing = run_sourcing_readiness()
    power_trace = run_power_trace_readiness(board)
    drc_disposition = run_drc_disposition(drc_path)
    package_geometry = run_package_geometry(out_dir)
    external_review = run_external_gerber_review(out_dir)
    report_path = out_dir / "order-readiness.md"
    preliminary, _ = build_report(board, out_dir, drc, waiver_accepted, bom, sourcing, power_trace, drc_disposition, package_geometry, external_review)
    report_path.write_text(preliminary)
    package_ready = False
    report = preliminary
    upload_runbook = None
    for _attempt in range(4):
        previous_report = report_path.read_text(errors="replace") if report_path.exists() else ""
        upload_runbook = run_upload_runbook(out_dir)
        report, package_ready = build_report(board, out_dir, drc, waiver_accepted, bom, sourcing, power_trace, drc_disposition, package_geometry, external_review, upload_runbook)
        report_path.write_text(report)
        if report == previous_report:
            break
    else:
        raise SystemExit("order-readiness/upload-runbook reports did not converge")
    print(report)
    print(f"Wrote {repo_relative(report_path)}")
    return 0 if package_ready else 3


if __name__ == "__main__":
    raise SystemExit(main())
