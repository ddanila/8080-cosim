#!/usr/bin/env python3
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ORDER_READINESS = ROOT / "kicad" / "report_order_readiness.py"
ORDER_EVIDENCE_TEMPLATE = ROOT / "kicad" / "report_replica_order_evidence_template.py"
UPLOAD_RUNBOOK = ROOT / "kicad" / "report_replica_order_upload_runbook.py"
DEFAULT_FAB_DIR = ROOT / "fab" / "gerbers"
DEFAULT_REPORT = ROOT / "docs" / "replica-manufacturing-readiness.md"

REQUIRED_REPORTS = [
    ("Main-board ERC/parity", "docs/main-board-erc-parity.md", "# Main-board ERC and schematic/PCB parity"),
    ("PPI orientation", "docs/ppi-orientation-audit.md", "# PPI physical orientation audit"),
    ("X8 electrolytic footprints", "docs/x8-electrolytic-footprint-audit.md", "# X8 C31–C33 footprint audit"),
    ("Order readiness", "fab/gerbers/order-readiness.md", "# Main board order readiness"),
    ("Upload runbook", "docs/replica-order-upload-runbook.md", "Status: **PACKAGE VERIFIED / DESIGN RELEASE SEPARATE**"),
    ("Package geometry", "docs/replica-package-geometry-readiness.md", "Status: **READY**"),
    ("DRC visual disposition", "docs/replica-fab-drc-disposition.md", "Status: **READY**"),
    ("Power trace readiness", "docs/replica-power-trace-readiness.md", "Status: **READY**"),
    ("Bring-up verification points", "docs/replica-bringup-verification-points.md", "# Replica bring-up verification points"),
    ("Sourcing readiness", "docs/replica-sourcing-readiness.md", "# Replica sourcing readiness"),
    ("Factory wire construction", "docs/factory-wire-route-fidelity.md", "# Factory insulated-wire route fidelity"),
    ("Order evidence template", "docs/replica-order-evidence-template.md", "# Replica order evidence template"),
    ("External Gerber review", "fab/gerbers/external-gerber-review.md", "Status: **READY**"),
    ("Review waiver", "fab/gerbers/review-waivers.md", "Status: **ACCEPTED**"),
    ("Fabrication readiness", "fab/gerbers/fab-readiness.md", "Fabrication-file inventory gate: **PASS**"),
]

# These reports are valid evidence even while the design is held, but their
# summary row must not say PASS until their actual release condition is true.
# Package-only reports intentionally keep the marker-presence PASS semantics.
RELEASE_MARKERS = {
    "docs/main-board-erc-parity.md": "Status: **READY**",
    "docs/ppi-orientation-audit.md": "Status: **READY**",
    "docs/x8-electrolytic-footprint-audit.md": "Status: **READY**",
    "fab/gerbers/order-readiness.md": "Status: **RELEASED FOR ORDER**",
    "docs/replica-bringup-verification-points.md": "Status: **DESIGN RELEASE RISKS CLOSED**",
    "docs/replica-sourcing-readiness.md": "Status: **SOURCING READY**",
    "docs/factory-wire-route-fidelity.md": "Status: **FACTORY WIRE CONSTRUCTION PRESERVED**",
}

LOCKED_VENDOR_OPTIONS = [
    ("Service", "PCB fabrication only; no factory assembly package for the replica main board"),
    ("Layers", "2"),
    ("Material/thickness", "FR-4, 1.6 mm"),
    ("Board outline", "310 mm x 266 mm Edge.Cuts coordinate box"),
    ("Rendered job size", "310.15 mm x 266.15 mm profile-aperture envelope"),
    ("Drill file", "one mixed-plating Excellon drill file"),
    ("Impedance/stackup", "do not request impedance control or stackup changes"),
]

EXPECTED_UPLOAD_DIR_FILES = {
    "juku-replica-gerbers-drill.zip",
    "SHA256SUMS.txt",
}


