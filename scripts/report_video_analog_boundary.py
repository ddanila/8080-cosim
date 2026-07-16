#!/usr/bin/env python3
"""Guard the .009 composite-video handoff and the retired .006 RF option."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "kicad/juku.board.json"
DISPOSITION = ROOT / "ref/photos/dgsh5-109-009-sb/rf-option-disposition.json"
REPORT = ROOT / "docs/video-analog-boundary.md"

RETAINED_NETS = {
    "D34_SYNC": {("D34", "8"), ("R62", "1")},
    "D34_SIG": {("D34", "11"), ("R63", "1")},
    "VT2_BASE": {("R62", "2"), ("R63", "2"), ("R64", "1"), ("VT2", "2")},
    "VIDEO_OUT": {("VT2", "1"), ("R65", "1"), ("X7", "1"), ("C94", "2")},
    "SOUND_CLAMP": {
        ("R66", "2"), ("VD3", "2"), ("R67", "1"),
        ("AX603", "1"), ("X6", "1"),
    },
    "R67_2_BOUNDARY": {("R67", "2")},
    "C94_1_BOUNDARY": {("C94", "1")},
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
            chips.get("VT2", {}).get("type") == "Q_TO92"
            and "video emitter follower" in chips.get("VT2", {}).get("prov", {}).get("pins", ""),
            "the non-RF .006 path remains the closest electrical evidence for the populated .009 VT2 stage",
        ),
        (
            "R66 clamp input remains on the source-proved +12 V rail",
            ("R66", "1") in node_set(board, "P12V"),
            "sheet-2 B arrow is +12 V",
        ),
        (
            "X7 composite connector retains signal and ground",
            ("X7", "1") in node_set(board, "VIDEO_OUT")
            and ("X7", "2") in node_set(board, "GND"),
            "X7.1 VIDEO_OUT / X7.2 GND",
        ),
        (
            "Bracket X6 uses photographed A:3/A:4 cable landings",
            "X6_1_BOUNDARY" not in board["nets"]
            and {("AX603", "1"), ("X6", "1")} <= node_set(board, "SOUND_CLAMP")
            and {("AX604", "1"), ("X6", "2")} <= node_set(board, "GND"),
            "A:3/X6.1 SOUND_CLAMP / A:4/X6.2 GND; no PCB X6 body",
        ),
        (
            "Target C94 680 pF body remains modeled",
            chips.get("C94", {}).get("type") == "C_KM"
            and chips.get("C94", {}).get("value") == "680",
            ".009 factory identity plus populated owner-photo 680п marking",
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
        "The older `.006` electrical sheet remains useful for the populated VT2 composite-video",
        "stage, but its dashed VT3/VT4 RF modulator is not a valid `.009` population source.",
        "The complete `.009` factory placement views label only VT1/VT2, and the complete owner",
        "component-side tile set corroborates that absence. The archived group BOM independently",
        "assigns the extra RF transistors and the 4.7 kΩ adjustable trimmer to `.006`.",
        "",
        "C9/C10/C11/C12/C15 are not removed: `.009` reuses those reference numbers around",
        "D93-D102. Their factory positions remain on the PCB, but every pin is an explicit",
        "continuity boundary instead of inheriting the superseded `.006` RF nets. X6 is instead",
        "bracket-mounted: A:3/X6.1 is photo-closed to SOUND_CLAMP and A:4/X6.2 to GND.",
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
        "- VT2/R62-R67/VD3/C94/X7 remain the populated target analog handoff. Two overlapping",
        "  July views plus an independent May angle close C94.2 to R65.1/VIDEO_OUT; C94.1",
        "  and the other unresolved",
        "  endpoints still require continuity or bench capture.",
        "- X6 is not evidence for the removed VT3/VT4 RF network. Its target bracket cable",
        "  instead closes directly to the retained SOUND_CLAMP/GND handoff.",
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
