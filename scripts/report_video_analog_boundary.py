#!/usr/bin/env python3
"""Guard the .009 composite-video handoff and the retired .006 RF option."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "kicad/juku.board.json"
DISPOSITION = ROOT / "ref/photos/dgsh5-109-009-sb/rf-option-disposition.json"
REPORT = ROOT / "docs/video-analog-boundary.md"
CORRECTION = ROOT / "ref/photos/juku-pcb-2/c94-endpoint-registration.json"

RETAINED_NETS = {
    "VID_MIX1": {("D37", "11"), ("D34", "12")},
    "D34_SYNC": {("D34", "8"), ("R62", "1")},
    "D34_SIG": {("D34", "11"), ("R63", "1")},
    "VT2_BASE": {("R62", "2"), ("R63", "2"), ("R64", "1"), ("VT2", "3")},
    "VIDEO_OUT": {("VT2", "1"), ("R65", "1")},
    "SOUND_CLAMP": {
        ("R66", "2"), ("VD3", "2"), ("R67", "1"),
    },
    "X6_A3_BOUNDARY": {("AX603", "1"), ("X6", "1")},
    "R67_2_BOUNDARY": {("R67", "2")},
    "C94_1_BOUNDARY": {("C94", "1")},
    "C94_2_BOUNDARY": {("C94", "2")},
}

REUSED_BOUNDARY_NETS = {
    f"{ref}_{pin}_BOUNDARY": {(ref, pin)}
    for ref in ("C9", "C10", "C11", "C12", "C15")
    for pin in ("1", "2")
}

RETIRED_NETS = {
    "SND_MIX", "VT3_BASE", "RF_RAIL", "VT3_E", "VT4_B",
    "RF_TANK", "VT4_C", "RF_TAP", "HF_OUT", "VT4_E",
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def node_set(board: dict, name: str) -> set[tuple[str, str]]:
    return {tuple(node) for node in board["nets"].get(name, {}).get("nodes", [])}


def endpoint_text(board: dict, name: str) -> str:
    return ", ".join(f"{ref}.{pin}" for ref, pin in sorted(node_set(board, name))) or "-"


def table_row(values: list[object]) -> str:
    return "| " + " | ".join(str(value).replace("|", "/") for value in values) + " |"


def main() -> int:
    board = load(BOARD)
    disposition = load(DISPOSITION)
    correction = load(CORRECTION)
    chips = {item["ref"]: item for item in board["chips"]}
    all_nodes = {
        tuple(node)
        for net in board["nets"].values()
        for node in net.get("nodes", [])
    }

    legacy_dnp = set(disposition["legacy_dnp_refs"])
    reused = set(disposition["reused_target_boundary_refs"])
    source_files = [
        disposition["legacy_source"]["schematic"],
        disposition["legacy_source"]["group_bom"],
        disposition["target_evidence"]["electrical_image"],
        *disposition["target_evidence"]["assembly_images"],
        *disposition["target_evidence"]["owner_images"],
    ]

    checks: list[tuple[str, bool, str]] = []
    checks.append((
        "All cross-revision evidence files are local",
        all((ROOT / name).is_file() for name in source_files),
        f"{len(source_files)} schematic/BOM/factory/owner artifacts",
    ))
    checks.append((
        "Legacy .006 RF-only population is absent from the .009 board model",
        not (legacy_dnp & chips.keys())
        and not any(ref in legacy_dnp for ref, _ in all_nodes),
        ", ".join(sorted(legacy_dnp)),
    ))
    checks.append((
        "Legacy RF net names are retired",
        not (RETIRED_NETS & board["nets"].keys()),
        ", ".join(sorted(RETIRED_NETS)),
    ))
    checks.append((
        "Factory-reused C9/C10/C11/C12/C15 remain generic capacitors",
        reused == {"C9", "C10", "C11", "C12", "C15"}
        and all(chips.get(ref, {}).get("type") == "C_KM" for ref in reused),
        "physical .009 identities retained; .006 RF assignments not carried across",
    ))
    checks.append((
        "Exact .009 source proves reused capacitors' +5 V/GND pair while pad polarity stays open",
        disposition.get("reused_target_schematic_pair") == {
            "refs": ["C9", "C10", "C11", "C12", "C15"],
            "rails": ["P5V", "GND"],
            "physical_pad_mapping": None,
        },
        "sheet-1 C9...C12/C15 bypass group; physical pad mapping pending",
    ))

    guarded = {**RETAINED_NETS, **REUSED_BOUNDARY_NETS}
    for name, required in guarded.items():
        checks.append((
            f"`{name}` has exactly the target endpoints",
            node_set(board, name) == required,
            endpoint_text(board, name),
        ))

    checks += [
        (
            "VT2 composite-video emitter follower is retained",
            chips.get("VT2", {}).get("type") == "Q_KT13"
            and chips.get("VT2", {}).get("value") == "КТ315"
            and chips.get("VT2", {}).get("pins") == {"1": "E", "2": "C", "3": "B"}
            and "video emitter follower" in chips.get("VT2", {}).get("prov", {}).get("pins", ""),
            "exact .009 E3 sheet 2 draws R62/R63/R64, VT2, R65 and the VIDEO output; .006 is historical corroboration",
        ),
        (
            "R66 clamp input remains on the source-proved +12 V rail",
            ("R66", "1") in node_set(board, "P12V"),
            "sheet-2 B arrow is +12 V",
        ),
        (
            "Unsupported physical X7 is absent; VT2/R65 video node is retained",
            "X7" not in chips
            and node_set(board, "VIDEO_OUT") == {("VT2", "1"), ("R65", "1")},
            "VIDEO_OUT is VT2.1/R65.1; X6 A:3 remains a target-board continuity boundary",
        ),
        (
            "Bracket X6 A:3 signal is isolated pending continuity; A:4 is ground",
            node_set(board, "X6_A3_BOUNDARY") == {("AX603", "1"), ("X6", "1")}
            and {("AX604", "1"), ("X6", "2")} <= node_set(board, "GND"),
            "A:3/X6.1 electrical net open / A:4/X6.2 GND; no PCB X6 body",
        ),
        (
            "VT2 photo registration and unresolved C94 model remain distinct",
            chips.get("C94", {}).get("type") == "C_KM"
            and not chips.get("C94", {}).get("value")
            and correction.get("vt2_component_registration", {}).get("visible_marking") == "Б / 8901"
            and correction.get("c94_disposition", {}).get("joined_endpoints") == [],
            "yellow three-lead body is VT2; separately drawn C94 retains two measurement boundaries",
        ),
    ]

    ok = all(result for _, result, _ in checks)
    status = (
        ".009 COMPOSITE HANDOFF GUARDED / .006 RF OPTION DNP"
        if ok else "VIDEO/RF REVISION DISPOSITION FAILED"
    )

    lines = [
        "# Video analog boundary",
        "",
        f"Status: **{status}**",
        "",
        'Exact `.009` Э3 sheet 2 records the VT2 composite-video stage. Its',
        'factory placement and owner-photo evidence omit the older `.006` VT3/VT4',
        'RF option. C9/C10/C11/C12/C15 are reused `.009` bypass identities;',
        'their physical pad-to-rail assignments remain open. C94 has a source-proved',
        '+5 V/GND pair with body and pad mapping unresolved.',
        '',
        'D37.11–D34.12 is source-traced and photo-supported; owner electrical',
        'continuity remains unmeasured. Its image controls are preserved in the',
        '[D34 via review](../ref/photos/juku-pcb-2/d34-pin12-video-via-review.json).',
        "",
        "## Command",
        "",
        "Run from the repository root with Python 3 (standard library only).",
        "The command replaces this report with its source-model check results",
        "and exits with status 1 if any listed check fails.",
        "",
        "```sh",
        "python3 scripts/report_video_analog_boundary.py",
        "```",
        "",
        "## Revision checks",
        "",
        "| Check | Result | Evidence |",
        "| --- | --- | --- |",
    ]
    lines.extend(table_row([name, "PASS" if result else "FAIL", evidence])
                 for name, result, evidence in checks)

    lines += [
        "",
        "Per-net provenance is retained in [the board model](../kicad/juku.board.json).",
    ]

    lines += [
        "",
        "## Interpretation",
        "",
        '- This guard checks source-model endpoints, revision/population metadata',
        '  and evidence-file availability. It does not inspect those images anew,',
        '  validate routed copper, simulate loaded output voltage or measure hardware.',
        '- VT2/R62-R67/VD3 form the retained analog handoff. The',
        '  [VT2 source review](vt2-009-source-review.md) records body identification,',
        '  values, pin mapping and electrical limits.',
        '- Bracket X6 connects through A:3/A:4. A:4 is ground; A:3 remains isolated',
        '  pending its target-board connection to VIDEO_OUT. See the',
        '  [X6 review](x6-a3-video-source-conflict-review.md).',
        "- VD3's schematic cathode is at SOUND_CLAMP and its anode at ground.",
        '  The board-model diode pin names are reversed; photos do not establish',
        '  the cathode-band lead sufficiently to remap physical pads. This remains',
        '  an electrical-use boundary.',
        "- C94 population, value and pad joins remain open. R67.2's target-board",
        '  continuation and the reused bypass pad mappings also require confirmation.',
        '- [Revision evidence](../ref/photos/dgsh5-109-009-sb/rf-option-disposition.json)',
        '  preserves source identities and the `.006` RF population exclusion.',
        "",
    ]

    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    print(f"Status: {status}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
