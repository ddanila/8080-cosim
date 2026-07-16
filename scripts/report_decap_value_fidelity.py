#!/usr/bin/env python3
"""Generate the C35-C72 decoupling value/authenticity audit."""
from __future__ import annotations

import ast
import hashlib
import json
import math
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOARD_JSON = ROOT / "kicad" / "juku.board.json"
SOURCE_PCB = ROOT / "kicad" / "juku.kicad_pcb"
PCB_GENERATOR = ROOT / "kicad" / "gen_kicad_pcb.py"
PLACEMENT_EVIDENCE = (
    ROOT
    / "ref"
    / "photos"
    / "dgsh5-109-009-sb"
    / "dram-decap-placement-registration.json"
)
REPORT = ROOT / "docs" / "decap-value-fidelity.md"

CAP_REFS = [f"C{i}" for i in range(35, 73)]
REGISTERED_DRAM_REFS = {
    "C38": "D91",
    "C42": "D89",
    "C46": "D87",
    "C50": "D85",
}
MAX_POSITION_ERROR_MM = 0.01


def table_row(values: list[object]) -> str:
    return "| " + " | ".join(str(value).replace("|", "/") for value in values) + " |"


def load_board() -> dict:
    return json.loads(BOARD_JSON.read_text(encoding="utf-8"))


def cap_nets(board: dict) -> dict[str, dict[str, str]]:
    nets: dict[str, dict[str, str]] = {ref: {} for ref in CAP_REFS}
    for net_name, net in board["nets"].items():
        for ref, pin in net.get("nodes", []):
            if ref in nets:
                nets[ref][str(pin)] = net_name
    return nets


def cap_chip(board: dict, ref: str) -> dict:
    for chip in board["chips"]:
        if chip.get("ref") == ref:
            return chip
    raise KeyError(ref)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def generator_decap_positions() -> dict[str, tuple[float, float, float]]:
    tree = ast.parse(PCB_GENERATOR.read_text(encoding="utf-8"))
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if any(isinstance(target, ast.Name) and target.id == "_DEC" for target in node.targets):
            value = ast.literal_eval(node.value)
            return {
                str(ref): tuple(float(coord) for coord in position)
                for ref, position in value.items()
            }
    raise SystemExit("decap audit: generator _DEC table is missing")


def pcb_footprint_pad_midpoint(ref: str) -> tuple[float, float]:
    text = SOURCE_PCB.read_text(encoding="utf-8")
    marker = f'(property "Reference" "{ref}"'
    ref_at = text.find(marker)
    if ref_at < 0:
        raise SystemExit(f"decap audit: source PCB is missing {ref}")
    start = text.rfind("\n\t(footprint ", 0, ref_at)
    end = text.find("\n\t(footprint ", ref_at)
    block = text[start : len(text) if end < 0 else end]
    if not block.lstrip().startswith('(footprint "C_Disc_D4.7mm_W2.5mm_P5.00mm"'):
        raise SystemExit(f"decap audit: {ref} no longer uses the guarded 5.00 mm footprint")
    match = re.search(
        r"\n\t\t\(at\s+(-?[0-9.]+)\s+(-?[0-9.]+)(?:\s+(-?[0-9.]+))?\)",
        block,
    )
    if match is None:
        raise SystemExit(f"decap audit: cannot parse {ref} source-PCB position")
    x, y = float(match.group(1)), float(match.group(2))
    angle = math.radians(float(match.group(3) or 0.0))
    # The guarded radial footprint has a 5.00 mm pitch and its anchor is pad 1.
    # Therefore its physical pad midpoint is 2.50 mm along the footprint axis.
    return x + 2.5 * math.cos(angle), y + 2.5 * math.sin(angle)


def valid_bbox(bbox: object, dimensions: object) -> bool:
    if not isinstance(bbox, list) or len(bbox) != 4:
        return False
    if not isinstance(dimensions, list) or len(dimensions) != 2:
        return False
    x1, y1, x2, y2 = (float(value) for value in bbox)
    width, height = (float(value) for value in dimensions)
    return 0 <= x1 < x2 <= width and 0 <= y1 < y2 <= height


