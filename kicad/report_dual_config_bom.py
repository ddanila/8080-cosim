#!/usr/bin/env python3
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOARD_JSON = ROOT / "kicad" / "juku.board.json"
DEFAULT_MD = ROOT / "docs" / "replica-dual-config-bom.md"
DEFAULT_CSV = ROOT / "docs" / "replica-dual-config-bom.csv"


AUTHENTIC_MARK = {
    "CPU8080": "КР580ИК80А",
    "SYS8238": "КР580ВК38",
    "USART8251": "КР580ВВ51А",
    "PPI8255": "КР580ВВ55А",
    "PIT8253": "КР580ВИ53",
    "PIC8259": "КР580ВН59",
    "BUF8286": "КР580ВА86",
    "BUF8287": "КР580ВА87",
    "VABUS": "КР580ВА87",
    "IR82": "КР580ИР82",
    "RU5": "К565РУ5Г / 565РУ5Г",
    "EPROM8K": "2764/M2764-class EPROM in .009 build; К573РФ5 on .006 BOM",
    "DEC_PROM": "КР556РТ4А",
    "RE3_PROM": "К155РЕ3",
    "RE3_PROM_113": "К155РЕ3",
    "VG93_FDC": "КР1818ВГ93",
    "IO_DEC138": "К555ИД7",
    "RASCAS_DEC": "К531ИД7",
    "IE7_CTR": "К555ИЕ7",
    "KP14_MUX": "К531/К555КП14",
    "LA1_GATE": "К531ЛА1",
    "LA3_GATE": "К555/КР1533ЛА3",
    "LA12_GATE": "К531ЛА12",
    "LN1_INV": "К531ЛН1",
    "LN1_OSC": "К531ЛН1",
    "LN1_DUAL": "К531ЛН1",
    "LN2": "К561ЛН2",
    "CLK_PHASE": "К155ЛН5",
    "AG3_ONESHOT": "К155/КМ555АГ3",
    "IE10_CTR": "К555ИЕ10",
    "CT16_CTR": "КР531ИЕ17",
    "IR16": "К155ИР16",
    "TL2": "К155ТЛ2",
    "LA18": "К155ЛА18",
    "LE4": "К555ЛЕ4",
    "LP5_XOR": "К155ЛП5",
    "AP2": "К170АП2",
    "UP2": "К170УП2",
    "C_KM": "КМ ceramic capacitor",
    "C_ELEC": "radial electrolytic",
    "R_AXIAL": "axial resistor",
    "R_TRIM": "СП3-22б trimmer",
    "C_TRIM": "trimmer capacitor",
    "D_DIODE": "Soviet diode/zener per value",
    "Q_TO92": "КТ315/КТ972-class transistor per position",
    "L_RADIAL": "radial inductor/choke",
    "XTAL": "РК-171 16 MHz crystal",
    "SW": "switch",
    "SW_DIP6": "DIP switch",
    "EXPANSION_CONN": "СНП59-96 Р-20-2-В",
    "SERIAL_CONN": "СНП59-30-23-В / serial connector",
    "POWER_CONN": "СНО51-30/56х9В-23 power connector",
    "KBD_CONN": "keyboard connector",
    "PAR_CONN": "parallel/interface connector",
    "VIDEO_CONN": "BNC/composite video connector",
    "RF_CONN": "RF connector",
    "JUMPER2": "wire/link",
    "JUMPER3": "wire/link",
    "JUMPER4": "wire/link",
}


