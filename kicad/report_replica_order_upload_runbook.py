#!/usr/bin/env python3
import hashlib
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FAB_DIR = ROOT / "fab" / "gerbers"
DEFAULT_REPORT = ROOT / "docs" / "replica-order-upload-runbook.md"

UPLOAD_FILES = [
    ("Top copper", "juku_routed-F_Cu.gtl"),
    ("Bottom copper", "juku_routed-B_Cu.gbl"),
    ("Top soldermask", "juku_routed-F_Mask.gts"),
    ("Bottom soldermask", "juku_routed-B_Mask.gbs"),
    ("Top silkscreen", "juku_routed-F_Silkscreen.gto"),
    ("Bottom silkscreen", "juku_routed-B_Silkscreen.gbo"),
    ("Board outline", "juku_routed-Edge_Cuts.gm1"),
    ("Gerber job", "juku_routed-job.gbrjob"),
    ("Excellon drill", "juku_routed.drl"),
]

RETAINED_EVIDENCE = [
    ("Order readiness", "order-readiness.md", "# Main board order readiness"),
    ("Fabrication readiness", "fab-readiness.md", "Fabrication-file inventory gate: **PASS**"),
    ("Review waiver", "review-waivers.md", "Status: **ACCEPTED**"),
    ("External Gerber review", "external-gerber-review.md", "Status: **READY**"),
    ("Power trace readiness", "docs/replica-power-trace-readiness.md", "Status: **READY**"),
    ("Checksum file", "SHA256SUMS", None),
]

ORDER_CHECKS = [
    "Upload only `upload/juku-replica-gerbers-drill.zip` for PCB fabrication.",
    "Confirm vendor preview reports a 2-layer board, 310 mm x 266 mm outline, and one Excellon drill file.",
    "Confirm top/bottom copper, soldermask, silkscreen, and edge-cuts all render with the same orientation as `fab/gerbers/review/tracespace/`.",
    "Select 1.6 mm FR-4 unless deliberately changed after DFM review.",
    "Select standard soldermask/silkscreen colors that keep the dense silkscreen readable.",
    "Do not request impedance control or stackup changes; this is the intentional 2-layer authenticity build.",
    "Review the 599 accepted courtyard/PTH/silk/text findings against the vendor preview before payment.",
    "Save vendor preview screenshots, quoted options, order number, and final ZIP checksum with the order record.",
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
    with path.open("rb") as fp:
        for chunk in iter(lambda: fp.read(65536), b""):
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


def make_zip(fab_dir, files):
    upload_dir = fab_dir / "upload"
    upload_dir.mkdir(parents=True, exist_ok=True)
    zip_path = upload_dir / "juku-replica-gerbers-drill.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for _label, name in files:
            archive.write(fab_dir / name, arcname=name)
    return zip_path


def build_report(fab_dir, report_path):
    failures = []
    hashes = read_hashes(fab_dir / "SHA256SUMS")

    upload_rows = []
    for label, name in UPLOAD_FILES:
        path = fab_dir / name
        if not path.exists() or path.stat().st_size == 0:
            failures.append(f"missing or empty upload file: {name}")
            upload_rows.append([label, f"`{name}`", 0, "-", "FAIL"])
            continue
        digest = sha256(path)
        expected = hashes.get(name)
        if expected and expected != digest:
            failures.append(f"checksum mismatch for {name}: SHA256SUMS has {expected}, computed {digest}")
        upload_rows.append([
            label,
            f"`{name}`",
            path.stat().st_size,
            f"`{digest}`",
            "PASS" if not expected or expected == digest else "FAIL",
        ])

    evidence_rows = []
    for label, name, marker in RETAINED_EVIDENCE:
        path = ROOT / name if "/" in name else fab_dir / name
        if not path.exists() or path.stat().st_size == 0:
            failures.append(f"missing or empty evidence file: {name}")
            evidence_rows.append([label, f"`{repo_relative(path)}`", 0, "FAIL"])
            continue
        text = path.read_text(errors="replace")
        if marker and marker not in text:
            failures.append(f"{name} does not contain expected marker `{marker}`")
        evidence_rows.append([
            label,
            f"`{repo_relative(path)}`",
            path.stat().st_size,
            "PASS" if not marker or marker in text else "FAIL",
        ])

    zip_path = None
    if not failures:
        zip_path = make_zip(fab_dir, UPLOAD_FILES)
    else:
        zip_path = fab_dir / "upload" / "juku-replica-gerbers-drill.zip"

    zip_status = "FAIL"
    zip_size = zip_path.stat().st_size if zip_path.exists() else 0
    zip_digest = sha256(zip_path) if zip_path.exists() and zip_size else "-"
    if zip_path.exists() and zip_size > 0:
        with zipfile.ZipFile(zip_path) as archive:
            names = sorted(archive.namelist())
        expected_names = sorted(name for _label, name in UPLOAD_FILES)
        if names == expected_names:
            zip_status = "PASS"
        else:
            failures.append("upload ZIP contents differ from expected Gerber/drill file set")
    else:
        failures.append("upload ZIP was not created")

    status = "READY" if not failures else "NOT READY"
    lines = [
        "# Replica order-upload runbook",
        "",
        f"Fabrication package: `{repo_relative(fab_dir)}`",
        f"Upload archive: `{repo_relative(zip_path)}`",
        f"Status: **{status}**",
        "",
        "This is the exact upload/runbook layer for the main replica board PCB order.",
        "It does not claim live vendor DFM acceptance; those checks happen in the",
        "vendor UI immediately before payment.",
        "",
        "## Pre-Upload Integrity",
        "",
        "Run from the repository root:",
        "",
        "```sh",
        "python3 kicad/report_order_readiness.py",
        "(cd fab/gerbers && sha256sum -c SHA256SUMS)",
        "```",
        "",
        "## Files In Upload ZIP",
        "",
        "| Purpose | File | Bytes | SHA256 | Status |",
        "| --- | --- | ---: | --- | --- |",
    ]
    lines.extend(table_row(row) for row in upload_rows)

    lines.extend([
        "",
        "## Upload Archive",
        "",
        "| File | Bytes | SHA256 | Contents |",
        "| --- | ---: | --- | --- |",
        table_row([f"`{repo_relative(zip_path)}`", zip_size, f"`{zip_digest}`" if zip_digest != "-" else "-", zip_status]),
        "",
        "## Retained Evidence",
        "",
        "| Purpose | File | Bytes | Status |",
        "| --- | --- | ---: | --- |",
    ])
    lines.extend(table_row(row) for row in evidence_rows)

    lines.extend(["", "## Order-Time Checks", ""])
    lines.extend(f"- [ ] {check}" for check in ORDER_CHECKS)

    lines.extend([
        "",
        "## Do Not Upload",
        "",
        "- `docs/replica-dual-config-bom.csv` is a sourcing/provenance BOM, not an assembly file.",
        "- `docs/replica-sourcing-readiness.md` is for procurement and acceptance planning, not vendor upload.",
        "- Review PNG/SVG outputs are retained as evidence only.",
    ])

    if failures:
        lines.extend(["", "## Failures", ""])
        lines.extend(f"- {failure}" for failure in failures)

    lines.append("")
    return "\n".join(lines), not failures


def main():
    fab_dir = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT_FAB_DIR
    report_path = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else DEFAULT_REPORT
    report, ok = build_report(fab_dir, report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report)
    print(report)
    print(f"Wrote {repo_relative(report_path)}")
    return 0 if ok else 3


if __name__ == "__main__":
    raise SystemExit(main())
