#!/usr/bin/env python3
"""Compare legible .009 sheet-2 IC power-table cells with board JSON."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = "ref/photos/dgsh5-109-009-e3/PXL_20260718_101927794.jpg"
REPORT = ROOT / "docs/sheet2-power-table-audit.md"
EMPTY_DRAM_SOCKETS = {f"D{number}" for number in range(60, 84)}

# Entries below are transcribed from the sheet-2 table. Its row labels are
# A(+5), ground symbol, E(ground), F(+5), and G(+12/+5 selector).
# RU5 pin 1 is a RU3 population-option VBB rail, not a RU5 power pin.
PIN_RAILS = {
    "CLK_PHASE": (("P5V", "14"), ("GND", "7")),
    "PIT8253": (("P5V", "24"), ("GND", "12")),
    "IR82": (("P5V", "20"), ("GND", "10")),
    "IE7_CTR": (("P5V", "16"), ("GND", "8")),
    "AG3_ONESHOT": (("P5V", "16"), ("GND", "8")),
    "IE10_CTR": (("P5V", "16"), ("GND", "8")),
    "LA12_GATE": (("GND", "7"), ("P5V", "14")),
    "KP14_MUX": (("GND", "8"), ("P5V", "16")),
    "RASCAS_DEC": (("GND", "8"), ("P5V", "16")),
    "RU5": (("GND", "16"), ("RAIL_G", "8")),
}


def main() -> int:
    board = json.loads((ROOT / "kicad/juku.board.json").read_text(encoding="utf-8"))
    nodes = {name: {tuple(node) for node in net["nodes"]} for name, net in board["nets"].items()}
    rows, missing = [], []
    for chip in board["chips"]:
        expected = PIN_RAILS.get(chip["type"])
        if expected is None:
            continue
        ref = chip["ref"]
        gaps = [f"{ref}.{pin} → {rail}" for rail, pin in expected if (ref, pin) not in nodes[rail]]
        missing.extend(gaps)
        rows.append((ref, chip["type"], ", ".join(f"{pin}:{rail}" for rail, pin in expected), "FAIL" if gaps else "PASS"))
    count = sum(len(PIN_RAILS[kind]) for _, kind, _, _ in rows)
    empty_count = sum(ref in EMPTY_DRAM_SOCKETS for ref, _, _, _ in rows)
    fitted_count = len(rows) - empty_count
    lines = [
        "# Exact .009 sheet-2 IC power-table audit", "",
        f"Source: `{SOURCE}`; original pixels `(0,2150)-(3072,3920)`. Row labels also appear in `PXL_20260718_101924004.jpg`.", "",
        f"Result: **{'FAIL' if missing else 'PASS'}** for the unambiguous mapped columns — {len(rows)} modeled positions ({fitted_count} factory-fitted ICs and {empty_count} empty expansion sockets), {count} audited rail endpoints, {len(missing)} missing model endpoints. The ИР16 and РУ4 columns remain outside this pass.", "",
        "| Ref | Population | Model type | Table pin:rail entries | Model |", "| --- | --- | --- | --- | --- |",
    ]
    lines += [f"| `{ref}` | {'empty socket' if ref in EMPTY_DRAM_SOCKETS else 'factory-fitted'} | `{kind}` | `{entries}` | {result} |" for ref, kind, entries, result in rows]
    lines += [
        "", "## Scope boundary", "",
        "Only unambiguous table columns with a direct model-type mapping are checked. The photographed table's `К581РУ4` column lists pin 9 on A and pin 1 on H. No К581РУ4 appears in the guarded .009 factory IC census; the eight fitted owner-bank devices D84–D91 are К565РУ5Г. The RU5 socket pin 9 carries MA7, so the table's RU4 pin-9 supply must not be applied to that bank. This resolves the fitted-bank interpretation of that column, but does not establish why the drawing retained it or whether a rewired RU4 variant existed. The table's G row is a +12/+5 selector, so `RAIL_G` is intentional rather than a fixed +5 V node. This checks JSON node names, not copper connectivity.", "",
        "The full header in the overlapping original-pixel table tile explicitly prints `555 ИР16` in its +5 pin-16 / ground pin-8 group. The official census calls D41–D43 К555ИР16, the owner D41 photo registration has a seven-contact row, an independent lower-centre owner crop shows marked D42/D43 with seven contacts per side, and the preserved 14-pin device contract assigns supply pins 14/7. This is a confirmed package-width error in the table for those fitted devices. Do not move their supply nets to nonexistent pads 16/8. See `ref/schematics/sheet2-ir16-power-table-conflict.json` for the images and remaining owner continuity check.", "",
    ]
    if missing:
        lines += ["Missing: " + ", ".join(missing), ""]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Sheet-2 power table: {fitted_count} fitted ICs, {empty_count} empty sockets, {count} endpoints, missing={len(missing)}")
    return int(bool(missing))


if __name__ == "__main__":
    raise SystemExit(main())