def repo_relative(path):
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def table_row(values):
    return "| " + " | ".join(str(value).replace("|", "/") if value not in (None, "") else "-" for value in values) + " |"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_hashes(path):
    hashes = {}
    if not path.exists():
        return hashes
    for line in path.read_text(errors="replace").splitlines():
        parts = line.split(None, 1)
        if len(parts) == 2:
            hashes[parts[1].strip()] = parts[0]
    return hashes


def run_order_readiness(fab_dir):
    return subprocess.run([
        sys.executable,
        str(ORDER_READINESS),
        str(ROOT / "kicad" / "juku_routed.kicad_pcb"),
        str(fab_dir),
    ], cwd=ROOT, text=True, capture_output=True)


def run_order_evidence_template(fab_dir):
    return subprocess.run([
        sys.executable,
        str(ORDER_EVIDENCE_TEMPLATE),
        str(fab_dir),
    ], cwd=ROOT, text=True, capture_output=True)


def refresh_upload_runbook(fab_dir):
    return subprocess.run([
        sys.executable,
        str(UPLOAD_RUNBOOK),
        str(fab_dir),
    ], cwd=ROOT, text=True, capture_output=True)


def first_match(text, pattern, default="-"):
    match = re.search(pattern, text, re.M)
    return match.group(1).strip() if match else default


def toolchain_rows(fab_dir):
    fab_text = (fab_dir / "fab-readiness.md").read_text(errors="replace")
    external_text = (fab_dir / "external-gerber-review.md").read_text(errors="replace")
    upload_text = (ROOT / "docs" / "replica-order-upload-runbook.md").read_text(errors="replace")
    job = json.loads((fab_dir / "juku_routed-job.gbrjob").read_text())
    generation = job.get("Header", {}).get("GenerationSoftware", {})
    return [
        ("KiCad CLI", first_match(fab_text, r"^KiCad CLI: `([^`]+)`")),
        ("KiCad CLI version", first_match(fab_text, r"^KiCad version: `([^`]+)`")),
        (
            "Gerber job generator",
            " ".join(
                value
                for value in [
                    generation.get("Vendor", ""),
                    generation.get("Application", ""),
                    generation.get("Version", ""),
                ]
                if value
            ),
        ),
        ("External viewer", first_match(external_text, r"^Viewer: `([^`]+)`")),
        ("Upload ZIP format", first_match(upload_text, r"^- Required metadata: (.+)$")),
    ]


