#!/usr/bin/env python3
import csv
import re
import sys
from collections import defaultdict
from pathlib import Path


DESIGNATOR_RE = re.compile(r"^([A-Z]+)([0-9]+)$")
JLCPCB_REFERENCES = [
    (
        "JLCPCB parts library",
        "https://jlcpcb.com/parts",
        "live inventory, pricing, quotation, and part matching are order-time checks",
    ),
    (
        "JLCPCB BOM/CPL preparation",
        "https://jlcpcb.com/help/article/advice-for-bom-and-cpl-files-preparation",
        "upload BOM and CPL must be reviewed in the order UI before payment",
    ),
    (
        "JLCPCB assembly FAQ",
        "https://jlcpcb.com/help/article/pcb-assembly-faqs",
        "assembly method, review feedback, and through-hole handling are vendor decisions",
    ),
    (
        "JLCPCB own/pre-ordered parts",
        "https://jlcpcb.com/help/article/how-to-use-my-own-parts-for-pcb-assembly-order",
        "private/pre-ordered inventory must be selected explicitly if used",
    ),
]


def natural_key(ref):
    match = DESIGNATOR_RE.match(ref)
    if not match:
        return (ref, 0)
    prefix, number = match.groups()
    return (prefix, int(number))


def expand_designators(field):
    refs = []
    for token in field.replace(";", ",").replace(" ", ",").split(","):
        token = token.strip().upper()
        if not token:
            continue
        if "-" not in token:
            refs.append(token)
            continue
        start, end = [part.strip() for part in token.split("-", 1)]
        start_match = DESIGNATOR_RE.match(start)
        end_match = DESIGNATOR_RE.match(end)
        if not start_match or not end_match:
            refs.append(token)
            continue
        start_prefix, start_number = start_match.groups()
        end_prefix, end_number = end_match.groups()
        if start_prefix != end_prefix:
            refs.append(token)
            continue
        for number in range(int(start_number), int(end_number) + 1):
            refs.append(f"{start_prefix}{number}")
    return refs


def read_csv(path):
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def cell(row, name):
    return (row.get(name) or "").strip()


def table_row(values):
    return "| " + " | ".join(str(value).replace("|", "/") if value else "-" for value in values) + " |"


def load_factory_rows(path):
    refs = {}
    for row in read_csv(path):
        cpn = cell(row, "LCSC Part #")
        for ref in expand_designators(cell(row, "Designator")):
            refs[ref] = {
                "cpn": cpn,
                "comment": cell(row, "Comment"),
                "footprint": cell(row, "Footprint"),
                "assembly": cell(row, "Assembly"),
                "sourcing": cell(row, "Sourcing"),
                "notes": cell(row, "Notes"),
            }
    return refs


def load_checklist(path):
    rows = read_csv(path)
    by_ref = {}
    for row in rows:
        preferred = [part.strip() for part in cell(row, "Preferred CPN").split() if part.strip()]
        refs = expand_designators(cell(row, "Designators"))
        for ref in refs:
            by_ref[ref] = {
                "group": cell(row, "Group"),
                "factory_action": cell(row, "Factory action"),
                "preferred": preferred,
                "status": cell(row, "Status"),
                "notes": cell(row, "Notes"),
            }
    return rows, by_ref


def row_requires_review(row):
    text = " ".join(
        [
            row.get("factory_action", ""),
            row.get("group", ""),
            row.get("status", ""),
            row.get("notes", ""),
        ]
    ).lower()
    review_markers = [
        "verify",
        "fixture",
        "socket",
        "wave-solder",
        "wave solder",
        "order-time",
        "vendor drawing",
        "stock",
    ]
    return any(marker in text for marker in review_markers)