FUNCTIONAL_SUBSTITUTE = {
    "CPU8080": "Intel 8080A / compatible 8080 CPU",
    "SYS8238": "8228/8238-class system controller; verify pinout",
    "USART8251": "8251A / 82C51-class USART",
    "PPI8255": "8255A / 82C55 PPI",
    "PIT8253": "8253 or 8254 PIT",
    "PIC8259": "8259A PIC",
    "BUF8286": "Intel 8286 / compatible bus transceiver",
    "BUF8287": "Intel 8287 / compatible bus transceiver",
    "VABUS": "Intel 8287 / compatible bus transceiver",
    "IR82": "8282/8283-class latch; verify polarity/package",
    "RU5": "4164-compatible 64Kx1 DRAM",
    "EPROM8K": "2764 / 27C64 / M2764 EPROM, programmed per ROM split",
    "DEC_PROM": "74S287/82S129-class 256x4 bipolar PROM, programmed",
    "RE3_PROM": "74188/82S23-class 32x8 bipolar PROM, programmed",
    "RE3_PROM_113": "74188/82S23-class 32x8 bipolar PROM, programmed",
    "VG93_FDC": "WD1793-compatible FDC",
    "IO_DEC138": "74LS138 / 74HCT138 decoder",
    "RASCAS_DEC": "74S138/74F138-class fast decoder; verify timing",
    "IE7_CTR": "74LS161/163-class counter; verify exact Soviet pin/timing match",
    "KP14_MUX": "74LS257/258-class quad 2:1 mux; verify OE/polarity",
    "LA1_GATE": "74S/74LS NAND-class gate; verify exact logic section",
    "LA3_GATE": "74LS00 / 74ALS00-class NAND",
    "LA12_GATE": "74S20/74LS20-class NAND; verify section",
    "LN1_INV": "74S04/74LS04-class inverter",
    "LN1_OSC": "74S04/74LS04-class inverter; oscillator section timing matters",
    "LN1_DUAL": "74S04/74LS04-class inverter",
    "LN2": "CD4049/К561ЛН2-class CMOS inverter; verify role",
    "CLK_PHASE": "74LS04/74LS14-class inverter; verify phase/timing use",
    "AG3_ONESHOT": "74LS123/74123-class one-shot; verify RC timing",
    "IE10_CTR": "74LS193/191-class counter; verify exact pinout",
    "CT16_CTR": "74F/74S163-class fast counter; verify timing",
    "IR16": "74295/74LS295-class shift register; verify pinout",
    "TL2": "74LS13 Schmitt NAND-class gate",
    "LA18": "open-collector NAND/driver; verify output topology",
    "LE4": "74LS02 NOR-class gate",
    "LP5_XOR": "74LS86 XOR-class gate",
    "AP2": "RS-232/line-driver substitute required; verify +/-12 V interface",
    "UP2": "RS-232/line-receiver substitute required; verify +/-12 V interface",
    "C_KM": "modern ceramic capacitor with matching value/voltage/lead spacing",
    "C_ELEC": "modern radial electrolytic with matching value/voltage/polarity",
    "R_AXIAL": "modern axial resistor, matching value and power rating",
    "R_TRIM": "modern vertical trimmer matching footprint/value",
    "C_TRIM": "modern trimmer capacitor matching footprint/value",
    "D_DIODE": "modern diode/zener matching value and power",
    "Q_TO92": "modern transistor selected per exact circuit role",
    "L_RADIAL": "modern radial choke/inductor after value confirmation",
    "XTAL": "16 MHz HC-49/metal-can crystal matching footprint/load",
}


TYPE_NOTES = {
    "DEC_PROM": "Contents remain a PROM-truth item: prefer Baltijets disk files or hardware dump before programming.",
    "RE3_PROM": "Timing/window PROM contents remain dump/reconstruction-gated.",
    "RE3_PROM_113": "FDC-revision timing/window PROM contents remain dump/reconstruction-gated.",
    "EPROM8K": "Only D15/D16 are populated in the .009 functional build; D17-D22 are expansion/empty sockets.",
    "RU5": "Only D60-D67 are populated for the current 64 KB .009 functional build; D68-D91 are empty expansion sockets.",
    "VG93_FDC": "Western WD1793 is the intended functional drop-in.",
}


PROGRAM_TYPES = {"DEC_PROM", "RE3_PROM", "RE3_PROM_113", "EPROM8K"}
EMPTY_SOCKET_TYPES = {"RU5", "EPROM8K"}
MECHANICAL_TYPES = {
    "EXPANSION_CONN",
    "SERIAL_CONN",
    "POWER_CONN",
    "KBD_CONN",
    "PAR_CONN",
    "VIDEO_CONN",
    "RF_CONN",
    "SW",
    "SW_DIP6",
    "JUMPER2",
    "JUMPER3",
    "JUMPER4",
}


def natural_key(ref):
    prefix = "".join(ch for ch in ref if not ch.isdigit())
    digits = "".join(ch for ch in ref if ch.isdigit())
    return (prefix, int(digits or 0), ref)


def value_of(chip):
    return str(chip.get("value") or "").strip()


def populated(chip):
    typ = chip["type"]
    if typ in EMPTY_SOCKET_TYPES:
        text = " ".join(str(v) for v in chip.get("prov", {}).values()).lower()
        return "populated" in text and "unpopulated" not in text
    return True


def group_key(chip):
    typ = chip["type"]
    value = value_of(chip)
    if typ in {"R_AXIAL", "C_KM", "C_ELEC", "D_DIODE", "XTAL", "R_TRIM", "C_TRIM"}:
        return typ, value
    return typ, ""


def action_for(typ, pop_count, socket_count):
    if typ in PROGRAM_TYPES:
        if pop_count == 0:
            return "leave-empty"
        return "program/dump"
    if typ in MECHANICAL_TYPES:
        return "mechanical-review"
    if typ in {"AP2", "UP2", "Q_TO92", "L_RADIAL"}:
        return "circuit-review"
    if typ in EMPTY_SOCKET_TYPES and pop_count < socket_count:
        return "source-populated-now"
    return "source-now"


def row_action(typ, value, pop_count, socket_count):
    if typ in {"R_AXIAL", "C_KM", "C_ELEC", "D_DIODE", "R_TRIM", "C_TRIM"} and not value:
        return "circuit-review"
    return action_for(typ, pop_count, socket_count)


