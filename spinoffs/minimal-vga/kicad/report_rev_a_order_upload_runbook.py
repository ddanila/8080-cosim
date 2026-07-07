#!/usr/bin/env python3
import csv
import hashlib
import sys
import zipfile
from pathlib import Path


UPLOAD_FILES = [
    ("PCB fabrication archive", "upload/vjuga-rev-a-gerbers-drill.zip"),
    ("Reference factory assembly BOM - do not upload for bare PCB", "upload/vjuga-rev-a-jlcpcb-bom.csv"),
    ("Reference factory assembly CPL - do not upload for bare PCB", "upload/vjuga-rev-a-jlcpcb-cpl.csv"),
    ("Reference assembly notes", "upload/vjuga-rev-a-assembly-notes.md"),
    ("Reference manual-install list", "upload/vjuga-rev-a-manual-assembly.csv"),
    ("Reference post-assembly insertion list", "upload/vjuga-rev-a-post-assembly-insertion.csv"),
    ("Upload README", "upload/README-upload.md"),
    ("Checksum file", "upload/SHA256SUMS.txt"),
]

EXPECTED_ZIP_MEMBERS = [
    "rev-a-physical-F_Cu.gtl",
    "rev-a-physical-In1_Cu.g1",
    "rev-a-physical-In2_Cu.g2",
    "rev-a-physical-B_Cu.gbl",
    "rev-a-physical-F_Mask.gts",
    "rev-a-physical-B_Mask.gbs",
    "rev-a-physical-F_Silkscreen.gto",
    "rev-a-physical-B_Silkscreen.gbo",
    "rev-a-physical-Edge_Cuts.gm1",
    "rev-a-physical-job.gbrjob",
    "rev-a-physical.drl",
]

FIXED_ZIP_DATE = (1980, 1, 1, 0, 0, 0)

ORDER_CHECKS = [
    "Verify the Gerber/drill ZIP renders correctly in the JLCPCB preview before payment.",
    "Select PCB fabrication only / no assembly for the first concept sample.",
    "Upload only `vjuga-rev-a-gerbers-drill.zip` for the bare-PCB order.",
    "Do not upload `vjuga-rev-a-jlcpcb-bom.csv` or `vjuga-rev-a-jlcpcb-cpl.csv` unless deliberately switching to the optional assembled-board path.",
    "Do not upload `rev-a.engineering-bom.csv`; it contains owner/manual insertion rows.",
    "Confirm the no-plane and 0.20 mm VCC/GND/VCC_RAW routing disposition remains intentional for this low-current prototype.",
    "Save the final vendor Gerber preview screenshots, stackup/settings, price, and order number with the order record.",
]


def read_csv(path):
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_hashes(path):
    hashes = {}
    if not path.exists():
        return hashes
    for line in path.read_text(errors="replace").splitlines():
        parts = line.split(None, 1)
        if len(parts) == 2:
            hashes[parts[1].strip()] = parts[0]
    return hashes


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require(path, failures, label):
    if not path.exists() or path.stat().st_size == 0:
        failures.append(f"{label} missing or empty: {path}")


def table_row(values):
    return "| " + " | ".join(str(value).replace("|", "/") if value else "-" for value in values) + " |"


def bom_cpn(row):
    for key in ["LCSC Part #", "LCSC Part Number", "CPN"]:
        value = row.get(key, "").strip()
        if value:
            return value
    return ""


def zip_member_mode(info):
    return (info.external_attr >> 16) & 0o777


def zip_member_metadata_ok(info):
    return (
        info.date_time == FIXED_ZIP_DATE
        and not info.filename.startswith("/")
        and ".." not in Path(info.filename).parts
        and info.compress_type == zipfile.ZIP_DEFLATED
        and zip_member_mode(info) == 0o644
    )


