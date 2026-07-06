#!/usr/bin/env python3
import csv
import hashlib
import sys
from pathlib import Path


UPLOAD_FILES = [
    ("PCB fabrication archive", "upload/vjuga-rev-a-gerbers-drill.zip"),
    ("Factory assembly BOM", "upload/vjuga-rev-a-jlcpcb-bom.csv"),
    ("Factory assembly CPL", "upload/vjuga-rev-a-jlcpcb-cpl.csv"),
    ("Assembly notes", "upload/vjuga-rev-a-assembly-notes.md"),
    ("Manual-install reference", "upload/vjuga-rev-a-manual-assembly.csv"),
    ("Post-assembly insertion reference", "upload/vjuga-rev-a-post-assembly-insertion.csv"),
    ("Upload README", "upload/README-upload.md"),
    ("Checksum file", "upload/SHA256SUMS.txt"),
]

ORDER_CHECKS = [
    "Verify the Gerber/drill ZIP renders correctly in the JLCPCB preview before payment.",
    "Upload only `vjuga-rev-a-jlcpcb-bom.csv` and `vjuga-rev-a-jlcpcb-cpl.csv` for factory assembly.",
    "Do not upload `rev-a.engineering-bom.csv`; it contains owner/manual insertion rows.",
    "Confirm all 20 unique factory CPNs are accepted by the order UI with current stock and price.",
    "Confirm JLCPCB will mount the through-hole sockets and selected headers in this assembly service.",
    "Keep D1/J30/R6/R15/U50/U51 outside factory assembly for Rev A unless the engineering BOM is deliberately changed.",
    "Confirm the no-plane and 0.20 mm VCC/GND/VCC_RAW routing disposition remains intentional for this low-current prototype.",
    "Save the final vendor BOM/CPL mapping and preview screenshots with the order record.",
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


def build_report(out_dir):
    failures = []
    upload_dir = out_dir / "upload"
    bom = read_csv(upload_dir / "vjuga-rev-a-jlcpcb-bom.csv")
    cpl = read_csv(upload_dir / "vjuga-rev-a-jlcpcb-cpl.csv")
    manual = read_csv(upload_dir / "vjuga-rev-a-manual-assembly.csv")
    post = read_csv(upload_dir / "vjuga-rev-a-post-assembly-insertion.csv")
    hashes = read_hashes(upload_dir / "SHA256SUMS.txt")

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
        "# VJUGA Rev A order-upload runbook",
        "",
        f"Package: `{out_dir}`",
        f"Status: **{status}**",
        "",
        "This is the exact upload/runbook layer for the Rev A JLCPCB order. It",
        "does not claim live stock or final vendor acceptance; those are order-time",
        "checks in the vendor UI immediately before payment.",
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
            "## Counts Expected In Vendor UI",
            "",
            f"- Factory assembly BOM rows: {len(bom)}",
            f"- Factory assembly CPL placements: {len(cpl)}",
            f"- Unique factory CPNs: {len(factory_cpns)}",
            f"- Manual-install rows kept out of factory BOM: {len(manual)}",
            f"- Owner post-assembly socket insertions: {len(post)}",
            "",
            "## Unique Factory CPNs",
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
