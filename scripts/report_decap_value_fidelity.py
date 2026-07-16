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
SCHEMATIC = ROOT / "kicad" / "juku.kicad_sch"
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
OPTIONAL_GRID_DNP_REFS = {
    "C35", "C36", "C37", "C39", "C40", "C41", "C43", "C44", "C45",
    "C47", "C48", "C49", "C54", "C55", "C56", "C57", "C58", "C59",
    "C60", "C61", "C62", "C64", "C65", "C66", "C67", "C68", "C69",
}
UNRESOLVED_PLACEMENT_REFS = {"C51", "C52", "C53", "C70", "C71", "C72"}
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


def pcb_footprint_block(ref: str) -> str:
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
    return block


def pcb_footprint_pad_midpoint(ref: str) -> tuple[float, float]:
    block = pcb_footprint_block(ref)
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


def pcb_footprint_population_flags(ref: str) -> tuple[bool, bool]:
    block = pcb_footprint_block(ref)
    attr = re.search(r"\n\t\t\(attr\s+([^\n)]+)\)", block)
    tokens = set(attr.group(1).split()) if attr is not None else set()
    return "dnp" in tokens, "exclude_from_pos_files" in tokens


def schematic_population_flags(ref: str) -> tuple[str, str]:
    text = SCHEMATIC.read_text(encoding="utf-8")
    marker = f'(property "Reference" "{ref}"'
    ref_at = text.find(marker)
    if ref_at < 0:
        raise SystemExit(f"decap audit: schematic is missing {ref}")
    line_start = text.rfind("\n", 0, ref_at) + 1
    flags_start = text.rfind("\n", 0, line_start - 1) + 1
    flags = text[flags_start:line_start]
    match = re.search(r"\(on_board (yes|no)\) \(dnp (yes|no)\)", flags)
    if match is None:
        raise SystemExit(f"decap audit: cannot parse {ref} schematic population flags")
    return match.group(1), match.group(2)


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
    legacy = evidence.get("legacy_grid_mapping", {})
    diagnostics: list[str] = []
    partition = (
        set(REGISTERED_DRAM_REFS)
        | OPTIONAL_GRID_DNP_REFS
        | UNRESOLVED_PLACEMENT_REFS
        | {"C63"}
    )
    if partition != set(CAP_REFS):
        diagnostics.append("C35-C72 population-disposition partition is incomplete")

    for source in (drawing, owner, legacy):
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
        if cap_chip(board, ref).get("assembly_dnp"):
            diagnostics.append(f"{ref}: factory-populated target is marked assembly DNP")
        if cap_chip(board, ref).get("procurement", {}).get("action") != "circuit-review":
            diagnostics.append(f"{ref}: unresolved factory value is not sourcing-gated")
        if schematic_population_flags(ref) != ("yes", "no"):
            diagnostics.append(f"{ref}: factory-populated schematic flags changed")
        if pcb_footprint_population_flags(ref) != (False, False):
            diagnostics.append(f"{ref}: factory-populated source-PCB footprint is marked DNP")

    optional = evidence.get("target_optional_grid_dnp", {})
    optional_refs = {str(ref) for ref in optional.get("refs", [])}
    if optional_refs != OPTIONAL_GRID_DNP_REFS:
        diagnostics.append("optional-grid DNP set is not the guarded 27 refs")
    if not valid_bbox(owner.get("optional_grid_bbox_px"), owner.get("dimensions_px")):
        diagnostics.append("owner optional-grid box is invalid")
    if "fabricated two-pad footprint" not in str(optional.get("population_state", "")):
        diagnostics.append("optional-grid footprint-retention disposition is missing")
    for ref in sorted(OPTIONAL_GRID_DNP_REFS):
        chip = cap_chip(board, ref)
        if chip.get("assembly_dnp") is not True or chip.get("pcb_dnp"):
            diagnostics.append(f"{ref}: must be assembly-DNP with its PCB footprint retained")
        if schematic_population_flags(ref) != ("yes", "yes"):
            diagnostics.append(f"{ref}: schematic must retain the footprint and mark DNP")
        if pcb_footprint_population_flags(ref) != (True, True):
            diagnostics.append(
                f"{ref}: source-PCB footprint must be DNP and excluded from position files"
            )
        generated_position = generated.get(ref)
        if generated_position is None:
            diagnostics.append(f"{ref}: legacy generator footprint is missing")
        elif math.dist(generated_position[:2], pcb_footprint_pad_midpoint(ref)) > MAX_POSITION_ERROR_MM:
            diagnostics.append(f"{ref}: retained source-PCB footprint differs from generator")
        note = str(chip.get("prov", {}).get("pins", ""))
        if "assembly DNP with the fabricated footprint retained" not in note:
            diagnostics.append(f"{ref}: board provenance lost assembly-DNP disposition")
    for ref in sorted(UNRESOLVED_PLACEMENT_REFS):
        chip = cap_chip(board, ref)
        if chip.get("assembly_dnp") or chip.get("pcb_dnp"):
            diagnostics.append(f"{ref}: unresolved non-field population was prematurely closed")
        if chip.get("procurement", {}).get("action") != "circuit-review":
            diagnostics.append(f"{ref}: unresolved placement/value is not sourcing-gated")
        if pcb_footprint_population_flags(ref) != (False, False):
            diagnostics.append(f"{ref}: unresolved source-PCB footprint is marked DNP")
    if schematic_population_flags("C63") != ("no", "yes"):
        diagnostics.append("C63 schematic no-footprint DNP flags changed")

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
        if chip.get("pcb_dnp"):
            population = "DNP / no PCB footprint"
        elif chip.get("assembly_dnp"):
            population = "assembly DNP / footprint retained"
        elif ref in REGISTERED_DRAM_REFS:
            population = "populate (factory drawing)"
        else:
            population = "pending / currently modeled populated"
        rows.append((ref, value, population, p1, p2, note))

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
        "Status: **DRAM-FIELD POPULATION CLOSED / C63 TARGET DNP CLOSED / VALUES AND FOOTPRINT PLACEMENTS PENDING**",
        "",
        "This generated report isolates the C35-C72 decoupling-capacitor",
        "authenticity issue. The board model and routed PCB preserve the two",
        "array-power bypass rail groups as schematic intent. The `.009` factory",
        "drawing and owner-board morphology close the 31-site DRAM-field population:",
        "fit C38/C42/C46/C50 and leave the other 27 inherited footprints empty.",
        "C63 has no target footprint. Six non-field placement/population dispositions,",
        "33 exact target footprint placements, and all factory capacitance values remain open.",
        "",
        "## Checks",
        "",
        "| Check | Result | Evidence |",
        "| --- | --- | --- |",
        table_row(["All C35-C72 refs exist in board JSON", "PASS", f"{len(rows)}/38 rows"]),
        table_row(["Rail-group connectivity matches model expectation", "PASS" if group_ok else "FAIL", ", ".join(f"{k}: {v}" for k, v in sorted(group_counts.items()))]),
        table_row(["Current model value is uniform 0,047", "PASS" if value_ok else "FAIL", ", ".join(f"{k or '-'}: {v}" for k, v in sorted(model_values.items()))]),
        table_row(["Target DRAM-bank C38/C42/C46/C50 placements are registered", "PASS" if dram_placement_ok else "FAIL", "factory drawing + owner landing/remnant sites + generator/source PCB" if dram_placement_ok else "; ".join(dram_placement_diagnostics)]),
        table_row(["Other 27 inherited DRAM-grid sites are assembly DNP", "PASS" if dram_placement_ok else "FAIL", "bare tinned target footprints retained in PCB; native KiCad DNP/position metadata and populate-now BOM are guarded"]),
        table_row(["C63 target-board population is DNP", "PASS" if c63_dnp else "FAIL", "registered bare site between D41/D40; no source-PCB footprint"]),
        table_row(["Historical value census is reconciled per position", "FAIL", "raw notes report mixed values but no per-position mapping"]),
        "",
        "## Current Board Model",
        "",
        "| Ref | Model value | Target population | Pin 1 net | Pin 2 net | Provenance note |",
        "| --- | --- | --- | --- | --- | --- |",
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
            "- The same complete target view omits the other 27 positions in the",
            "  older `.006` 4x8 zigzag. The owner view shows those inherited sites",
            "  as clean bare tinned landings, including the four alternate bottom-row",
            "  sites. They remain fabricated verification footprints but are marked",
            "  assembly DNP and excluded from the populate-now BOM.",
            "- The retained factory and owner-photo evidence includes aggregate",
            "  mixed-value capacitor counts, but no defensible mapping from those",
            "  counts to individual C35-C72 positions.",
            "- C51-C53 and C70-C72 still require target-revision placement/population",
            "  disposition. Exact target-artwork placement of those six plus the 27",
            "  retained bare grid footprints also remains to be photogrammetrically",
            "  registered; `.006` coordinates are not `.009` placement proof.",
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