def build_report(out_dir, checklist_path):
    upload_bom = out_dir / "upload" / "vjuga-rev-a-jlcpcb-bom.csv"
    upload_manual = out_dir / "upload" / "vjuga-rev-a-manual-assembly.csv"
    upload_post = out_dir / "upload" / "vjuga-rev-a-post-assembly-insertion.csv"
    assembly_notes = out_dir / "upload" / "vjuga-rev-a-assembly-notes.md"

    factory_rows = load_factory_rows(upload_bom)
    _, checklist_by_ref = load_checklist(checklist_path)
    manual_refs = {cell(row, "Designator") for row in read_csv(upload_manual)}
    post_refs = {cell(row, "Designator") for row in read_csv(upload_post)}
    notes_text = assembly_notes.read_text(errors="replace") if assembly_notes.exists() else ""

    failures = []
    reviews = []
    by_cpn = defaultdict(list)
    detail_rows = []

    for ref, row in sorted(factory_rows.items(), key=lambda item: natural_key(item[0])):
        cpn = row["cpn"]
        by_cpn[cpn].append(ref)
        checklist = checklist_by_ref.get(ref)
        row_failures = []
        row_reviews = []
        if not cpn:
            row_failures.append("upload BOM row has no CPN")
        if not checklist:
            row_failures.append("missing from sourcing checklist")
            preferred = []
            group = ""
            status = ""
        else:
            preferred = checklist["preferred"]
            group = checklist["group"]
            status = checklist["status"]
            if cpn not in preferred:
                row_failures.append("upload CPN is not a preferred checklist CPN")
            if row_requires_review(checklist):
                row_reviews.append("order-time vendor/stock/fit review")
        if ref in manual_refs:
            row_failures.append("manual-install row appears in factory upload BOM")
        if ref in post_refs and "socket" not in row["assembly"].lower():
            row_failures.append("post-assembly IC insertion is not represented as factory socket mounting")

        result = "FAIL" if row_failures else "REVIEW" if row_reviews else "PASS"
        if row_failures:
            failures.append(f"{ref}: " + "; ".join(row_failures))
        if row_reviews:
            reviews.append(ref)
        detail_rows.append(
            {
                "Designator": ref,
                "CPN": cpn,
                "Group": group,
                "Assembly": row["assembly"],
                "Checklist status": status,
                "Result": result,
                "Notes": "; ".join(row_failures + row_reviews),
            }
        )

    factory_refs = set(factory_rows)
    factory_checklist_refs = {
        ref for ref, row in checklist_by_ref.items() if not row["factory_action"].lower().startswith("manual install")
    }
    missing_factory_refs = sorted(factory_checklist_refs - factory_refs - manual_refs, key=natural_key)
    for ref in missing_factory_refs:
        failures.append(f"{ref}: sourcing checklist expects factory handling but upload BOM has no row")

    manual_checklist_refs = {
        ref for ref, row in checklist_by_ref.items() if row["factory_action"].lower().startswith("manual install")
    }
    unexpected_manual_refs = sorted(manual_refs - manual_checklist_refs, key=natural_key)
    missing_manual_refs = sorted(manual_checklist_refs - manual_refs, key=natural_key)
    for ref in unexpected_manual_refs:
        failures.append(f"{ref}: upload manual row is not marked manual in sourcing checklist")
    for ref in missing_manual_refs:
        failures.append(f"{ref}: checklist manual row is missing from upload manual CSV")

    if not upload_bom.exists() or upload_bom.stat().st_size == 0:
        failures.append("upload JLCPCB BOM is missing or empty")
    if not assembly_notes.exists() or assembly_notes.stat().st_size == 0:
        failures.append("upload assembly notes are missing or empty")
    for ref in sorted(manual_refs, key=natural_key):
        if ref not in notes_text:
            failures.append(f"{ref}: upload assembly notes do not mention manual handling")
    if post_refs and "Post-Assembly IC Insertion" not in notes_text:
        failures.append("upload assembly notes do not include a post-assembly IC insertion section")
    if post_refs and "socketed ICs" not in notes_text:
        failures.append("upload assembly notes do not explicitly keep socketed ICs out of factory population")

    status = "NOT READY" if failures else "REVIEW REQUIRED" if reviews else "READY"
    lines = [
        "# Rev A vendor/order checklist",
        "",
        f"Package: `{out_dir}`",
        f"Status: **{status}**",
        "",
        "This report makes the JLCPCB/LCSC order-time decisions explicit. It",
        "verifies that every factory-mounted designator in the upload BOM has a",
        "checklist-backed CPN and that manually installed or post-assembly parts",
        "stay out of the factory-populated IC list. It deliberately does not claim",
        "live stock availability; stock, price, alternatives, and assembly-service",
        "acceptance must be checked in the vendor order UI immediately before",
        "payment.",
        "",
        "## Summary",
        "",
        f"- Factory-mounted designators checked: {len(factory_rows)}",
        f"- Unique factory CPNs: {len([cpn for cpn in by_cpn if cpn])}",
        f"- Manual-install rows excluded from factory BOM: {len(manual_refs)}",
        f"- Post-assembly owner insertions: {len(post_refs)}",
        f"- Rows requiring order-time vendor/stock/fit review: {len(set(reviews))}",
        f"- Vendor checklist failures: {len(failures)}",
        "",
        "## Vendor References",
        "",
        "| Reference | URL | Order-time use |",
        "| --- | --- | --- |",
    ]
    for name, url, use in JLCPCB_REFERENCES:
        lines.append(table_row([name, url, use]))

    lines.extend(
        [
            "",
            "## Unique Factory CPNs",
            "",
            "| CPN | Designators |",
            "| --- | --- |",
        ]
    )
    for cpn in sorted(by_cpn):
        refs = ", ".join(sorted(by_cpn[cpn], key=natural_key))
        lines.append(table_row([cpn, refs]))

    lines.extend(
        [
            "",
            "## Factory Rows",
            "",
            "| Designator | CPN | Group | Assembly | Checklist status | Result | Notes |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in detail_rows:
        lines.append(
            table_row(
                [
                    row["Designator"],
                    row["CPN"],
                    row["Group"],
                    row["Assembly"],
                    row["Checklist status"],
                    row["Result"],
                    row["Notes"],
                ]
            )
        )

    lines.extend(["", "## Manual / Post-Assembly Rows", ""])
    lines.append(f"- Manual install rows in upload package: {', '.join(sorted(manual_refs, key=natural_key))}")
    lines.append(f"- Owner-supplied post-assembly insertions: {', '.join(sorted(post_refs, key=natural_key))}")

    if failures:
        lines.extend(["", "## Failures", ""])
        for failure in failures:
            lines.append(f"- {failure}")

    lines.append("")
    return "\n".join(lines), status


def main():
    out_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "fab/minimal-vga")
    checklist = Path(sys.argv[2] if len(sys.argv) > 2 else "spinoffs/minimal-vga/kicad/rev-a-jlcpcb-cpn-checklist.csv")
    report, status = build_report(out_dir, checklist)
    path = out_dir / "assembly" / "vendor-order-checklist.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report)
    print(report)
    print(f"Wrote {path}")
    return 0 if status in {"READY", "REVIEW REQUIRED"} else 3


if __name__ == "__main__":
    raise SystemExit(main())
