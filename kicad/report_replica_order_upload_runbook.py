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
    ("DRC visual disposition", "docs/replica-fab-drc-disposition.md", "Status: **READY**"),
    ("Package geometry", "docs/replica-package-geometry-readiness.md", "Status: **READY**"),
    ("Power trace readiness", "docs/replica-power-trace-readiness.md", "Status: **READY**"),
    ("Bring-up verification points", "docs/replica-bringup-verification-points.md", "# Replica bring-up verification points"),
    ("Sourcing readiness", "docs/replica-sourcing-readiness.md", "# Replica sourcing readiness"),
    ("Factory wire construction", "docs/factory-wire-route-fidelity.md", "# Factory insulated-wire route fidelity"),
    ("Checksum file", "SHA256SUMS", None),
    ("Order evidence template", "docs/replica-order-evidence-template.md", "# Replica order evidence template"),
]

ORDER_CHECKS = [
    "Require the pre-upload command above to exit successfully with `replica manufacturing readiness: RELEASED FOR UPLOAD` and confirm `fab/gerbers/order-readiness.md` says `RELEASED FOR ORDER`; do not upload while either gate is unreleased.",
    "After release, upload only `fab/gerbers/upload/juku-replica-gerbers-drill.zip` for PCB fabrication.",
    "Confirm vendor preview matches `docs/replica-package-geometry-readiness.md`: 2-layer board, 310 mm x 266 mm Edge.Cuts box, and one mixed-plating Excellon drill file.",
    "Confirm top/bottom copper, soldermask, silkscreen, and edge-cuts all render with the same orientation as `fab/gerbers/review/tracespace/`.",
    "Select 1.6 mm FR-4 unless deliberately changed after DFM review.",
    "Select standard soldermask/silkscreen colors that keep the dense silkscreen readable.",
    "Do not request impedance control or stackup changes; this is the intentional 2-layer authenticity build.",
    "Review the current findings and acceptance status in `docs/replica-fab-drc-disposition.md` against the vendor preview before payment.",
    "Review `docs/replica-bringup-verification-points.md` and confirm no listed residual source-risk net blocks PCB fabrication.",
    "Save vendor preview screenshots, quoted options, order number, and final ZIP checksum using `docs/replica-order-evidence-template.md`.",
]
FIXED_ZIP_DATE = (1980, 1, 1, 0, 0, 0)
ZIP_COMPRESSION = zipfile.ZIP_STORED
ZIP_COMPRESSION_LABEL = "stored (uncompressed)"
UPLOAD_ZIP_NAME = "juku-replica-gerbers-drill.zip"
UPLOAD_SHA_NAME = "SHA256SUMS.txt"


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
    zip_path = upload_dir / UPLOAD_ZIP_NAME
    with zipfile.ZipFile(zip_path, "w", compression=ZIP_COMPRESSION) as archive:
        for _label, name in files:
            info = zipfile.ZipInfo(name)
            info.date_time = FIXED_ZIP_DATE
            info.compress_type = ZIP_COMPRESSION
            info.create_system = 3
            info.create_version = 20
            info.extract_version = 10
            info.flag_bits = 0
            info.internal_attr = 0
            info.external_attr = 0o100644 << 16
            archive.writestr(info, (fab_dir / name).read_bytes())
    return zip_path


def write_upload_sha256(zip_path):
    sha_path = zip_path.parent / UPLOAD_SHA_NAME
    sha_path.write_text(f"{sha256(zip_path)}  {UPLOAD_ZIP_NAME}\n")
    return sha_path


def zip_member_mode(info):
    return (info.external_attr >> 16) & 0o777


