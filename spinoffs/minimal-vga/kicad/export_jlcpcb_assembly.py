#!/usr/bin/env python3
import argparse
import csv
import re
from collections import defaultdict
from pathlib import Path

import pcbnew


DESIGNATOR_RE = re.compile(r"^([A-Z]+)([0-9]+)$")
MAX_REFS_PER_BOM_LINE = 200


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


def load_engineering_bom(path):
    by_ref = {}
    with open(path, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if None in row:
                extras = ", ".join(row[None])
                raise SystemExit(
                    f"malformed engineering BOM row for {row.get('Designator', '<unknown>')}: "
                    f"extra CSV fields {extras!r}"
                )
            designators = expand_designators(row["Designator"])
            for ref in designators:
                if ref in by_ref:
                    raise SystemExit(f"duplicate engineering BOM designator: {ref}")
                by_ref[ref] = row
    return by_ref


def footprint_name(fp):
    return str(fp.GetFPID().GetLibItemName())


def is_socket_footprint(fp):
    name = footprint_name(fp)
    return name.startswith("DIP-") and name.endswith("_Socket")


def socket_comment(fp, source):
    value = source.get("Value") or fp.GetValue()
    name = footprint_name(fp)
    match = re.match(r"^(DIP-[0-9]+)_", name)
    socket = match.group(1) if match else name
    return f"{socket} IC socket for {value}"


def assembly_comment(fp, source):
    ref = fp.GetReference().upper()
    if ref.startswith("U") and is_socket_footprint(fp):
        return socket_comment(fp, source)
    return source.get("Value") or fp.GetValue()


def lcsc_part(source):
    cpn = (source.get("JLCPCB/LCSC CPN") or "").strip()
    return "" if cpn.upper() == "TBD" else cpn


def mpn(source):
    candidate = (source.get("Candidate MPN") or "").strip()
    return "" if candidate.upper() == "TBD" else candidate


def assembly_mpn(fp, source):
    ref = fp.GetReference().upper()
    if ref.startswith("U") and is_socket_footprint(fp):
        return ""
    return mpn(source)


def assembly_notes(fp, source):
    ref = fp.GetReference().upper()
    notes = source.get("Notes", "")
    if ref.startswith("U") and is_socket_footprint(fp):
        device = source.get("Value") or fp.GetValue()
        return f"Factory mounts socket only; owner inserts {device} after assembly. {notes}".strip()
    return notes


def assembly_owner(fp, source):
    ref = fp.GetReference().upper()
    if ref.startswith("U") and is_socket_footprint(fp):
        return "Factory socket"
    return source.get("Assembly", "")


def assembly_sourcing(fp, source):
    ref = fp.GetReference().upper()
    if ref.startswith("U") and is_socket_footprint(fp):
        return "JLCPCB/LCSC socket"
    return source.get("Sourcing", "")


def board_footprints(board):
    return sorted(board.Footprints(), key=lambda fp: natural_key(fp.GetReference().upper()))


def build_rows(board, engineering_bom):
    bom_groups = defaultdict(list)
    cpl_rows = []
    post_assembly_rows = []
    missing_engineering_rows = []

    for fp in board_footprints(board):
        ref = fp.GetReference().upper()
        source = engineering_bom.get(ref)
        if source is None:
            missing_engineering_rows.append(ref)
            source = {}

        fp_name = footprint_name(fp)
        comment = assembly_comment(fp, source)
        key = (
            str(comment),
            str(fp_name),
            str(lcsc_part(source)),
            str(assembly_mpn(fp, source)),
            str(assembly_owner(fp, source)),
            str(assembly_sourcing(fp, source)),
            str(assembly_notes(fp, source)),
        )
        bom_groups[key].append(ref)

        pos = fp.GetPosition()
        cpl_rows.append(
            {
                "Designator": ref,
                "Mid X": f"{pcbnew.ToMM(pos.x):.3f}mm",
                "Mid Y": f"{pcbnew.ToMM(pos.y):.3f}mm",
                "Layer": "Top" if fp.GetLayer() == pcbnew.F_Cu else "Bottom",
                "Rotation": f"{fp.GetOrientationDegrees():.3f}",
            }
        )

        if ref.startswith("U") and is_socket_footprint(fp):
            post_assembly_rows.append(
                {
                    "Designator": ref,
                    "Device": source.get("Value") or fp.GetValue(),
                    "Socket": fp_name,
                    "Action": "Insert owner-supplied IC after factory socket assembly",
                    "Notes": source.get("Notes", ""),
                }
            )

    bom_rows = []
    for key, refs in sorted(bom_groups.items(), key=lambda item: natural_key(item[1][0])):
        comment, fp_name, cpn, candidate_mpn, assembly, sourcing, notes = key
        refs = sorted(refs, key=natural_key)
        for start in range(0, len(refs), MAX_REFS_PER_BOM_LINE):
            chunk = refs[start : start + MAX_REFS_PER_BOM_LINE]
            bom_rows.append(
                {
                    "Comment": comment,
                    "Designator": ",".join(chunk),
                    "Footprint": fp_name,
                    "LCSC Part #": cpn,
                    "MPN": candidate_mpn,
                    "Assembly": assembly,
                    "Sourcing": sourcing,
                    "Notes": notes,
                }
            )

    return bom_rows, cpl_rows, post_assembly_rows, missing_engineering_rows


def write_csv(path, fieldnames, rows):
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_readiness(path, bom_rows, cpl_rows, post_assembly_rows):
    missing_lcsc = [row for row in bom_rows if not row["LCSC Part #"]]
    tbd_sourcing = [
        row for row in bom_rows
        if "TBD" in row["Sourcing"].upper() or "TBD" in row["Notes"].upper()
    ]
    status = "NOT READY" if missing_lcsc or tbd_sourcing else "READY"
    lines = [
        "# JLCPCB assembly readiness",
        "",
        f"Status: **{status}**",
        "",
        "## Summary",
        "",
        f"- BOM rows: {len(bom_rows)}",
        f"- CPL placements: {len(cpl_rows)}",
        f"- Post-assembly socket insertions: {len(post_assembly_rows)}",
        f"- BOM rows missing LCSC part numbers: {len(missing_lcsc)}",
        f"- BOM rows with TBD sourcing/notes: {len(tbd_sourcing)}",
        "",
        "## Gate",
        "",
        "The JLCPCB BOM/CPL designators match, but the assembly package is not "
        "ready to upload until factory-mounted rows have orderable LCSC part "
        "numbers and the remaining TBD connector/VGA choices are resolved.",
        "",
    ]
    if missing_lcsc:
        lines.extend(["## Missing LCSC Part Numbers", ""])
        for row in missing_lcsc:
            lines.append(f"- `{row['Designator']}`: {row['Comment']} ({row['Footprint']})")
        lines.append("")
    if tbd_sourcing:
        lines.extend(["## TBD Rows", ""])
        for row in tbd_sourcing:
            lines.append(f"- `{row['Designator']}`: {row['Comment']}")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def validate_designator_match(bom_rows, cpl_rows):
    bom_refs = set()
    duplicate_refs = set()
    for row in bom_rows:
        for ref in expand_designators(row["Designator"]):
            if ref in bom_refs:
                duplicate_refs.add(ref)
            bom_refs.add(ref)
    cpl_refs = {row["Designator"].upper() for row in cpl_rows}
    if duplicate_refs:
        raise SystemExit("duplicate generated BOM designators: " + ", ".join(sorted(duplicate_refs, key=natural_key)))
    missing_from_cpl = sorted(bom_refs - cpl_refs, key=natural_key)
    missing_from_bom = sorted(cpl_refs - bom_refs, key=natural_key)
    if missing_from_cpl or missing_from_bom:
        raise SystemExit(
            "BOM/CPL designator mismatch: "
            f"missing from CPL={missing_from_cpl}; missing from BOM={missing_from_bom}"
        )


def main():
    parser = argparse.ArgumentParser(description="Export draft JLCPCB BOM/CPL files for the minimal VGA Rev A board.")
    parser.add_argument("board", nargs="?", default="spinoffs/minimal-vga/kicad/rev-a-physical.kicad_pcb")
    parser.add_argument("engineering_bom", nargs="?", default="spinoffs/minimal-vga/kicad/rev-a.bom.csv")
    parser.add_argument("out_dir", nargs="?", default="fab/minimal-vga/assembly")
    args = parser.parse_args()

    board = pcbnew.LoadBoard(args.board)
    engineering_bom = load_engineering_bom(args.engineering_bom)
    bom_rows, cpl_rows, post_assembly_rows, missing_engineering_rows = build_rows(board, engineering_bom)
    validate_designator_match(bom_rows, cpl_rows)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(
        out_dir / "jlcpcb-bom-draft.csv",
        ("Comment", "Designator", "Footprint", "LCSC Part #", "MPN", "Assembly", "Sourcing", "Notes"),
        bom_rows,
    )
    write_csv(
        out_dir / "jlcpcb-cpl-draft.csv",
        ("Designator", "Mid X", "Mid Y", "Layer", "Rotation"),
        cpl_rows,
    )
    write_csv(
        out_dir / "post-assembly-insertion.csv",
        ("Designator", "Device", "Socket", "Action", "Notes"),
        post_assembly_rows,
    )
    write_readiness(out_dir / "assembly-readiness.md", bom_rows, cpl_rows, post_assembly_rows)

    if missing_engineering_rows:
        raise SystemExit("footprints missing engineering BOM rows: " + ", ".join(missing_engineering_rows))

    print(
        f"JLCPCB draft assembly export: PASS "
        f"({len(bom_rows)} BOM rows, {len(cpl_rows)} CPL placements, "
        f"{len(post_assembly_rows)} post-assembly insertions)"
    )
    print(f"Wrote {out_dir}")


if __name__ == "__main__":
    main()
