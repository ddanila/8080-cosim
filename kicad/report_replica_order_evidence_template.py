#!/usr/bin/env python3
import hashlib
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FAB_DIR = ROOT / "fab" / "gerbers"
DEFAULT_REPORT = ROOT / "docs" / "replica-order-evidence-template.md"
UPLOAD_ZIP_NAME = "juku-replica-gerbers-drill.zip"
UPLOAD_SHA_NAME = "SHA256SUMS.txt"

REQUIRED_EVIDENCE = [
    ("Upload runbook", "docs/replica-order-upload-runbook.md", "Status: **READY**"),
    ("Package geometry", "docs/replica-package-geometry-readiness.md", "Status: **READY**"),
    ("DRC visual disposition", "docs/replica-fab-drc-disposition.md", "Status: **READY**"),
    ("Bring-up verification points", "docs/replica-bringup-verification-points.md", "Status: **READY**"),
]

VENDOR_OPTIONS = [
    ("Vendor", ""),
    ("Order/project number", ""),
    ("Quote timestamp and currency", ""),
    ("Quantity", ""),
    ("Layers", "2"),
    ("Material/thickness", "FR-4, 1.6 mm"),
    ("Board size shown by vendor", ""),
    ("Drill files accepted", ""),
    ("Soldermask color", ""),
    ("Silkscreen color", ""),
    ("Surface finish", ""),
    ("Copper weight", ""),
    ("Electrical test option", ""),
    ("Impedance/stackup option", "none / not requested"),
    ("Notes sent to vendor", ""),
]

SCREENSHOT_EVIDENCE = [
    f"Upload file list showing `{UPLOAD_ZIP_NAME}`.",
    "Vendor top copper preview.",
    "Vendor bottom copper preview.",
    "Vendor top soldermask/silkscreen preview.",
    "Vendor bottom soldermask/silkscreen preview.",
    "Vendor board-outline/drill preview showing the 310 mm x 266 mm class outline.",
    "Quoted fabrication options and price.",
    "Final order confirmation page with order number.",
]

REVIEW_CHECKS = [
    "Re-ran the pre-payment gate above after the vendor ZIP upload was selected.",
    "Vendor preview agrees with `docs/replica-package-geometry-readiness.md`.",
    "Top/bottom orientation agrees with `fab/gerbers/review/tracespace/`.",
    "Accepted DRC classes in `docs/replica-fab-drc-disposition.md` remain acceptable in the vendor preview.",
    "Reviewed `docs/replica-bringup-verification-points.md`; none of the listed residual source-risk nets block PCB fabrication.",
    "Vendor did not enable impedance control or change the 2-layer stackup.",
    "Final quoted options match the locked options in `docs/replica-manufacturing-readiness.md`.",
    "Upload ZIP SHA256 above is saved with the order.",
]


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


def evidence_rows():
    failures = []
    rows = []
    for label, rel, marker in REQUIRED_EVIDENCE:
        path = ROOT / rel
        exists = path.exists() and path.stat().st_size > 0
        text = path.read_text(errors="replace") if exists else ""
        marker_ok = marker in text if marker else True
        if not exists:
            failures.append(f"missing or empty evidence file: {rel}")
        elif not marker_ok:
            failures.append(f"evidence marker missing in {rel}: {marker}")
        rows.append([
            label,
            f"`{rel}`",
            path.stat().st_size if exists else 0,
            "PASS" if exists and marker_ok else "FAIL",
        ])
    return rows, failures


def build_report(fab_dir):
    failures = []
    upload_zip = fab_dir / "upload" / UPLOAD_ZIP_NAME
    upload_sha = upload_zip.parent / UPLOAD_SHA_NAME
    zip_exists = upload_zip.exists() and upload_zip.stat().st_size > 0
    zip_digest = sha256(upload_zip) if zip_exists else "-"
    upload_hashes = read_hashes(upload_sha)
    recorded_digest = upload_hashes.get(UPLOAD_ZIP_NAME, "")

    if not zip_exists:
        failures.append(f"missing or empty upload ZIP: {repo_relative(upload_zip)}")
    if not upload_sha.exists() or upload_sha.stat().st_size == 0:
        failures.append(f"missing or empty upload checksum file: {repo_relative(upload_sha)}")
    elif recorded_digest != zip_digest:
        failures.append(
            f"upload checksum file is stale: recorded {recorded_digest or '-'}, computed {zip_digest}"
        )
    extra_hashes = sorted(set(upload_hashes) - {UPLOAD_ZIP_NAME})
    if extra_hashes:
        failures.append("unexpected upload checksum entries: " + ", ".join(extra_hashes))

    rows, evidence_failures = evidence_rows()
    failures.extend(evidence_failures)

    status = "READY" if not failures else "NOT READY"
    lines = [
        "# Replica order evidence template",
        "",
        f"Status: **{status}**",
        "",
        "Copy this checklist into the private order record when the replica main-board",
        "fabrication order is placed. Do not fill it in ahead of the vendor UI; live DFM,",
        "price, and order-number evidence only exists after upload/quotation.",
        "",
        "## Pre-Payment Gate",
        "",
        "```sh",
        "kicad/check_replica_manufacturing_ready.sh",
        "```",
        "",
        "Expected result: `replica manufacturing readiness: READY TO UPLOAD`.",
        "",
        "## Upload Artifact",
        "",
        "| Field | Value |",
        "| --- | --- |",
        table_row(["Upload ZIP", f"`{repo_relative(upload_zip)}`"]),
        table_row(["Upload ZIP SHA256", f"`{zip_digest}`" if zip_digest != "-" else "-"]),
        table_row(["Upload checksum command", f"`(cd {repo_relative(upload_zip.parent)} && sha256sum -c {UPLOAD_SHA_NAME})`"]),
        "",
        "## Required Source Evidence",
        "",
        "| Purpose | File | Bytes | Status |",
        "| --- | --- | ---: | --- |",
    ]
    lines.extend(table_row(row) for row in rows)

    lines.extend([
        "",
        "## Vendor Options To Record",
        "",
        "| Field | Recorded value |",
        "| --- | --- |",
    ])
    lines.extend(table_row(row) for row in VENDOR_OPTIONS)

    lines.extend(["", "## Screenshot Evidence To Save", ""])
    lines.extend(f"- {item}" for item in SCREENSHOT_EVIDENCE)

    lines.extend(["", "## Review Before Payment", ""])
    lines.extend(f"- [ ] {check}" for check in REVIEW_CHECKS)

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
