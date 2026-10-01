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
            "VT2/C94 owner-photo misidentification remains corrected",
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
        "Status date: 2026-07-13.",
        "",
        f"Status: **{status}**",
        "",
        "Exact `.009` Э3 sheet 2 draws the populated VT2 composite-video stage and",
        "the VIDEO output contacts. The older `.006` electrical sheet is historical",
        "corroboration; its dashed VT3/VT4 RF modulator is not a valid `.009` population source.",
        "The complete `.009` factory placement views label only VT1/VT2, and the complete owner",
        "component-side tile set corroborates that absence. The archived group BOM independently",
        "assigns the extra RF transistors and the 4.7 kΩ adjustable trimmer to `.006`.",
        "",
        "C9/C10/C11/C12/C15 are not removed: `.009` reuses those reference numbers around",
        "D93-D102. Exact `.009` sheet-1 supply detail makes each a +5 V-to-ground",
        "bypass, but their physical pin-to-rail assignments remain explicit continuity",
        "boundaries instead of inheriting superseded `.006` RF nets. The same source",
        "proves C94's +5 V/GND pair while its body and pad mapping stay open. X6 is instead",
        "bracket-mounted: A:3/X6.1 is isolated pending continuity and A:4/X6.2 reaches GND.",
        "",
        "The exact `.009` sheet-2 overview and lower-right detail now trace D37.11 to D34.12.",
        "D34.13 is on rail A (+5 V), and D34.11 drives R63 toward the VT2",
        "composite-video stage. The adjacent D103.11 1.23 MHz/tag-13 line stays separate",
        "from D34.12; the previous clock assignment was a tracing error. Owner-board",
        "continuity between D37.11 and D34.12 remains to be measured",
        "(`ref/schematics/d35-d37-d42-source-recheck.json`).",
        "Native owner photos show D34.12 on front copper to the open hole near",
        "(3418,2985). Six independent cross-face controls predict its solder",
        "counterpart (795,2642) within about 4 px; visible B.Cu reaches the",
        "counted D37.11 solder pad near (2045,2620). This photo-supported",
        "route still requires a power-off electrical continuity check",
        "(`ref/photos/juku-pcb-2/d34-pin12-video-via-review.json`).",
        "",
        "## Command",
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
        "## Retained target nets and boundaries",
        "",
        "| Net | Endpoints | Source note |",
        "| --- | --- | --- |",
    ]
    for name in guarded:
        net = board["nets"].get(name, {})
        lines.append(table_row([f"`{name}`", f"`{endpoint_text(board, name)}`", net.get("src", "-")]))

    lines += [
        "",
        "## Interpretation",
        "",
        "- The `.009` PCB no longer carries fifteen physically contradicted `.006` RF-only parts",
        "  or the ten false pad-collision pairs they caused.",
        "- VT2/R62-R67/VD3 remain the populated target analog handoff. Exact `.009`",
        "  source frames and their limits are recorded in `docs/vt2-009-source-review.md`.",
        "  Two overlapping July views plus an independent May angle identify the yellow",
        "  three-lead body as",
        "  VT2 marked `Б / 8901`; its emitter shares R65.1/VIDEO_OUT. The separately drawn",
        "  C94 is obscured: its schematic +5 V/GND pair is proved, while its",
        "  population, value, and individual physical pad joins require inspection.",
        "- X6 is not evidence for the removed VT3/VT4 RF network. Its bracket cable",
        "  reaches A:3/A:4, but A:3's prior VD3/SOUND_CLAMP photo attribution was",
        "  rejected by the original-resolution reread. See",
        "  `docs/x6-a3-video-source-conflict-review.md`.",
        "- Exact `.009` sheet 2 draws VD3's cathode at SOUND_CLAMP and anode at ground.",
        "  The current board-model diode pin names are reversed; the archived photos do",
        "  not yet establish the cathode-band lead well enough to remap physical pads.",
        "  See `docs/vt2-009-source-review.md` before electrical use of the sound clamp.",
        "- Machine-readable source and population evidence is in",
        "  `ref/photos/dgsh5-109-009-sb/rf-option-disposition.json`.",
        "",
    ]

    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    print(f"Status: {status}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