def validate_registered_dram_placements(board: dict) -> tuple[bool, list[str]]:
    evidence = json.loads(PLACEMENT_EVIDENCE.read_text(encoding="utf-8"))
    drawing = evidence.get("factory_drawing", {})
    owner = evidence.get("owner_board", {})
    diagnostics: list[str] = []

    for source in (drawing, owner):
        path = ROOT / str(source.get("source", ""))
        if not path.is_file() or sha256(path) != source.get("sha256"):
            diagnostics.append(f"source/hash mismatch: {source.get('source', '-')}")

    drawing_targets = {
        str(item.get("refdes")): item for item in drawing.get("targets", [])
    }
    owner_sites = {
        str(item.get("refdes")): item for item in owner.get("sites", [])
    }
    generated = generator_decap_positions()
    for ref, above_ref in REGISTERED_DRAM_REFS.items():
        target = drawing_targets.get(ref, {})
        site = owner_sites.get(ref, {})
        if target.get("above_ref") != above_ref or site.get("above_ref") != above_ref:
            diagnostics.append(f"{ref}: factory/owner DRAM anchor is not {above_ref}")
            continue
        if not valid_bbox(target.get("label_bbox_px"), drawing.get("dimensions_px")):
            diagnostics.append(f"{ref}: invalid factory-drawing label box")
        if not valid_bbox(site.get("site_bbox_px"), owner.get("dimensions_px")):
            diagnostics.append(f"{ref}: invalid owner-board site box")
        if "removed" not in str(site.get("population_state", "")):
            diagnostics.append(f"{ref}: owner removal state is not explicit")

        expected = tuple(float(value) for value in target.get("board_pad_midpoint_mm", []))
        generated_position = generated.get(ref)
        if len(expected) != 2 or generated_position is None:
            diagnostics.append(f"{ref}: expected/generator placement is missing")
            continue
        if math.dist(expected, generated_position[:2]) > MAX_POSITION_ERROR_MM:
            diagnostics.append(f"{ref}: generator midpoint differs from registered placement")
        if math.dist(expected, pcb_footprint_pad_midpoint(ref)) > MAX_POSITION_ERROR_MM:
            diagnostics.append(f"{ref}: source-PCB midpoint differs from registered placement")

        note = str(cap_chip(board, ref).get("prov", {}).get("pins", ""))
        if f"directly places {ref} above {above_ref}" not in note:
            diagnostics.append(f"{ref}: board provenance lost factory placement")
        if "exact factory capacitance is pending" not in note:
            diagnostics.append(f"{ref}: board provenance overstates value closure")

    if set(drawing_targets) != set(REGISTERED_DRAM_REFS):
        diagnostics.append("factory target set is not exactly C38/C42/C46/C50")
    if set(owner_sites) != set(REGISTERED_DRAM_REFS):
        diagnostics.append("owner site set is not exactly C38/C42/C46/C50")
    if "populate all four" not in str(evidence.get("population_disposition", "")):
        diagnostics.append("factory-replica population disposition is missing")
    return not diagnostics, diagnostics


