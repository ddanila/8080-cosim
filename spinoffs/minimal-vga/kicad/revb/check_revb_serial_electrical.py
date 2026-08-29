#!/usr/bin/env python3
"""R5.S2: validate baud selection and the protected 3.3/5 V USB-TTL boundary."""
from __future__ import annotations

import json
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent


def refs(card: str):
    data = json.loads((HERE / f"{card}.board.json").read_text())
    return {part["ref"]: part for part in data["chips"]}


def expect(errors, actual, wanted, label):
    if actual != wanted:
        errors.append(f"{label}: {actual!r} != {wanted!r}")


def main() -> int:
    errors: list[str] = []
    cfg = json.loads((HERE / "serial-electrical.json").read_text())
    io = refs("io")
    bp = refs("backplane")

    osc_hz = cfg["oscillator"]["frequency_hz"]
    over = cfg["baud"]["oversample"]
    for name in ("primary", "fallback"):
        mode = cfg["baud"][name]
        expect(errors, osc_hz // mode["divider"], mode["clock_hz"], f"{name} divider")
        expect(errors, mode["clock_hz"] // over, mode["baud"], f"{name} x{over} baud")

    expect(errors, io["U3"]["pins"],
           {"1": "OSC_EN_NC", "4": "GND", "5": "BAUD_MASTER", "8": "VCC5"},
           "4.9152 MHz oscillator pinout")
    expect(errors, io["U7"]["pins"]["6"], "BAUD_19200", "74HC393 /16 output")
    expect(errors, io["U7"]["pins"]["11"], "BAUD_9600", "74HC393 /32 output")
    expect(errors, io["JP_BAUD"]["pins"],
           {"1": "BAUD_19200", "2": "BAUD_DIRECT", "3": "BAUD_9600"},
           "JP_BAUD direct-recovery-rate pinout")
    expect(errors, io["JP_CLK_SRC"]["pins"],
           {"1": "PIT_BAUD", "2": "BAUDCLK", "3": "BAUD_DIRECT"},
           "JP_CLK_SRC PIT/direct pinout")

    expect(errors, bp["J_TTL"]["pins"],
           {"1": "VCC_SENSE", "2": "BOARD_TX", "3": "BOARD_RX", "4": "GND"},
           "J_TTL protected pinout")
    expect(errors, bp["JP_S5"]["pins"],
           {"1": "TX", "2": "CON_TX_SRC", "3": "CON_RX_DRIVE", "4": "RX"},
           "JP_S5 protected paths")
    expect(errors, bp["R_TX_TOP"]["pins"], {"1": "CON_TX_5V", "2": "BOARD_TX"},
           "TX top resistor")
    expect(errors, bp["R_TX_BOT"]["pins"], {"1": "BOARD_TX", "2": "GND"},
           "TX bottom resistor")
    expect(errors, bp["R_RX_SER"]["pins"], {"1": "BOARD_RX", "2": "CON_RX_BUF"},
           "RX series resistor")
    expect(errors, bp["R_RX_PULL"]["pins"], {"1": "CON_RX_BUF", "2": "VCC5"},
           "RX idle pull-up")
    expect(errors, bp["R_TX_PULL"]["pins"], {"1": "CON_TX_SRC", "2": "VCC5"},
           "isolated board-TX buffer input pull-up")
    expect(errors, bp["R_BUS_RX"]["pins"], {"1": "RX", "2": "VCC5"},
           "isolated 8251 RX bus pull-up")
    expect(errors, bp["R_VSENSE"]["pins"], {"1": "VCC5", "2": "VSENSE_A"},
           "sense resistor")
    expect(errors, bp["D_VSENSE"]["pins"], {"1": "VCC_SENSE", "2": "VSENSE_A"},
           "sense blocking diode (pad 2 anode, pad 1 cathode)")

    # Both used HCT channels are enabled. The two unused inputs are low and their
    # active-low enables are high, as required for defined CMOS inputs at power-up.
    hct = bp["U_CON"]["pins"]
    expect(errors, {p: hct[p] for p in ("1", "4")}, {"1": "GND", "4": "GND"},
           "used HCT enables")
    expect(errors, {p: hct[p] for p in ("9", "10", "12", "13")},
           {"9": "GND", "10": "VCC5", "12": "GND", "13": "VCC5"},
           "unused HCT inputs/enables")

    r = cfg["resistors_ohm"]
    hct_cfg = cfg["buffer"]
    host = cfg["host_3v3_boundary"]
    ratio = r["tx_bottom"] / (r["tx_top"] + r["tx_bottom"])
    tx_high_worst = hct_cfg["voh_min_v"] * ratio
    host_vih = host["rx_vdd_v"] * host["rx_vih_fraction"]
    tx_high_max = hct_cfg["vcc_max_v"] * ratio
    tx_current_ma = hct_cfg["vcc_max_v"] / (r["tx_top"] + r["tx_bottom"]) * 1000
    if tx_high_worst < host_vih:
        errors.append(f"board TX worst high {tx_high_worst:.3f} V < host VIH {host_vih:.3f} V")
    if tx_high_max > host["rx_abs_max_v"]:
        errors.append(f"board TX max {tx_high_max:.3f} V > host absolute max {host['rx_abs_max_v']:.3f} V")
    if tx_current_ma > hct_cfg["source_limit_ma"]:
        errors.append(f"TX divider current {tx_current_ma:.3f} mA exceeds HCT source rating")
    if host["tx_high_min_v"] < hct_cfg["vih_min_v"] or host["tx_low_max_v"] > hct_cfg["vil_max_v"]:
        errors.append("3.3 V host TX levels do not meet HCT receive thresholds")

    if errors:
        print("rev B serial electrical check FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("rev B serial electrical PASS: 19,200/9,600 x16 clocks; "
          f"3.3 V host thresholds pass; board TX={tx_high_worst:.3f}..{tx_high_max:.3f} V; "
          "sense diode blocks host back-power")
    return 0


if __name__ == "__main__":
    sys.exit(main())
