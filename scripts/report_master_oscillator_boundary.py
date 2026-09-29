#!/usr/bin/env python3
"""Guard the recovered sheet-2 16 MHz crystal oscillator topology."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "kicad" / "juku.board.json"
REPORT = ROOT / "docs" / "master-oscillator-boundary.md"

REQUIRED = {
    "OSC_FB": {("D59", "9"), ("R31", "1"), ("R32", "1"), ("Z1", "1")},
    "OSC_PRE": {("D59", "8"), ("D59", "1"), ("R31", "2")},
    "XTAL_TRIM": {("Z1", "2"), ("C73", "1")},
    "OSC": {("D59", "2"), ("D59", "3"), ("D40", "2"), ("C73", "2")},
    "PST_CLK": {("D59", "4"), ("D44", "5"), ("R32", "2")},
}


def row(items: list[str]) -> str:
    return "| " + " | ".join(items) + " |"


def main() -> int:
    board = json.loads(BOARD.read_text(encoding="utf-8"))
    chips = {item["ref"]: item for item in board["chips"]}
    actual = {
        name: {tuple(node) for node in board["nets"].get(name, {}).get("nodes", [])}
        for name in REQUIRED
    }
    checks: list[tuple[str, bool, str]] = []
    for name, expected in REQUIRED.items():
        checks.append((
            f"`{name}` preserves every sheet-2 endpoint",
            expected <= actual[name],
            ", ".join(f"{ref}.{pin}" for ref, pin in sorted(actual[name])) or "-",
        ))
    checks.extend((
        (
            "R31/R32 are modeled as physical oscillator parts",
            chips.get("R31", {}).get("type") == "R_AXIAL" and chips.get("R32", {}).get("type") == "R_AXIAL",
            f"R31={chips.get('R31', {}).get('value', '-')}; R32={chips.get('R32', {}).get('value', '-')}",
        ),
        (
            "Crystal and trimmer have no omitted endpoint",
            all(any((ref, pin) in endpoints for endpoints in actual.values())
                for ref in ("Z1", "C73") for pin in ("1", "2")),
            "Z1.1/Z1.2 and C73.1/C73.2 are assigned",
        ),
        (
            "R31 exact-revision value agrees with owner body",
            "R31=1к" in chips.get("R31", {}).get("prov", {}).get("pins", "")
            and "older .006" in chips.get("R31", {}).get("prov", {}).get("pins", "")
            and chips.get("R31", {}).get("value") == "1к",
            "`.009` sheet 2: 1к; owner board #2: 1K0; older `.006` scan: 820 ohm",
        ),
        (
            "R32 exact-revision value agrees with owner body",
            "R32=1,3к" in chips.get("R32", {}).get("prov", {}).get("pins", "")
            and "1K3" in chips.get("R32", {}).get("prov", {}).get("pins", "")
            and chips.get("R32", {}).get("value") == "1,3к",
            "`.009` sheet 2: 1,3к; owner board #2: 1K3; older `.006` scan: 1,2к",
        ),
        (
            "R34 exact-revision value agrees with owner body",
            "R34=12к" in chips.get("R34", {}).get("prov", {}).get("pins", "")
            and "12K" in chips.get("R34", {}).get("prov", {}).get("pins", "")
            and chips.get("R34", {}).get("value") == "12к",
            "`.009` sheet 2: 12к; owner board #2: 12K; older `.006` scan: 13к",
        ),
        (
            "C73 exact-revision range remains open",
            not chips.get("C73", {}).get("value")
            and "prints no C73 capacitance range" in chips.get("C73", {}).get("prov", {}).get("pins", "")
            and "older .006" in chips.get("C73", {}).get("prov", {}).get("pins", ""),
            "`.009` sheet 2: no range; older `.006`: 4/20; owner top: unreadable",
        ),
        (
            "D59 section 5->6 is traced into the mux-enable links",
            ["D59", "5"] not in board.get("no_connects", [])
            and ["D59", "6"] not in board.get("no_connects", [])
            and {("D40", "11"), ("D59", "5"), ("E14", "1")} <= {
                tuple(node) for node in board["nets"]["LATCH_B"]["nodes"]
            }
            and {("D59", "6"), ("E13", "1")} <= {
                tuple(node) for node in board["nets"]["CPU_MUX_G"]["nodes"]
            },
            "full-resolution sheet 2: D59.5 feeds E14/video /G and D59.6 feeds E13/CPU /G",
        ),
    ))
    ok = all(result for _, result, _ in checks)
    status = "SCHEMATIC OSCILLATOR TOPOLOGY GUARDED; C4 PHYSICAL GAP" if ok else "MASTER OSCILLATOR CHECK FAILED"
    lines = [
        "# Master oscillator boundary",
        "",
        "Status date: 2026-07-23.",
        "",
        f"Status: **{status}**",
        "",
        "The sheet-2 16 MHz oscillator around D59 matches its drawn endpoints in",
        "the source board model. The factory assembly drawing independently fixes",
        "R31 vertically between Z1 and D59 and R32 horizontally above D59; the owner",
        "photograph confirms both physical bodies. Native exact `.009` sheet-2",
        "`PXL_20260718_101908284.jpg` prints R31=`1к`, agreeing with board #2's",
        "visible `1K0` body. The older `.006` scan `ref/schematics/p2_sheet2.png`",
        "prints 820 ohms; this is a revision difference, not a conflict between the",
        "target board and the exact `.009` drawing.",
        "The same exact tile prints R32=`1,3к`; the overlapping owner photo",
        "`PXL_20260710_200439607.jpg` directly reads `1K3` on the horizontal",
        "body above the КР531ЛН1 package. The older `.006` scan has `1,2к`.",
        "An enlarged July owner view now appears to join the photographed R32 left",
        "lead to physical D59.4 and its right lead to D59.14 and a nearby pale R38=1K0",
        "left lead on continuous front copper. The exact `.009` sheet-2 drawing",
        "instead places R32 between D59.9 and D59.4; neither endpoint is D59.14.",
        "The checks below verify the drawn",
        "logical topology, not the owner-board R32 route. Confirm these physical",
        "connections and inspect for a cut or repair before adopting either topology",
        "for final copper (`ref/photos/juku-pcb-2/d59-orientation-audit.json`).",
        "The original-pixel comparisons are recorded in",
        "`ref/photos/juku-pcb-2/r31-r32-oscillator-value-review.json`.",
        "The adjacent D40 control pull-up R34 also changes from older `.006`",
        "13к to exact `.009` 12к; the fitted body directly reads `12K`",
        "(`ref/photos/juku-pcb-2/r34-d40-value-review.json`).",
        "C73's exact `.009` symbol has no printed capacitance range; the older",
        "`.006` 4/20 annotation is retained only as a measurement candidate.",
        "The fitted trimmer's visible top has no readable range. A May side view",
        "(`PXL_20260519_202052986.jpg`) reads `8811` on its cylindrical body,",
        "but supplies no interpretable range. The replica value field and BOM",
        "remain open pending physical measurement.",
        "",
        "The original-resolution `.009` sheet-2 oscillator frame",
        "`PXL_20260718_101908284.jpg` draws Z1 and C73 without a C4 branch.",
        "The `.009` assembly `PXL_20260711_114604420.jpg` and owner photos",
        "show a fitted C4 beside C73. One C4 lead visibly shares the upper C73",
        "terminal. Two native owner views now show the separate C73 lower terminal",
        "running on uninterrupted front copper to Z1's lower right lug. Under the",
        "sheet-2 Z1–C73 series topology, the shared C4-upper/C73-upper strip is",
        "therefore the likely opposite `OSC` side; Z1 lug numbering and remote",
        "D40/D59 continuity still need measurement. C4's other net and value remain",
        "unproved. Thus the checks below guard the drawn oscillator only; they",
        "do not establish a complete physical oscillator or authorize a C4 netlist",
        "or footprint (`ref/photos/juku-pcb-2/c4-c73-shared-node-review.json`).",
        "",
        "The separate `XTAL16M` rail remains deliberately unmerged: its suspected",
        "continuation from `OSC` still needs the pending sheet-2 bundle-tag read.",
        "",
        "## Checks",
        "",
        "| Check | Result | Evidence |",
        "| --- | --- | --- |",
    ]
    lines.extend(row([name, "PASS" if result else "FAIL", evidence]) for name, result, evidence in checks)
    lines.extend(("", "Generated by `python3 scripts/report_master_oscillator_boundary.py`." , ""))
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(status)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
