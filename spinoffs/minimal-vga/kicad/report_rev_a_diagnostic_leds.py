#!/usr/bin/env python3
import csv
import sys
from pathlib import Path

import pcbnew


VCC_VOLTS = 5.0
RED_LED_FORWARD_VOLTS = 2.0
EXPECTED_RESISTANCE_OHMS = 2200
MAX_LED_CURRENT_MA = 2.0
MAX_TOTAL_LED_CURRENT_MA = 12.0

LED_ROWS = (
    {
        "name": "+5V present",
        "led": "D2",
        "resistor": "R24",
        "source": "VCC",
        "anode": "LED_PWR_A",
        "cathode": "GND",
        "sense": "always-on fused +5V indicator",
        "driver": "supply",
    },
    {
        "name": "PWR_OK",
        "led": "D3",
        "resistor": "R25",
        "source": "PWR_OK",
        "anode": "LED_PWR_OK_A",
        "cathode": "GND",
        "sense": "PWR_OK high sources LED current",
        "driver": "logic-source",
    },
    {
        "name": "CLK",
        "led": "D4",
        "resistor": "R26",
        "source": "CLK",
        "anode": "LED_CLK_A",
        "cathode": "GND",
        "sense": "clock high pulses source LED current",
        "driver": "logic-source",
    },
    {
        "name": "RESET_N",
        "led": "D5",
        "resistor": "R27",
        "source": "RESET_N",
        "anode": "LED_RESET_A",
        "cathode": "GND",
        "sense": "RESET_N high sources LED current after reset releases",
        "driver": "logic-source",
    },
    {
        "name": "M1_N",
        "led": "D6",
        "resistor": "R28",
        "source": "VCC",
        "anode": "LED_M1_A",
        "cathode": "M1_N",
        "sense": "active-low instruction-fetch indicator sinks current",
        "driver": "logic-sink",
    },
    {
        "name": "RFSH_N",
        "led": "D7",
        "resistor": "R29",
        "source": "VCC",
        "anode": "LED_RFSH_A",
        "cathode": "RFSH_N",
        "sense": "active-low refresh indicator sinks current",
        "driver": "logic-sink",
    },
)


def footprint_by_ref(board):
    return {fp.GetReference().upper(): fp for fp in board.Footprints()}


def pad_net(fp, number):
    pad = fp.FindPadByNumber(str(number)) if fp else None
    return pad.GetNetname() if pad else ""


def footprint_name(fp):
    return str(fp.GetFPID().GetLibItemName()) if fp else "missing"


def read_bom_rows(path):
    rows = []
    with path.open(newline="") as handle:
        for row in csv.DictReader(handle):
            designators = row.get("Designator", "")
            expanded = []
            for token in designators.replace(",", " ").split():
                if "-" in token and token[0].isalpha():
                    prefix = token[0]
                    start, end = token[1:].split("-", 1)
                    if end.startswith(prefix):
                        end = end[1:]
                    expanded.extend(f"{prefix}{idx}" for idx in range(int(start), int(end) + 1))
                elif token:
                    expanded.append(token)
            row["ExpandedDesignators"] = expanded
            rows.append(row)
    return rows


def bom_row_for(rows, ref):
    return next((row for row in rows if ref in row["ExpandedDesignators"]), None)


def cpn(row):
    if not row:
        return ""
    return row.get("JLCPCB/LCSC CPN") or row.get("LCSC") or row.get("CPN") or ""


def resistor_ohms_from_value(value):
    value = value.strip().lower().replace(" ", "")
    if value.endswith("k"):
        return int(float(value[:-1]) * 1000)
    if "k" in value:
        left, right = value.split("k", 1)
        return int(float(f"{left}.{right}") * 1000)
    if value.endswith("r"):
        return int(float(value[:-1]))
    try:
        return int(float(value))
    except ValueError:
        return None


def led_current_ma(resistance_ohms):
    return (VCC_VOLTS - RED_LED_FORWARD_VOLTS) / resistance_ohms * 1000.0


