#!/usr/bin/env python3
"""Compare the exact .009 sheet-1 IC power table with board JSON rails."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "kicad/juku.board.json"
REPORT = ROOT / "docs/sheet1-power-table-audit.md"
SOURCE = "ref/photos/dgsh5-109-009-e3/PXL_20260718_101827714.jpg"

# The photographed sheet-1 table, rows +5 A / +12 B / -12 C / ground.
# Functional input ties and D1's separate derived -5 V supply are outside
# this table. D104 pin16 is separately held because the table's +12 cell is
# blank although the preserved К170УП2 device sheet calls it +12 V supply.
PIN_RAILS = {
    "CPU8080": (("P5V", "20"), ("P12V", "28"), ("GND", "2")),
    "PPI8255": (("P5V", "26"), ("GND", "7")),
    "USART8251": (("P5V", "26"), ("GND", "4")),
    "PIC8259": (("P5V", "28"), ("GND", "14")),
    "SYS8238": (("P5V", "28"), ("GND", "14")),
    "EPROM8K": (("P5V", "1"), ("P5V", "26"), ("P5V", "27"), ("P5V", "28"), ("GND", "14")),
    "BUF8286": (("P5V", "20"), ("GND", "10")),
    "VABUS": (("P5V", "20"), ("GND", "10")),
    "BUF8287": (("P5V", "20"), ("GND", "10")),
    "WAIT_PROM": (("P5V", "16"), ("GND", "8")),
    "DEC_PROM": (("P5V", "16"), ("GND", "8")),
    "RE3_PROM": (("P5V", "16"), ("GND", "8")),
    "RE3_PROM_092": (("P5V", "16"), ("GND", "8")),
    "IO_DEC138": (("P5V", "16"), ("GND", "8")),
    "UP2": (("P5V", "15"), ("GND", "8")),
    "LA18": (("P5V", "8"), ("GND", "4")),
    "AP2": (("P12V", "8"), ("M12V", "5"), ("GND", "4")),
}


def main() -> int:
    board = json.loads(BOARD.read_text(encoding="utf-8"))
    nodes = {name: {tuple(node) for node in net["nodes"]} for name, net in board["nets"].items()}
    rows = []
    missing = []
    count = 0
    for chip in board["chips"]:
        expected = PIN_RAILS.get(chip["type"])
        if expected is None:
            continue
        ref = chip["ref"]
        gaps = [f"{ref}.{pin} → {rail}" for rail, pin in expected if (ref, pin) not in nodes[rail]]
        missing.extend(gaps)
        count += len(expected)
        rows.append((ref, chip["type"], ", ".join(f"{pin}:{rail}" for rail, pin in expected), "PASS" if not gaps else "FAIL"))
    lines = [
        "# Exact .009 sheet-1 IC power-table audit", "",
        f"Source: `{SOURCE}`; original pixels `(0,2050)-(2350,3150)`.", "",
        f"Result: **{'PASS' if not missing else 'FAIL'}** for the table's populated cells — {len(rows)} ICs, {count} audited rail endpoints, {len(missing)} missing model endpoints. D104.16 is a separate device-contract conflict outside this pass.", "",
        "## Command", "", "```sh", "python3 scripts/check_sheet1_power_table.py", "```", "",
        "| Ref | Model type | Table pin:rail entries | Model |", "| --- | --- | --- | --- |",
    ]
    lines += [f"| `{ref}` | `{kind}` | `{entries}` | {result} |" for ref, kind, entries, result in rows]
    lines += ["", "## Scope boundary", "",
        "The script compares hard-coded table transcriptions with board JSON nodes",
        "for every chip whose model type is listed in its `PIN_RAILS` map. It does",
        "not enforce a fixed reference census: a removed chip or an unmapped type",
        "can disappear from the report without causing failure. Physical population",
        "is not checked.",
        "The source image is cited for the transcription; this script neither",
        "reads its pixels nor checks its hash.", "", "The table's 170АП2 column gives +12 V pin8, −12 V pin5, and ground pin4. The separate УП2 column gives +5 V pin15 and ground pin8 but leaves its +12 V cell blank. The preserved К170УП2 device sheet calls D104.16 a +12 V supply. That physical rail remains open in `ref/schematics/d104-pin16-rail-conflict.json`; this table check does not assign it. These results check logical node names, not copper connectivity, PPI footprint orientation, or the rest of the .009 sheets.", ""]
    if missing:
        lines += ["Missing: " + ", ".join(missing), ""]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Sheet-1 power table: {len(rows)} ICs, {count} endpoints, missing={len(missing)}")
    return int(bool(missing))


if __name__ == "__main__":
    raise SystemExit(main())
