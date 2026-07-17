#!/usr/bin/python3
"""Guard X3 cable landings and the sheet-1 triple D104 receiver."""
from __future__ import annotations

import json
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "kicad/juku.kicad_pcb"
SPEC = ROOT / "kicad/juku.board.json"
SIGNALS = {22: "S_OC", 23: "S_TTL", 24: "S_SIN", 25: "S_CTS", 26: "S_DSR",
           29: "S_SOUT", 30: "S_RTS", 31: "S_DTP", 32: "S_OC"}


def mm(value: int) -> float:
    return pcbnew.ToMM(value)


def main() -> int:
    board = pcbnew.LoadBoard(str(BOARD))
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    failures: list[str] = []
    if board.FindFootprintByReference("X3") is not None:
        failures.append("off-board X3 still has a PCB footprint")
    for number in range(21, 33):
        refdes = f"A{number}"
        footprint = board.FindFootprintByReference(refdes)
        pad = footprint.FindPadByNumber("1") if footprint else None
        if pad is None:
            failures.append(f"{refdes}.1 is missing")
            continue
        position = pad.GetPosition()
        expected_x = 173.7 + (number - 21) * 2.54
        if abs(mm(position.x) - expected_x) > 0.002 or abs(mm(position.y) - 15.2) > 0.002:
            failures.append(f"{refdes}.1 has wrong position")
        net = SIGNALS.get(number, f"X3_HARNESS_{number - 20}")
        if pad.GetNetname() != net:
            failures.append(f"{refdes}.1 net {pad.GetNetname()!r} != {net!r}")
        nodes = {tuple(node) for node in spec["nets"][net]["nodes"]}
        if ("X3", str(number - 20)) not in nodes:
            failures.append(f"{net} lacks X3.{number - 20}")
    for net in ("X3_HARNESS_7", "X3_HARNESS_8"):
        record = spec["nets"][net]
        if record.get("intentional_harness_only") is not True or len(record["nodes"]) != 2:
            failures.append(f"{net} is not a two-end intentional cable-only contact")

    d104 = board.FindFootprintByReference("D104")
    expected_d104 = {"4": "S_SIN", "13": "SER_RXD", "5": "S_CTS",
                     "12": "SER_CTS_N", "6": "S_DSR", "11": "SER_DSR_N",
                     "8": "GND", "15": "P5V"}
    for pin, net in expected_d104.items():
        pad = d104.FindPadByNumber(pin) if d104 else None
        if pad is None or pad.GetNetname() != net:
            failures.append(f"D104.{pin} is not assigned to {net}")
    d11 = board.FindFootprintByReference("D11")
    for pin, net in {"17": "SER_CTS_N", "22": "SER_DSR_N"}.items():
        pad = d11.FindPadByNumber(pin) if d11 else None
        if pad is None or pad.GetNetname() != net:
            failures.append(f"D11.{pin} is not assigned to {net}")
    r104 = board.FindFootprintByReference("R104")
    for pin, net in {"1": "X3_HARNESS_1", "2": "P5V"}.items():
        pad = r104.FindPadByNumber(pin) if r104 else None
        if pad is None or pad.GetNetname() != net:
            failures.append(f"R104.{pin} is not assigned to {net}")
    if r104 is not None and r104.GetValue() != "120":
        failures.append("R104 value is not 120 ohms")
    for refdes, expected in {
        "R18": {"1": "S_OC", "2": "SER_TXD"},
        "R30": {"1": "S_OC", "2": "GND"},
    }.items():
        footprint = board.FindFootprintByReference(refdes)
        for pin, net in expected.items():
            pad = footprint.FindPadByNumber(pin) if footprint else None
            if pad is None or pad.GetNetname() != net:
                failures.append(f"{refdes}.{pin} is not assigned to {net}")
        if footprint is not None and footprint.GetValue() != "33к":
            failures.append(f"{refdes} value is not the native 33к literal")
    for refdes, expected in {
        "D3": {"9": "SER_TXD", "8": "SER_TXD_INV"},
        "D12": {"1": "SER_TXD_INV", "2": "SER_TXD_INV", "3": "S_OC"},
    }.items():
        footprint = board.FindFootprintByReference(refdes)
        for pin, net in expected.items():
            pad = footprint.FindPadByNumber(pin) if footprint else None
            if pad is None or pad.GetNetname() != net:
                failures.append(f"{refdes}.{pin} is not assigned to {net}")

    if failures:
        for failure in failures:
            print("FAIL:", failure)
        return 1
    print("X3 LANDINGS: PASS — A21..A32 harness and D104 triple receiver")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