def build_report(board_path, bom_path):
    board = pcbnew.LoadBoard(str(board_path))
    fps = footprint_by_ref(board)
    bom_rows = read_bom_rows(Path(bom_path))
    failures = []
    rows = []
    total_current_ma = 0.0
    max_current_ma = 0.0
    logic_loaded = []

    for policy in LED_ROWS:
        led = fps.get(policy["led"])
        resistor = fps.get(policy["resistor"])
        led_row = bom_row_for(bom_rows, policy["led"])
        resistor_row = bom_row_for(bom_rows, policy["resistor"])
        resistor_ohms = resistor_ohms_from_value(resistor.GetValue()) if resistor else None
        current_ma = led_current_ma(resistor_ohms) if resistor_ohms else 0.0
        total_current_ma += current_ma
        max_current_ma = max(max_current_ma, current_ma)

        checks = [
            (resistor is not None, f"{policy['resistor']} footprint missing"),
            (led is not None, f"{policy['led']} footprint missing"),
            (pad_net(resistor, 1) == policy["source"], f"{policy['resistor']}.1 is not on {policy['source']}"),
            (pad_net(resistor, 2) == policy["anode"], f"{policy['resistor']}.2 is not on {policy['anode']}"),
            (pad_net(led, 2) == policy["anode"], f"{policy['led']}.2 is not on {policy['anode']}"),
            (pad_net(led, 1) == policy["cathode"], f"{policy['led']}.1 is not on {policy['cathode']}"),
            (resistor_ohms == EXPECTED_RESISTANCE_OHMS, f"{policy['resistor']} is not {EXPECTED_RESISTANCE_OHMS} ohm"),
            (current_ma <= MAX_LED_CURRENT_MA, f"{policy['led']} current is above {MAX_LED_CURRENT_MA:.1f} mA"),
            (cpn(led_row) == "C99772", f"{policy['led']} BOM CPN is not C99772"),
            (cpn(resistor_row) == "C3454390", f"{policy['resistor']} BOM CPN is not C3454390"),
        ]
        row_failures = [message for passed, message in checks if not passed]
        failures.extend(row_failures)
        if policy["driver"] != "supply":
            logic_loaded.append(policy["name"])
        rows.append(
            {
                "Signal": policy["name"],
                "LED": policy["led"],
                "Resistor": policy["resistor"],
                "Topology": f"{policy['source']} -> {policy['resistor']} -> {policy['anode']} -> {policy['led']} -> {policy['cathode']}",
                "Current": f"{current_ma:.2f} mA",
                "Driver": policy["driver"],
                "Sense": policy["sense"],
                "Status": "PASS" if not row_failures else "FAIL",
            }
        )

    if total_current_ma > MAX_TOTAL_LED_CURRENT_MA:
        failures.append(
            f"worst-case LED current {total_current_ma:.2f} mA exceeds {MAX_TOTAL_LED_CURRENT_MA:.2f} mA budget"
        )

    status = "READY" if not failures else "NOT READY"
    lines = [
        "# Rev A diagnostic LED readiness",
        "",
        f"Board: `{board_path}`",
        f"BOM: `{bom_path}`",
        f"Status: **{status}**",
        "",
        "This report checks the first-pass diagnostic LED bank for connectivity,",
        "selected BOM rows, and current loading. The Rev A baseline intentionally",
        "uses conservative 2.2k current limiting so debug LEDs do not dominate",
        "the +5V budget or heavily load Z80/control signals.",
        "",
        "## Summary",
        "",
        f"- Diagnostic LEDs checked: {len(LED_ROWS)}",
        f"- Expected resistor value: {EXPECTED_RESISTANCE_OHMS} ohm",
        f"- Estimated current per lit LED: {max_current_ma:.2f} mA",
        f"- Worst-case all-lit LED current: {total_current_ma:.2f} mA",
        f"- Per-LED current limit: {MAX_LED_CURRENT_MA:.2f} mA",
        f"- Total LED current budget: {MAX_TOTAL_LED_CURRENT_MA:.2f} mA",
        f"- Logic-loaded indicators: {', '.join(logic_loaded)}",
        f"- Diagnostic LED failures: {len(failures)}",
        "",
        "## Rows",
        "",
        "| Signal | LED | Resistor | Topology | Current | Driver | Sense | Status |",
        "| --- | --- | --- | --- | ---: | --- | --- | --- |",
    ]
    for row in rows:
        safe = {key: str(value).replace("|", "/") for key, value in row.items()}
        lines.append(
            "| {Signal} | {LED} | {Resistor} | {Topology} | {Current} | {Driver} | {Sense} | {Status} |".format(
                **safe
            )
        )
    if failures:
        lines.extend(["", "## Failures", ""])
        lines.extend(f"- {failure}" for failure in failures)
    lines.append("")
    return "\n".join(lines), not failures


def main():
    board_path = Path(sys.argv[1] if len(sys.argv) > 1 else "spinoffs/minimal-vga/kicad/rev-a-physical.kicad_pcb")
    bom_path = Path(sys.argv[2] if len(sys.argv) > 2 else "spinoffs/minimal-vga/kicad/rev-a.bom.csv")
    out_dir = Path(sys.argv[3] if len(sys.argv) > 3 else "fab/minimal-vga")
    report, ready = build_report(board_path, bom_path)
    report_path = out_dir / "diagnostic-led-readiness.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report)
    print(report)
    print(f"Wrote {report_path}")
    return 0 if ready else 3


if __name__ == "__main__":
    raise SystemExit(main())