def build_report(out_dir):
    failures = []
    upload_dir = out_dir / "upload"
    bom = read_csv(upload_dir / "vjuga-rev-a-jlcpcb-bom.csv")
    cpl = read_csv(upload_dir / "vjuga-rev-a-jlcpcb-cpl.csv")
    manual = read_csv(upload_dir / "vjuga-rev-a-manual-assembly.csv")
    post = read_csv(upload_dir / "vjuga-rev-a-post-assembly-insertion.csv")
    hashes = read_hashes(upload_dir / "SHA256SUMS.txt")
    zip_path = out_dir / "upload/vjuga-rev-a-gerbers-drill.zip"

    for label, rel in UPLOAD_FILES:
        require(out_dir / rel, failures, label)
    if len(bom) != 26:
        failures.append(f"expected 26 factory BOM rows, got {len(bom)}")
    if len(cpl) != 89:
        failures.append(f"expected 89 factory CPL placements, got {len(cpl)}")
    if len(manual) != 6:
        failures.append(f"expected 6 manual-install rows, got {len(manual)}")
    if len(post) != 19:
        failures.append(f"expected 19 post-assembly insertions, got {len(post)}")

    factory_cpns = sorted({bom_cpn(row) for row in bom if bom_cpn(row)})
    if len(factory_cpns) != 20:
        failures.append(f"expected 20 unique factory CPNs, got {len(factory_cpns)}")

    zip_rows = []
    if zip_path.exists() and zip_path.stat().st_size > 0:
        try:
            with zipfile.ZipFile(zip_path) as archive:
                infos = archive.infolist()
                zip_names = [info.filename for info in infos]
                if zip_names != EXPECTED_ZIP_MEMBERS:
                    failures.append("Gerber/drill ZIP member order/content mismatch: " + ", ".join(zip_names))
                for info in infos:
                    metadata_ok = zip_member_metadata_ok(info)
                    zip_rows.append(
                        [
                            info.filename,
                            info.file_size,
                            "PASS" if metadata_ok else "FAIL",
                        ]
                    )
                    if not metadata_ok:
                        failures.append(f"Gerber/drill ZIP member has non-reproducible metadata: {info.filename}")
        except zipfile.BadZipFile:
            failures.append("Gerber/drill ZIP is not a valid ZIP file")
    else:
        failures.append("Gerber/drill ZIP missing or empty")

    upload_rows = []
    for label, rel in UPLOAD_FILES:
        path = out_dir / rel
        size = path.stat().st_size if path.exists() else 0
        recorded = hashes.get(rel, "")
        computed = sha256(path) if path.exists() and size else ""
        if rel == "upload/SHA256SUMS.txt":
            status_cell = "SELF"
        elif not recorded:
            failures.append(f"missing SHA256SUMS entry for {rel}")
            status_cell = "FAIL"
        elif recorded != computed:
            failures.append(f"SHA256SUMS entry for {rel} is stale: recorded {recorded}, computed {computed}")
            status_cell = "FAIL"
        else:
            status_cell = "PASS"
        digest_cell = f"`{recorded}`" if recorded else "-"
        upload_rows.append([label, f"`{rel}`", size, digest_cell, status_cell])

    expected_hash_entries = {rel for _label, rel in UPLOAD_FILES if rel != "upload/SHA256SUMS.txt"}
    extra_hash_entries = sorted(set(hashes) - expected_hash_entries)
    if extra_hash_entries:
        failures.append("unexpected SHA256SUMS entries: " + ", ".join(extra_hash_entries))

    status = "READY" if not failures else "NOT READY"
    lines = [
        "# VJUGA Rev A bare-PCB order-upload runbook",
        "",
        f"Package: `{out_dir}`",
        f"Status: **{status}**",
        "",
        "This is the exact upload/runbook layer for the Rev A bare-PCB first",
        "sample. It does not claim live vendor acceptance; preview, stackup,",
        "price, and order-number evidence are order-time checks in the vendor UI",
        "immediately before payment.",
        "",
        "## Pre-Upload Integrity",
        "",
        "Run from the repository root:",
        "",
        "```sh",
        "(cd fab/minimal-vga && sha256sum -c upload/SHA256SUMS.txt)",
        "```",
        "",
        "## Files To Upload / Retain",
        "",
        "| Purpose | File | Bytes | SHA256 | Status |",
        "| --- | --- | ---: | --- | --- |",
    ]
    lines.extend(table_row(row) for row in upload_rows)

    lines.extend(
        [
            "",
            "## Gerber/Drill ZIP Reproducibility",
            "",
            f"- Expected ZIP members: {len(EXPECTED_ZIP_MEMBERS)}",
            f"- ZIP members found: {len(zip_rows)}",
            "- Required metadata: timestamp `1980-01-01 00:00:00`, deflated compression, file mode `0644`",
            "",
            "| Member | Bytes | Metadata |",
            "| --- | ---: | --- |",
        ]
    )
    lines.extend(table_row(row) for row in zip_rows)

    lines.extend(
        [
            "",
            "## Reference Assembly Counts",
            "",
            f"- Reference factory BOM rows retained: {len(bom)}",
            f"- Reference factory CPL placements retained: {len(cpl)}",
            f"- Reference unique factory CPNs retained: {len(factory_cpns)}",
            f"- Manual-install rows retained for later assembly: {len(manual)}",
            f"- Owner post-assembly socket insertions retained for later assembly: {len(post)}",
            "",
            "## Reference Unique Factory CPNs",
            "",
        ]
    )
    lines.extend(f"- `{cpn}`" for cpn in factory_cpns)

    lines.extend(["", "## Order-Time Checks", ""])
    lines.extend(f"- [ ] {check}" for check in ORDER_CHECKS)

    if failures:
        lines.extend(["", "## Failures", ""])
        lines.extend(f"- {failure}" for failure in failures)

    lines.append("")
    return "\n".join(lines), not failures


def main():
    out_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "fab/minimal-vga")
    report, ok = build_report(out_dir)
    path = out_dir / "order-upload-runbook.md"
    path.write_text(report)
    print(report)
    print(f"Wrote {path}")
    return 0 if ok else 3


if __name__ == "__main__":
    raise SystemExit(main())