def zip_member_metadata_ok(info):
    return (
        info.date_time == FIXED_ZIP_DATE
        and not info.filename.startswith("/")
        and ".." not in Path(info.filename).parts
        and info.compress_type == ZIP_COMPRESSION
        and zip_member_mode(info) == 0o644
    )


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
        if not expected:
            failures.append(f"missing SHA256SUMS entry for {name}")
        elif expected != digest:
            failures.append(f"checksum mismatch for {name}: SHA256SUMS has {expected}, computed {digest}")
        upload_rows.append([
            label,
            f"`{name}`",
            path.stat().st_size,
            f"`{digest}`",
            "PASS" if expected == digest else "FAIL",
        ])

    evidence_rows = []
    for label, name, marker in RETAINED_EVIDENCE:
        path = ROOT / name if "/" in name else fab_dir / name
        if not path.exists() or path.stat().st_size == 0:
            failures.append(f"missing or empty evidence file: {name}")
            evidence_rows.append([label, f"`{repo_relative(path)}`", "FAIL"])
            continue
        text = path.read_text(errors="replace")
        if marker and marker not in text:
            failures.append(f"{name} does not contain expected marker `{marker}`")
        evidence_rows.append([
            label,
            f"`{repo_relative(path)}`",
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
    zip_rows = []
    if zip_path.exists() and zip_size > 0:
        try:
            with zipfile.ZipFile(zip_path) as archive:
                infos = archive.infolist()
                names = [info.filename for info in infos]
                expected_names = [name for _label, name in UPLOAD_FILES]
                if names != expected_names:
                    failures.append("upload ZIP member order/content differs from expected Gerber/drill file set")
                for info in infos:
                    source = fab_dir / info.filename
                    metadata_ok = zip_member_metadata_ok(info)
                    content_ok = source.exists() and archive.read(info.filename) == source.read_bytes()
                    zip_rows.append([
                        info.filename,
                        info.file_size,
                        "PASS" if metadata_ok else "FAIL",
                        "PASS" if content_ok else "FAIL",
                    ])
                    if not metadata_ok:
                        failures.append(f"upload ZIP member has non-deterministic or unsafe metadata: {info.filename}")
                    if not content_ok:
                        failures.append(f"upload ZIP member does not match source file: {info.filename}")
            if not failures:
                zip_status = "PASS"
        except zipfile.BadZipFile:
            failures.append("upload ZIP is not a valid ZIP file")
    else:
        failures.append("upload ZIP was not created")

    sha_path = write_upload_sha256(zip_path) if zip_path.exists() and zip_size else zip_path.parent / UPLOAD_SHA_NAME
    upload_hashes = read_hashes(sha_path)
    recorded_zip_hash = upload_hashes.get(UPLOAD_ZIP_NAME, "")
    sha_rows = []
    if not sha_path.exists() or sha_path.stat().st_size == 0:
        failures.append("upload SHA256SUMS.txt was not created")
        sha_rows.append([f"`{repo_relative(sha_path)}`", 0, "-", "FAIL"])
    elif recorded_zip_hash != zip_digest:
        failures.append(
            f"upload SHA256SUMS.txt is stale for {UPLOAD_ZIP_NAME}: recorded {recorded_zip_hash}, computed {zip_digest}"
        )
        sha_rows.append([f"`{repo_relative(sha_path)}`", sha_path.stat().st_size, f"`{recorded_zip_hash or '-'}`", "FAIL"])
    else:
        sha_rows.append([f"`{repo_relative(sha_path)}`", sha_path.stat().st_size, f"`{recorded_zip_hash}`", "PASS"])
    extra_upload_hashes = sorted(set(upload_hashes) - {UPLOAD_ZIP_NAME})
    if extra_upload_hashes:
        failures.append("unexpected upload SHA256SUMS entries: " + ", ".join(extra_upload_hashes))

    status = "PACKAGE VERIFIED / DESIGN RELEASE SEPARATE" if not failures else "PACKAGE INVALID"
    lines = [
        "# Replica order-upload runbook",
        "",
        f"Fabrication package: `{repo_relative(fab_dir)}`",
        f"Upload archive: `{repo_relative(zip_path)}`",
        f"Status: **{status}**",
        "",
        "The [superseded package record](../ref/routing/zero-open-fabrication-package.json)",
        "preserves the historical ZIP identity. Current release requires fresh verification.",
        "",
        "Refresh from the repository root with Python 3 (standard library only):",
        "`python3 kicad/report_replica_order_upload_runbook.py`.",
        "The generator overwrites this report and exits `0` when its package checks",
        "pass or `3` when they fail. Run the separate manufacturing gate below",
        "to check design release.",
        "The generator checks exported files against `fab/gerbers/SHA256SUMS` and",
        "retained-evidence markers. When those checks pass, it rebuilds the upload",
        "ZIP; otherwise it inspects any existing ZIP. It checks ZIP members against",
        "the exported files and required metadata, then rewrites the upload checksum",
        "for any nonempty ZIP. A checksum PASS therefore does not verify a previously",
        "recorded ZIP identity. Preserve the approved hash in the order record.",
        "",
        "This report is not an order authorization. The design-release state is owned by",
        "`fab/gerbers/order-readiness.md` and the top-level command below.",
        "",
        "## Pre-Upload Integrity",
        "",
        "Run from the repository root:",
        "",
        "```sh",
        "kicad/check_replica_manufacturing_ready.sh",
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
        "## Upload ZIP Members",
        "",
        f"- Required metadata: timestamp `1980-01-01 00:00:00`, {ZIP_COMPRESSION_LABEL} members, file mode `0644`",
        "",
        "| Member | Bytes | Metadata | Source match |",
        "| --- | ---: | --- | --- |",
    ])
    lines.extend(table_row(row) for row in zip_rows)

    lines.extend([
        "",
        "## Upload Checksum",
        "",
        "| File | Bytes | SHA256SUMS entry | Status |",
        "| --- | ---: | --- | --- |",
    ])
    lines.extend(table_row(row) for row in sha_rows)

    lines.extend([
        "",
        "## Retained Evidence",
        "",
        "Here `PASS` means a nonempty file contains its configured text marker",
        "(or exists when no marker is configured). Some markers are only titles:",
        "this table does not establish that every report is ready or its contents",
        "were freshly verified. Run the manufacturing gate for release checks.",
        "",
        "| Purpose | File | Status |",
        "| --- | --- | --- |",
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
