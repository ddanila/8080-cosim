#!/usr/bin/env python3
"""Audit the exact .009 sheet-3 IC power table against model and PCB pads."""

import json
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/sheet3-power-table-audit.md"
SOURCE = "ref/photos/dgsh5-109-009-e3/PXL_20260718_101633062.jpg"
BOARDS = (
    ROOT / "kicad/juku.kicad_pcb",
    ROOT / "kicad/juku_routed.kicad_pcb",
    ROOT / "kicad/juku_routed_candidate.kicad_pcb",
)

# Original-pixel table crop (1200,2890)-(2700,3470). Rows are ground,
# +5 V, then +12 V. The К155ЛН3/К555ТМ2 column is 7/14; the
# КП12/ИЕ7/АГ3/РЕ3/ЛП11 column is 8/16; ВГ93 is 20/21/40; ВА87 is 10/20.
EXPECTED = {
    "D28": {"7": "GND", "14": "P5V"},
    "D93": {"20": "GND", "21": "P5V", "40": "P12V"},
    "D94": {"8": "GND", "16": "P5V"},
    "D95": {"8": "GND", "16": "P5V"},
    "D96": {"7": "GND", "14": "P5V"},
    "D97": {"8": "GND", "16": "P5V"},
    "D98": {"8": "GND", "16": "P5V"},
    "D99": {"8": "GND", "16": "P5V"},
    "D100": {"10": "GND", "20": "P5V"},
    "D101": {"8": "GND", "16": "P5V"},
    "D102": {"8": "GND", "16": "P5V"},
    "D106": {"8": "GND", "16": "P5V"},
}


def main() -> int:
    board_json = json.loads((ROOT / "kicad/juku.board.json").read_text(encoding="utf-8"))
    nodes = {net: {tuple(node) for node in value["nodes"]} for net, value in board_json["nets"].items()}
    chips = {chip["ref"]: chip["type"] for chip in board_json["chips"]}
    footprints = {}
    for path in BOARDS:
        pcb = pcbnew.LoadBoard(str(path))
        footprints[path.name] = {
            fp.GetReference(): {pad.GetNumber(): pad.GetNetname() for pad in fp.Pads()}
            for fp in pcb.GetFootprints()
        }

    rows = []
    missing = []
    for ref, pins in EXPECTED.items():
        if ref not in chips:
            missing.append(f"{ref} missing chip")
        for pin, rail in pins.items():
            if (ref, pin) not in nodes.get(rail, set()):
                missing.append(f"model {ref}.{pin} expected {rail}")
            for name, pads in footprints.items():
                actual = pads.get(ref, {}).get(pin)
                if actual != rail:
                    missing.append(f"{name} {ref}.{pin} expected {rail}, found {actual or 'none'}")
        entries = ", ".join(f"{pin}:{rail}" for pin, rail in pins.items())
        rows.append(f"| `{ref}` | `{chips.get(ref, 'missing')}` | `{entries}` |")

    count = sum(map(len, EXPECTED.values()))
    lines = [
        "# Exact .009 sheet-3 IC power-table audit", "",
        f"Source: `{SOURCE}`, original pixels `(1200,2890)-(2700,3470)`.", "",
        f"Result: **{'FAIL' if missing else 'PASS'}** — {len(EXPECTED)} fitted devices, {count} table endpoints, checked in board JSON and all three PCB variants; {len(missing)} mismatches.", "",
        "## Command", "",
        'Run from the repository root with KiCad’s `pcbnew` available to the chosen Python.',
        'The command below uses the system Python; adjust its path for your KiCad installation.',
        "The command overwrites this report.", "", "```sh", "/usr/bin/python3 scripts/check_sheet3_power_table.py", "```", "",
        "| Ref | Model type | Table pin:rail entries |", "| --- | --- | --- |",
        *rows, "", "## Scope boundary", "",
        "The script checks the 12 fixed references and 25 transcribed endpoints",
        "against board JSON nodes and pad net names in `juku.kicad_pcb`,",
        "`juku_routed.kicad_pcb`, and `juku_routed_candidate.kicad_pcb`.",
        "Model types are displayed, not validated. The source image is cited for",
        "the transcription; its pixels and hash are not checked here.",
        "The audit does not prove copper connectivity or physical-board continuity.", "",
    ]
    if missing:
        lines += ["## Mismatches", "", *[f"- {item}" for item in missing], ""]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Sheet-3 power table: {len(EXPECTED)} devices, {count} endpoints, mismatches={len(missing)}")
    return int(bool(missing))


if __name__ == "__main__":
    raise SystemExit(main())
