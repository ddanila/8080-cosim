#!/usr/bin/env python3
"""Check all adopted .009 IC power-table cells against three PCB pad sets."""

import json
from pathlib import Path

import pcbnew

from check_sheet1_power_table import PIN_RAILS as SHEET1
from check_sheet2_power_table import PIN_RAILS as SHEET2
from check_sheet3_power_table import EXPECTED as SHEET3


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/009-power-table-pad-parity.md"
BOARDS = (
    ROOT / "kicad/juku.kicad_pcb",
    ROOT / "kicad/juku_routed.kicad_pcb",
    ROOT / "kicad/juku_routed_candidate.kicad_pcb",
)


def main() -> int:
    model = json.loads((ROOT / "kicad/juku.board.json").read_text(encoding="utf-8"))
    expected = {}
    conflicts = []
    sheet_counts = [0, 0, 0]
    for chip in model["chips"]:
        for index, table in enumerate((SHEET1, SHEET2)):
            for rail, pin in table.get(chip["type"], ()):
                key = (chip["ref"], pin)
                if key in expected and expected[key] != rail:
                    conflicts.append(f"{chip['ref']}.{pin}: {expected[key]} versus {rail}")
                expected[key] = rail
                sheet_counts[index] += 1
    for ref, pins in SHEET3.items():
        for pin, rail in pins.items():
            key = (ref, pin)
            if key in expected and expected[key] != rail:
                conflicts.append(f"{ref}.{pin}: {expected[key]} versus {rail}")
            expected[key] = rail
            sheet_counts[2] += 1

    board_results = []
    for path in BOARDS:
        pcb = pcbnew.LoadBoard(str(path))
        pads = {
            (fp.GetReference(), pad.GetNumber()): pad.GetNetname()
            for fp in pcb.GetFootprints() for pad in fp.Pads()
        }
        mismatches = [
            f"{ref}.{pin}: table {rail}, pad {pads.get((ref, pin)) or 'missing'}"
            for (ref, pin), rail in expected.items()
            if pads.get((ref, pin)) != rail
        ]
        board_results.append((path.name, mismatches))

    failed = bool(conflicts or any(mismatches for _, mismatches in board_results))
    lines = [
        "# Exact .009 power-table PCB pad parity", "",
        "Sources: sheet-1 `PXL_20260718_101827714.jpg`, sheet-2 `PXL_20260718_101927794.jpg`, and sheet-3 `PXL_20260718_101633062.jpg` in `ref/photos/dgsh5-109-009-e3/`.", "",
        f"Result: **{'FAIL' if failed else 'PASS'}** — {sheet_counts[0]} sheet-1, {sheet_counts[1]} sheet-2, and {sheet_counts[2]} sheet-3 adopted table entries; {len(expected)} unique package pads after overlap, {len(conflicts)} conflicting source assignments.", "",
        "## Command", "", "```sh", "/usr/bin/python3 scripts/check_009_power_table_pad_parity.py", "```", "",
        "| PCB | Matching pads | Mismatches |", "| --- | ---: | ---: |",
        *[f"| `{name}` | {len(expected) - len(mismatches)} | {len(mismatches)} |" for name, mismatches in board_results],
        "", "Sheet-1 and sheet-2 entries are selected by the current board JSON chip types;",
        "sheet-3 entries use a fixed reference list. This check imports those",
        "transcriptions without running the individual sheet audits. It does not",
        "validate JSON rail nodes, enforce the full chip census, or hash the images.", "",
        "This checks adopted table entries against pad net names in the saved PCB files. Sheet-1 D104.16 and sheet-2 ИР16/РУ4 conflicts remain outside the adopted entry sets. The reports for each sheet document those limits. Pad names do not establish track contact or original-board continuity.", "",
    ]
    if conflicts or any(mismatches for _, mismatches in board_results):
        lines += ["## Mismatches", "", *[f"- source {item}" for item in conflicts]]
        for name, mismatches in board_results:
            lines += [f"- {name}: {item}" for item in mismatches]
        lines.append("")
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f".009 power-table pad parity: {len(expected)} unique pads, mismatches={sum(len(x) for _, x in board_results)}, source conflicts={len(conflicts)}")
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