def build_report(fab_dir):
    failures = []
    source_stamp = fab_dir / "source-board.sha256"
    current_board_sha = sha256(ROOT / "kicad" / "juku_routed.kicad_pcb")
    if not source_stamp.exists() or source_stamp.read_text().strip() != current_board_sha:
        failures.append("fabrication source-board.sha256 is absent or differs from the current routed PCB")
    order_result = run_order_readiness(fab_dir)
    # report_order_readiness returns 3 after successfully writing a coherent
    # NOT READY / DESIGN HOLD report.  Only other nonzero codes mean its
    # regeneration failed; the report's own status remains the release gate.
    if order_result.returncode not in (0, 3):
        detail = order_result.stderr.strip() or order_result.stdout.strip()
        failures.append("order-readiness regeneration failed" + (f": {detail}" if detail else ""))
    evidence_result = run_order_evidence_template(fab_dir)
    # The evidence-template generator likewise uses 3 for a valid template
    # whose prerequisite reports are held.  Its FAIL rows are consumed below;
    # do not duplicate the entire generated template as a process failure.
    if evidence_result.returncode not in (0, 3):
        detail = evidence_result.stderr.strip() or evidence_result.stdout.strip()
        failures.append("order-evidence-template regeneration failed" + (f": {detail}" if detail else ""))
    # Order readiness generates the upload runbook before the evidence template.
    # Refresh the runbook once after the template so its retained-evidence byte
    # counts describe the final files from this invocation, not the prior run.
    runbook_result = refresh_upload_runbook(fab_dir)
    if runbook_result.returncode not in (0, 3):
        detail = runbook_result.stderr.strip() or runbook_result.stdout.strip()
        failures.append("upload-runbook refresh failed" + (f": {detail}" if detail else ""))

    report_rows = []
    release_gates_ready = True
    for label, rel, marker in REQUIRED_REPORTS:
        path = ROOT / rel
        exists = path.exists() and path.stat().st_size > 0
        text = path.read_text(errors="replace") if exists else ""
        marker_ok = marker in text if marker else True
        if not exists:
            failures.append(f"missing or empty required report: {rel}")
        elif not marker_ok:
            failures.append(f"required report marker missing in {rel}: {marker}")
        release_marker = RELEASE_MARKERS.get(rel)
        if release_marker is not None and release_marker not in text:
            release_gates_ready = False
        gate_status = (
            "FAIL"
            if not exists or not marker_ok
            else "PASS"
            if release_marker is None or release_marker in text
            else "HOLD"
        )
        report_rows.append([
            label,
            f"`{rel}`",
            path.stat().st_size if exists else 0,
            gate_status,
        ])

    upload_zip = fab_dir / "upload" / "juku-replica-gerbers-drill.zip"
    upload_sha = upload_zip.parent / "SHA256SUMS.txt"
    root_sha = fab_dir / "SHA256SUMS"
    zip_digest = sha256(upload_zip) if upload_zip.exists() and upload_zip.stat().st_size else ""
    upload_hashes = read_hashes(upload_sha)
    root_hashes = read_hashes(root_sha)
    upload_dir_files = sorted(path for path in upload_zip.parent.iterdir() if path.is_file()) if upload_zip.parent.exists() else []
    upload_dir_names = {path.name for path in upload_dir_files}
    if upload_dir_names != EXPECTED_UPLOAD_DIR_FILES:
        failures.append(
            "upload directory contains unexpected file set: "
            + ", ".join(sorted(upload_dir_names))
        )
    if upload_hashes.get(upload_zip.name) != zip_digest:
        failures.append("upload SHA256SUMS.txt does not match the final upload ZIP")

    upload_members = [
        "juku_routed-F_Cu.gtl",
        "juku_routed-B_Cu.gbl",
        "juku_routed-F_Mask.gts",
        "juku_routed-B_Mask.gbs",
        "juku_routed-F_Silkscreen.gto",
        "juku_routed-B_Silkscreen.gbo",
        "juku_routed-Edge_Cuts.gm1",
        "juku_routed-job.gbrjob",
        "juku_routed.drl",
    ]
    missing_root_hashes = [name for name in upload_members if name not in root_hashes]
    if missing_root_hashes:
        failures.append("root SHA256SUMS missing upload member(s): " + ", ".join(missing_root_hashes))

    tools = toolchain_rows(fab_dir)
    for label, value in tools:
        if value == "-":
            failures.append(f"missing toolchain provenance: {label}")

    order_path = ROOT / "fab" / "gerbers" / "order-readiness.md"
    order_text = order_path.read_text(errors="replace") if order_path.exists() else ""
    released = (
        "Status: **RELEASED FOR ORDER**" in order_text
        and release_gates_ready
    )
    if failures:
        status = "PACKAGE INVALID"
    elif released:
        status = "RELEASED FOR UPLOAD"
    else:
        status = "DESIGN HOLD / PACKAGE VERIFIED"
    lines = [
        "# Replica manufacturing readiness",
        "",
        f"Status: **{status}**",
        f"Fabrication package: `{repo_relative(fab_dir)}`",
        f"Final upload ZIP: `{repo_relative(upload_zip)}`",
        f"Final upload ZIP SHA256: `{zip_digest or '-'}`",
        f"Routed PCB SHA256: `{current_board_sha}`",
        f"Fabrication source stamp: `{source_stamp.read_text().strip() if source_stamp.exists() else '-'}`",
        "",
        "This is the tracked top-level manufacturing packet for the replica main",
        "board. It separates reproducible package integrity from functional design",
        "release. A verified package must not be uploaded while the status is",
        "DESIGN HOLD.",
        "",
        "Archive review adds a physical-layout hold: `docs/ppi-orientation-audit.md`",
        "records D26 and D27 PPI orientations on the owner board that disagree",
        "with their current 90° routed footprints. D26 is horizontal with its",
        "notch at the right, as does D27 under X2 in both factory and owner",
        "evidence. The current 90° KiCad footprints are left-notched. The",
        "package-geometry gate below checks outline, layers, and drill export;",
        "it does not validate IC orientation or physical pin-to-net mapping.",
        "Release requires a local pin-center fit, corrected PPI footprints and",
        "routing, and renewed electrical and visual review.",
        "The current routed PCB has 40/40 net mismatches at the photographed physical",
        "pin positions on each PPI; see `docs/ppi-physical-pin-mapping.json`.",
        "The X8 power corner has a separate footprint hold: C31–C33 remain on",
        "2 mm radial footprints in all PCB variants, while the .009 assembly and",
        "owner photos show axial cans with about 25–26 mm lead spacing. See",
        "`docs/x8-electrolytic-footprint-audit.md`; register the six original",
        "joints and replace/reroute the footprints before fabrication.",
        "The timer cluster has a separate placement hold: owner component and solder",
        "photos place D54's lower pin row about 23 mm above the physical bottom edge,",
        "while the routed row is only 7.38 mm above Edge.Cuts. See",
        "`docs/photo-registration.md`; D54/D55/D57 and adjacent D26 need a mechanical",
        "fit before fabrication, regardless of the package-geometry gate below.",
        "The lower-right mounting hole seen on both board faces is also absent from",
        "the routed Edge.Cuts; its approximate photo coordinate needs a dimensioned",
        "fit before adding the drill.",
        "",
        "## Gate Summary",
        "",
        "| Gate | Evidence | Bytes | Status |",
        "| --- | --- | ---: | --- |",
    ]
    lines.extend(table_row(row) for row in report_rows)

    lines.extend([
        "",
        "## Toolchain Provenance",
        "",
        "| Tool | Version / command |",
        "| --- | --- |",
    ])
    lines.extend(table_row(row) for row in tools)

    lines.extend([
        "",
        "## Final Upload Directory",
        "",
        "| File | Bytes | SHA256 | Status |",
        "| --- | ---: | --- | --- |",
    ])
    for path in upload_dir_files:
        expected = path.name in EXPECTED_UPLOAD_DIR_FILES
        lines.append(table_row([
            f"`{repo_relative(path)}`",
            path.stat().st_size,
            f"`{sha256(path)}`",
            "PASS" if expected else "FAIL",
        ]))

    lines.extend([
        "",
        "## Locked Vendor Options",
        "",
        "| Option | Value |",
        "| --- | --- |",
    ])
    lines.extend(table_row(row) for row in LOCKED_VENDOR_OPTIONS)

    lines.extend([
        "",
        "## Required release/pre-payment command",
        "",
        "```sh",
        "kicad/check_replica_manufacturing_ready.sh",
        "```",
        "",
        "## External evidence to save after design release",
        "",
        "Use `docs/replica-order-evidence-template.md` for the private order record.",
        "Use `docs/replica-first-article-record.md` for each received and assembled",
        "physical unit; package verification and vendor evidence do not substitute for",
        "as-built identity or acceptance testing.",
        "",
        "- Vendor preview screenshots.",
        "- Quoted fabrication options and price.",
        "- Vendor order number.",
        "- The final upload ZIP checksum above.",
        "- Confirmation that `fab/gerbers/order-readiness.md` says `RELEASED FOR ORDER`.",
        "- Confirmation that the package was regenerated after the final D2/D94",
        "  changes, FDC-support functional pin dispositions, and source-risk",
        "  net corrections.",
    ])

    if failures:
        lines.extend(["", "## Failures", ""])
        lines.extend(f"- {failure}" for failure in failures)

    lines.append("")
    return "\n".join(lines), not failures


def main():
    fab_dir = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT_FAB_DIR
    report_path = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else DEFAULT_REPORT
    report, ok = build_report(fab_dir)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report)
    print(report)
    print(f"Wrote {repo_relative(report_path)}")
    return 0 if ok else 3


if __name__ == "__main__":
    raise SystemExit(main())