def main() -> int:
    board = load_board()
    nets = cap_nets(board)

    rows = []
    group_counts: dict[str, int] = {}
    model_values: dict[str, int] = {}
    for ref in CAP_REFS:
        chip = cap_chip(board, ref)
        value = str(chip.get("value", ""))
        p1 = nets.get(ref, {}).get("1", "-")
        p2 = nets.get(ref, {}).get("2", "-")
        group = f"{p1}<->{p2}"
        group_counts[group] = group_counts.get(group, 0) + 1
        model_values[value] = model_values.get(value, 0) + 1
        note = str(chip.get("prov", {}).get("pins", ""))
        rows.append((ref, value, p1, p2, note))

    expected_groups = {
        "RAIL_G<->GND": 19,
        "GND<->RAIL_H": 19,
    }
    group_ok = group_counts == expected_groups
    value_ok = model_values == {"0,047": 38}
    c63_dnp = cap_chip(board, "C63").get("pcb_dnp") is True
    dram_placement_ok, dram_placement_diagnostics = validate_registered_dram_placements(board)

    lines = [
        "# Decoupling capacitor value fidelity",
        "",
        "Status date: 2026-07-16.",
        "",
        "Status: **FOUR TARGET DRAM PLACEMENTS CLOSED / C63 TARGET DNP CLOSED / VALUES AND 33 PLACEMENTS PENDING**",
        "",
        "This generated report isolates the C35-C72 decoupling-capacitor",
        "authenticity issue. The board model and routed PCB preserve the two",
        "array-power bypass rail groups as schematic intent. The `.009` factory",
        "drawing and owner-board remnants now close placement and original population",
        "intent for C38/C42/C46/C50; C63 is a target DNP. The other 33 placements",
        "and all exact factory per-position capacitance values remain unproven.",
        "",
        "## Checks",
        "",
        "| Check | Result | Evidence |",
        "| --- | --- | --- |",
        table_row(["All C35-C72 refs exist in board JSON", "PASS", f"{len(rows)}/38 rows"]),
        table_row(["Rail-group connectivity matches model expectation", "PASS" if group_ok else "FAIL", ", ".join(f"{k}: {v}" for k, v in sorted(group_counts.items()))]),
        table_row(["Current model value is uniform 0,047", "PASS" if value_ok else "FAIL", ", ".join(f"{k or '-'}: {v}" for k, v in sorted(model_values.items()))]),
        table_row(["Target DRAM-bank C38/C42/C46/C50 placements are registered", "PASS" if dram_placement_ok else "FAIL", "factory drawing + owner landing/remnant sites + generator/source PCB" if dram_placement_ok else "; ".join(dram_placement_diagnostics)]),
        table_row(["C63 target-board population is DNP", "PASS" if c63_dnp else "FAIL", "registered bare site between D41/D40; no source-PCB footprint"]),
        table_row(["Historical value census is reconciled per position", "FAIL", "raw notes report mixed values but no per-position mapping"]),
        "",
        "## Current Board Model",
        "",
        "| Ref | Model value | Pin 1 net | Pin 2 net | Provenance note |",
        "| --- | --- | --- | --- | --- |",
    ]
    lines.extend(table_row(list(row)) for row in rows)

    lines.extend(
        [
            "",
            "## Evidence Reconciliation",
            "",
            "- The native sheet-2 ground symbol directly identifies rail E as GND.",
            "  Board JSON and both PCBs therefore place C35-C53 between `RAIL_G`",
            "  and `GND`, and C54-C72 between `GND` and `RAIL_H`.",
            "- C34 is separately source-closed across rail E/GND and rail F/+5 V;",
            "  the former `RAIL_H`-to-GND assignment was a scan-reading error.",
            "- The current BOM/model value for these 38 positions is uniform",
            "  `0,047`, which is suitable for the functional replica's modeled",
            "  bypass role. C63 remains one of those intended schematic positions",
            "  but is not populated or fabricated on the exact target board.",
            "- The `.009` drawing directly labels C38, C42, C46, and C50 above",
            "  D91, D89, D87, and D85 respectively. The owner component photo",
            "  shows a matching landing pair with solder and clipped lead remnants",
            "  at each site but no body. Those four parts are therefore populated",
            "  in the factory replica; the photographed board records later removal.",
            "- The retained factory and owner-photo evidence includes aggregate",
            "  mixed-value capacitor counts, but no defensible mapping from those",
            "  counts to individual C35-C72 positions.",
            "- The remaining 33 C35-C72 placement/population associations still",
            "  require target-revision drawing registration. The older `.006`",
            "  zigzag is not sufficient proof for the `.009` target revision.",
            "",
            "## Boundary",
            "",
            "- Do not silently promote the old mixed-value census into C35-C72",
            "  values; it is a board-authenticity lead, not a per-refdes map.",
            "- Do not treat the uniform `0,047` model as Tier-3 factory value",
            "  proof. It is a functional and currently routed BOM/model value.",
            "- The next data-unlocking action is a macro-photo/value read or a",
            "  matching specification page that maps values to individual",
            "  C35-C72 refdes positions.",
            "",
        ]
    )
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    return 0 if group_ok and value_ok and c63_dnp and dram_placement_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
