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
            f"`{name}` contains the required transcribed endpoints",
            expected <= actual[name],
            ", ".join(f"{ref}.{pin}" for ref, pin in sorted(actual[name])) or "-",
        ))
    checks.extend((
        (
            "R31/R32 use axial-resistor model types",
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
        f"Status: **{status}**",
        "",
        'The source board model retains the drawn sheet-2 16 MHz oscillator',
        'around D59. Exact `.009` values and fitted body markings agree on',
        'R31=1 kOhm, R32=1.3 kOhm and R34=12 kOhm. The checks table records',
        'older `.006` revision differences; image identities and comparisons are in',
        '[the R31/R32 review](../ref/photos/juku-pcb-2/r31-r32-oscillator-value-review.json)',
        'and [the R34 review](../ref/photos/juku-pcb-2/r34-d40-value-review.json).',
        '',
        '## Physical boundaries',
        '',
        '- **R32 route:** the exact schematic places R32 between D59.9 and D59.4.',
        '  The owner photo appears to connect it to D59.4 and D59.14, with a nearby',
        '  R38 lead on the latter conductor. Confirm continuity and inspect for cuts',
        '  or repairs before choosing final copper. See',
        '  [the D59 orientation audit](../ref/photos/juku-pcb-2/d59-orientation-audit.json).',
        '- **C73 range:** the exact `.009` drawing and fitted body do not establish',
        '  a capacitance range. The older `.006` 4/20 annotation remains a measurement',
        '  candidate; the replica value and BOM stay open.',
        '- **C4:** assembly and owner photos show a fitted capacitor sharing one',
        '  terminal with C73. The local exact schematic draws no C4 branch.',
        '  The model provisionally assigns C4.1 to C73.2/`OSC` by inference from',
        '  the drawn Z1-C73 series topology and the photographed C73-to-Z1 route.',
        '  Z1 lug numbering and continuity to D40/D59 remain unproved. C4.2 stays',
        '  on `C4_RETURN_HOLD`; its return, value, physical holes and placement',
        '  remain open. These placeholders do not prove C4 is parallel to C73.',
        '  See [the C4/C73 review](../ref/photos/juku-pcb-2/c4-c73-shared-node-review.json).',
        '- **OSC / XTAL16M:** these rails remain separate pending owner continuity.',
        "  D59.3's photographed branch reaches an open annulus whose connection to",
        '  Z1 is unproved. Use [the bench checklist](next-bench-session-checklist.md#d59-timing-and-oscillator-probes-p1)',
        '  for annulus-to-Z1/C73/D40.2/D39.10 measurements.',
        '',
        '## Command',
        '',
        'Run from the repository root with Python 3 (standard library only).',
        'The writer reads `kicad/juku.board.json`, overwrites this report even',
        'when checks fail, and returns status 1 on a failed check.',
        '',
        '```sh',
        'python3 scripts/report_master_oscillator_boundary.py',
        '```',
        '',
        "## Verification scope", "",
        "The generator reads canonical board JSON. It requires the listed",
        "endpoint subsets (additional members are allowed), axial R31/R32 types,",
        "Z1/C73 pin membership, selected value/provenance markers, and D59 mux",
        "enable endpoints. It does not hash or reread images, inspect PCB copper,",
        "verify oscillator startup, or measure frequency. Photo findings above",
        "are reviewed evidence summaries, not results recomputed by this guard.", "",
        "For net checks, the Evidence column lists all current members, not just",
        "the required subset defined in the writer's `REQUIRED` mapping. In particular,",
        "the displayed provisional `C4.1` member of `OSC` is not required by this guard.", "",
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
