#!/usr/bin/env python3
import csv
import re
import sys
from pathlib import Path

import pcbnew


DESIGNATOR_RE = re.compile(r"^([A-Z]+)([0-9]+)$")


def natural_key(ref):
    match = DESIGNATOR_RE.match(ref)
    if not match:
        return (ref, 0)
    prefix, number = match.groups()
    return (prefix, int(number))


def expand_designators(field):
    refs = []
    for token in field.replace(";", ",").split(","):
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


def footprint_name(fp):
    return str(fp.GetFPID().GetLibItemName())


def is_socketed_ic(fp):
    ref = fp.GetReference().upper()
    name = footprint_name(fp)
    return ref.startswith("U") and name.startswith("DIP-") and name.endswith("_Socket")


def refs_from_rows(rows, column="Designator"):
    refs = set()
    for row in rows:
        refs.update(expand_designators(row.get(column, "")))
    return refs


def row_for_ref(rows, ref):
    for row in rows:
        if ref in expand_designators(row.get("Designator", "")):
            return row
    return None


def table_row(values):
    return "| " + " | ".join(str(value).replace("|", "/") if value else "-" for value in values) + " |"


def build_report(board_path, out_dir):
    board = pcbnew.LoadBoard(str(board_path))
    bom_rows = read_csv(out_dir / "assembly" / "jlcpcb-bom-draft.csv")
    cpl_rows = read_csv(out_dir / "assembly" / "jlcpcb-cpl-draft.csv")
    manual_rows = read_csv(out_dir / "assembly" / "manual-assembly.csv")
    post_rows = read_csv(out_dir / "assembly" / "post-assembly-insertion.csv")

    socket_refs = sorted(
        [fp.GetReference().upper() for fp in board.Footprints() if is_socketed_ic(fp)],
        key=natural_key,
    )
    bom_refs = refs_from_rows(bom_rows)
    cpl_refs = refs_from_rows(cpl_rows)
    manual_refs = refs_from_rows(manual_rows)
    post_refs = refs_from_rows(post_rows)

    failures = []
    rows = []
    for ref in socket_refs:
        bom_row = row_for_ref(bom_rows, ref)
        post_row = row_for_ref(post_rows, ref)
        issues = []
        if ref not in bom_refs:
            issues.append("missing from JLCPCB BOM")
        if ref not in cpl_refs:
            issues.append("missing from JLCPCB CPL")
        if ref not in post_refs:
            issues.append("missing from post-assembly list")
        if ref in manual_refs:
            issues.append("also listed as manual/non-factory")
        if bom_row:
            if bom_row.get("Assembly") != "Factory socket":
                issues.append("BOM assembly is not Factory socket")
            if "socket" not in (bom_row.get("Sourcing") or "").lower():
                issues.append("BOM sourcing does not identify socket sourcing")
            if (bom_row.get("MPN") or "").strip():
                issues.append("BOM MPN should stay empty for owner-supplied socketed ICs")
            if "owner inserts" not in (bom_row.get("Notes") or "").lower():
                issues.append("BOM notes do not state owner insertion")
        if post_row:
            if "owner-supplied" not in (post_row.get("Action") or "").lower():
                issues.append("post-assembly action does not state owner-supplied insertion")
            if "socket" not in (post_row.get("Socket") or "").lower():
                issues.append("post-assembly row does not name a socket footprint")

        if issues:
            failures.extend(f"{ref}: {issue}" for issue in issues)
        rows.append([
            ref,
            bom_row.get("Comment", "-") if bom_row else "-",
            bom_row.get("LCSC Part #", "-") if bom_row else "-",
            "yes" if ref in cpl_refs else "no",
            "yes" if ref in post_refs else "no",
            "FAIL" if issues else "PASS",
        ])

    extra_post = sorted(post_refs - set(socket_refs), key=natural_key)
    if extra_post:
        failures.append("post-assembly rows without socketed PCB footprint: " + ", ".join(extra_post))

    status = "READY" if not failures else "NOT READY"
    lines = [
        "# Rev A socket insertion policy",
        "",
        f"Board: `{board_path}`",
        f"Status: **{status}**",
        "",
        "This report verifies the Rev A assembly policy that factory assembly",
        "mounts sockets only for socketed `U*` devices, while owner-supplied ICs",
        "are inserted after factory assembly.",
        "",
        "## Summary",
        "",
        f"- Socketed IC footprints: {len(socket_refs)}",
        f"- Post-assembly insertion rows: {len(post_rows)}",
        f"- Policy failures: {len(failures)}",
        "",
        "## Socketed IC Rows",
        "",
        "| Ref | Factory BOM comment | Socket CPN | CPL placement | Post insertion | Status |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    lines.extend(table_row(row) for row in rows)

    if failures:
        lines.extend(["", "## Failures", ""])
        lines.extend(f"- {failure}" for failure in failures)

    lines.append("")
    return "\n".join(lines), status


def main():
    board_path = Path(sys.argv[1] if len(sys.argv) > 1 else "spinoffs/minimal-vga/kicad/rev-a-physical.kicad_pcb")
    out_dir = Path(sys.argv[2] if len(sys.argv) > 2 else "fab/minimal-vga")
    report, status = build_report(board_path, out_dir)
    report_path = out_dir / "assembly" / "socket-insertion-policy.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report)
    print(report)
    print(f"Wrote {report_path}")
    return 0 if status == "READY" else 3


if __name__ == "__main__":
    raise SystemExit(main())
