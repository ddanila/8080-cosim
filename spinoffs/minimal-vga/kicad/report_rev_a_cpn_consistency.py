#!/usr/bin/env python3
import csv
import re
import sys
from pathlib import Path


DESIGNATOR_RE = re.compile(r"^([A-Z]+)([0-9]+)$")


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
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_engineering_cpns(path):
    by_ref = {}
    for row in read_csv(path):
        cpn = (row.get("JLCPCB/LCSC CPN") or "").strip()
        for ref in expand_designators(row.get("Designator", "")):
            by_ref[ref] = cpn
    return by_ref


def load_jlcpcb_bom_cpns(path):
    by_ref = {}
    for row in read_csv(path):
        cpn = (row.get("LCSC Part #") or "").strip()
        for ref in expand_designators(row.get("Designator", "")):
            by_ref[ref] = {
                "cpn": cpn,
                "comment": row.get("Comment", ""),
                "footprint": row.get("Footprint", ""),
            }
    return by_ref


def load_checklist_cpns(path):
    by_ref = {}
    for row in read_csv(path):
        preferred = [part.strip() for part in (row.get("Preferred CPN") or "").split() if part.strip()]
        status = row.get("Status", "")
        factory_action = row.get("Factory action", "")
        group = row.get("Group", "")
        for ref in expand_designators(row.get("Designators", "")):
            by_ref[ref] = {
                "preferred": preferred,
                "status": status,
                "factory_action": factory_action,
                "group": group,
            }
    return by_ref


def table_row(values):
    return "| " + " | ".join(str(value).replace("|", "/") if value else "-" for value in values) + " |"


def build_report(out_dir, engineering_bom, checklist):
    generated = load_jlcpcb_bom_cpns(out_dir / "assembly" / "jlcpcb-bom-draft.csv")
    engineering = load_engineering_cpns(engineering_bom)
    checklist_cpns = load_checklist_cpns(checklist)

    rows = []
    failures = []
    reviews = []
    for ref in sorted(generated, key=natural_key):
        generated_row = generated[ref]
        generated_cpn = generated_row["cpn"]
        engineering_cpn = engineering.get(ref, "")
        checklist_row = checklist_cpns.get(ref)
        checklist_preferred = checklist_row["preferred"] if checklist_row else []
        checklist_group = checklist_row["group"] if checklist_row else ""

        row_failures = []
        row_reviews = []
        if not generated_cpn:
            row_failures.append("generated JLCPCB BOM has no CPN")
        if engineering_cpn != generated_cpn:
            row_failures.append(f"engineering BOM CPN is {engineering_cpn or '<blank>'}")
        if checklist_row is None:
            row_failures.append("missing from CPN checklist")
        elif generated_cpn not in checklist_preferred:
            row_failures.append(
                "generated CPN is not in checklist preferred CPN set "
                + "(" + (", ".join(checklist_preferred) or "<blank>") + ")"
            )
        if checklist_row and "verify" in checklist_row["status"].lower():
            row_reviews.append("order-time verification")
        if checklist_row and "fixture" in (checklist_row["factory_action"] + " " + checklist_group).lower():
            row_reviews.append("fixture/process review")

        if row_failures:
            status = "FAIL"
            failures.append(ref)
        elif row_reviews:
            status = "REVIEW"
            reviews.append(ref)
        else:
            status = "PASS"

        rows.append(
            {
                "Designator": ref,
                "Generated CPN": generated_cpn,
                "Engineering CPN": engineering_cpn,
                "Checklist CPNs": ", ".join(checklist_preferred),
                "Checklist group": checklist_group,
                "Status": status,
                "Notes": "; ".join(row_failures + row_reviews),
            }
        )

    status = "NOT READY" if failures else "REVIEW REQUIRED" if reviews else "READY"
    lines = [
        "# Rev A CPN consistency",
        "",
        f"Status: **{status}**",
        "",
        "This report cross-checks factory-mounted designators across the generated",
        "JLCPCB BOM, the engineering BOM, and the sourcing checklist. It does not",
        "prove stock availability; it prevents local CPN assignments from drifting",
        "between files before the order-time stock/footprint review.",
        "",
        "## Summary",
        "",
        f"- Factory-mounted designators checked: {len(rows)}",
        f"- CPN consistency failures: {len(failures)}",
        f"- Rows still requiring order-time review: {len(reviews)}",
        "",
        "## Rows",
        "",
        "| Designator | Generated CPN | Engineering CPN | Checklist CPNs | Checklist group | Status | Notes |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            table_row(
                [
                    row["Designator"],
                    row["Generated CPN"],
                    row["Engineering CPN"],
                    row["Checklist CPNs"],
                    row["Checklist group"],
                    row["Status"],
                    row["Notes"],
                ]
            )
        )

    if failures:
        lines.extend(["", "## Failures", ""])
        for ref in sorted(failures, key=natural_key):
            lines.append(f"- `{ref}`")

    if reviews:
        lines.extend(["", "## Review Rows", ""])
        for ref in sorted(reviews, key=natural_key):
            lines.append(f"- `{ref}`")

    lines.append("")
    return "\n".join(lines), status


def main():
    out_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "fab/minimal-vga")
    engineering_bom = Path(sys.argv[2] if len(sys.argv) > 2 else "spinoffs/minimal-vga/kicad/rev-a.bom.csv")
    checklist = Path(sys.argv[3] if len(sys.argv) > 3 else "spinoffs/minimal-vga/kicad/rev-a-jlcpcb-cpn-checklist.csv")
    report, status = build_report(out_dir, engineering_bom, checklist)
    path = out_dir / "assembly" / "cpn-consistency.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report)
    print(report)
    print(f"Wrote {path}")
    return 0 if status in {"READY", "REVIEW REQUIRED"} else 3


if __name__ == "__main__":
    raise SystemExit(main())
