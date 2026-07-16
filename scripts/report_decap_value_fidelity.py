#!/usr/bin/env python3
"""Generate the C35-C72 decoupling value/authenticity audit."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOARD_JSON = ROOT / "kicad" / "juku.board.json"
REPORT = ROOT / "docs" / "decap-value-fidelity.md"

CAP_REFS = [f"C{i}" for i in range(35, 73)]


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

    lines = [
        "# Decoupling capacitor value fidelity",
        "",
        "Status date: 2026-07-10.",
        "",
        "Status: **DECAP CONNECTIVITY GUARDED / C63 TARGET DNP CLOSED / PER-POSITION VALUE PENDING**",
        "",
        "This generated report isolates the C35-C72 decoupling-capacitor",
        "authenticity issue. The board model and routed PCB preserve the two",
        "array-power bypass rail groups as schematic intent. The target PCB has",
        "37 populated positions plus the photo-proven bare C63 DNP site, but the exact factory per-position",
        "capacitance values are not proven by current automatic evidence.",
        "",
        "## Checks",
        "",
        "| Check | Result | Evidence |",
        "| --- | --- | --- |",
        table_row(["All C35-C72 refs exist in board JSON", "PASS", f"{len(rows)}/38 rows"]),
        table_row(["Rail-group connectivity matches model expectation", "PASS" if group_ok else "FAIL", ", ".join(f"{k}: {v}" for k, v in sorted(group_counts.items()))]),
        table_row(["Current model value is uniform 0,047", "PASS" if value_ok else "FAIL", ", ".join(f"{k or '-'}: {v}" for k, v in sorted(model_values.items()))]),
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
            "- The retained factory and owner-photo evidence includes aggregate",
            "  mixed-value capacitor counts, but no defensible mapping from those",
            "  counts to individual C35-C72 positions.",
            "- DSN/PCB placement preserves the two physical rows, but the available",
            "  photographs do not expose readable markings for every position.",
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
    return 0 if group_ok and value_ok and c63_dnp else 1


if __name__ == "__main__":
    raise SystemExit(main())