def format_refs(refs, limit=18):
    refs = sorted(refs, key=natural_key)
    if len(refs) <= limit:
        return ", ".join(refs)
    shown = ", ".join(refs[:limit])
    return f"{shown}, ... (+{len(refs) - limit})"


def table_row(values):
    return "| " + " | ".join(str(value).replace("|", "/") if value not in (None, "") else "-" for value in values) + " |"


def build_rows(board_json):
    spec = json.loads(board_json.read_text())
    groups = defaultdict(list)
    for chip in spec["chips"]:
        groups[group_key(chip)].append(chip)

    rows = []
    for (typ, value), chips in groups.items():
        refs = [chip["ref"] for chip in chips]
        pop_refs = [chip["ref"] for chip in chips if populated(chip)]
        authentic = AUTHENTIC_MARK.get(typ, typ)
        if value:
            authentic = f"{authentic} {value}"
        rows.append({
            "type": typ,
            "value": value,
            "authentic_part": authentic,
            "functional_substitute": FUNCTIONAL_SUBSTITUTE.get(typ, "select exact substitute after circuit review"),
            "board_positions": len(refs),
            "populate_now": len(pop_refs),
            "leave_empty": len(refs) - len(pop_refs),
            "action": row_action(typ, value, len(pop_refs), len(refs)),
            "refs": format_refs(refs),
            "populated_refs": format_refs(pop_refs) if pop_refs else "",
            "notes": TYPE_NOTES.get(typ, ""),
        })

    return sorted(rows, key=lambda row: (row["action"], row["type"], row["value"]))


def write_csv(path, rows):
    fields = [
        "action",
        "type",
        "value",
        "authentic_part",
        "functional_substitute",
        "board_positions",
        "populate_now",
        "leave_empty",
        "refs",
        "populated_refs",
        "notes",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path, rows, board_json, csv_path):
    socket_positions = sum(row["board_positions"] for row in rows)
    populate_now = sum(row["populate_now"] for row in rows)
    leave_empty = sum(row["leave_empty"] for row in rows)
    by_action = defaultdict(int)
    for row in rows:
        by_action[row["action"]] += row["populate_now"] if row["populate_now"] else row["board_positions"]
    if leave_empty:
        by_action["leave-empty"] += leave_empty

    lines = [
        "# Replica dual-config BOM",
        "",
        f"Source: `{board_json.relative_to(ROOT)}`",
        f"CSV: `{csv_path.relative_to(ROOT)}`",
        "Sourcing gate: `docs/replica-sourcing-readiness.md`",
        "",
        "This is the first sourcing BOM split required by WS-E: an authentic Soviet",
        "part column and a functional substitute column. It is generated from the",
        "current KiCad board source and keeps the .009 populated-vs-expansion-socket",
        "distinction explicit.",
        "",
        "Run `python3 kicad/report_replica_sourcing_readiness.py` after regenerating this",
        "BOM to refresh the source-early, programming-gated, and review-before-buying",
        "readiness report.",
        "",
        "## Summary",
        "",
        f"- Board component positions: {socket_positions}",
        f"- Populate for current functional .009 build: {populate_now}",
        f"- Leave empty for expansion/authentic completeness: {leave_empty}",
        f"- Unique BOM lines: {len(rows)}",
        "",
        "## Action Totals",
        "",
        "| Action | Count basis |",
        "| --- | ---: |",
    ]
    for action in sorted(by_action):
        lines.append(table_row([action, by_action[action]]))

    lines.extend([
        "",
        "## BOM Lines",
        "",
        "| Action | Type | Authentic part | Functional substitute | Positions | Populate now | Empty | Refs | Notes |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | --- | --- |",
    ])
    for row in rows:
        lines.append(table_row([
            row["action"],
            row["type"] + (f" {row['value']}" if row["value"] else ""),
            row["authentic_part"],
            row["functional_substitute"],
            row["board_positions"],
            row["populate_now"],
            row["leave_empty"],
            row["refs"],
            row["notes"],
        ]))

    lines.extend([
        "",
        "## Use",
        "",
        "- `source-now` and `source-populated-now` rows are the functional shopping baseline.",
        "- `program/dump` rows need firmware/PROM contents before they are build-ready.",
        "- `leave-empty` rows are sockets present on the board but not populated for the current .009 functional build.",
        "- `mechanical-review` and `circuit-review` rows need exact part drawing, footprint, or circuit-role confirmation before order.",
        "",
    ])
    path.write_text("\n".join(lines))


def main():
    board_json = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT_BOARD_JSON
    md_path = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else DEFAULT_MD
    csv_path = Path(sys.argv[3]).resolve() if len(sys.argv) > 3 else DEFAULT_CSV
    rows = build_rows(board_json)
    write_csv(csv_path, rows)
    write_markdown(md_path, rows, board_json, csv_path)
    print(f"Wrote {md_path.relative_to(ROOT)}")
    print(f"Wrote {csv_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
