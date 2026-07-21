#!/usr/bin/env python3
"""Generate exact D101 first-half logic and measurement constraints."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "kicad" / "juku.board.json"
DATASHEET = ROOT / "ref" / "datasheets" / "sn74ls253-ti.pdf"
PINOUT = ROOT / "ref" / "datasheets" / "k555kp12-pinout.txt"
D94_IMAGE = ROOT / "ref" / "physical-proms" / "validated" / "d94_092.raw.bin"
REPORT = ROOT / "docs" / "d101-reconstruction-constraints.md"

DATASHEET_SHA256 = "6dac6d83b154c40e39bf772ae3b144c8d5d7a42f7b31ddc49942223d6df6c47a"
D94_SHA256 = "bcf942a87ee70adb1a16cebb7f018cf8f491ea2a74db0b0a5dd7d5c8db8a29e0"

EXPECTED_PIN_NETS = {
    "1": "D101_OE0_BOUNDARY",
    "2": "FDC_EARLY_SEL",
    "3": "D101_D03_BOUNDARY",
    "4": "D101_D02_R92_R99",
    "5": "D101_D01_BOUNDARY",
    "6": "D101_D00_BOUNDARY",
    "7": "D94_A4_D101_Q0",
    "8": "GND",
    "9": "FDC_PRECOMP_WRDATA",
    "10": "PRECOMP_TAP_1",
    "11": "PRECOMP_TAP_2",
    "12": "PRECOMP_TAP_3",
    "13": "GND",
    "14": "FDC_LATE_SEL",
    "15": "GND",
    "16": "P5V",
}

PIN_ROLES = {
    "1": "/OE0",
    "2": "select B / EARLY",
    "3": "D03",
    "4": "D02",
    "5": "D01",
    "6": "D00",
    "7": "Q0 / D94 A4",
    "8": "GND",
    "9": "Q1 / precomp output",
    "10": "D10 / tap 1",
    "11": "D11 / tap 2",
    "12": "D12 / tap 3",
    "13": "D13 / GND",
    "14": "select A / LATE",
    "15": "/OE1 / GND",
    "16": "+5 V",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def net_for_pin(board: dict, ref: str, pin: str) -> str | None:
    for name, net in board["nets"].items():
        if [ref, pin] in net.get("nodes", []):
            return name
    return None


def nodes(board: dict, net: str) -> set[tuple[str, str]]:
    return {tuple(node) for node in board["nets"].get(net, {}).get("nodes", [])}


def chip(board: dict, ref: str) -> dict:
    for item in board["chips"]:
        if item.get("ref") == ref:
            return item
    raise SystemExit(f"missing chip {ref}")


def table_row(values: list[object]) -> str:
    return "| " + " | ".join(str(value).replace("|", "/") for value in values) + " |"


def main() -> int:
    board = json.loads(BOARD.read_text(encoding="utf-8"))
    image = D94_IMAGE.read_bytes()
    pinout = read(PINOUT)
    devices = read(ROOT / "hdl" / "devices.v")
    tb = read(ROOT / "hdl" / "sim" / "kp12_mux_tb.v")

    pin_nets = {pin: net_for_pin(board, "D101", pin) for pin in EXPECTED_PIN_NETS}
    pin_map_ok = pin_nets == EXPECTED_PIN_NETS
    singleton_boundaries_ok = all(
        nodes(board, net) == {("D101", pin)}
        for pin, net in {
            "1": "D101_OE0_BOUNDARY",
            "3": "D101_D03_BOUNDARY",
            "5": "D101_D01_BOUNDARY",
            "6": "D101_D00_BOUNDARY",
        }.items()
    )
    closed_local_nodes_ok = (
        nodes(board, "D94_A4_D101_Q0") == {("D94", "14"), ("D101", "7")}
        and nodes(board, "D101_D02_R92_R99")
        == {("D101", "4"), ("R92", "1"), ("R99", "2")}
        and nodes(board, "FDC_EARLY_SEL") == {("D93", "17"), ("D101", "2")}
        and nodes(board, "FDC_LATE_SEL") == {("D93", "18"), ("D101", "14")}
    )
    resistor_values_ok = chip(board, "R92").get("value") == "1,3к" and chip(board, "R99").get("value") == "4,7к"
    artifact_ok = sha256(DATASHEET) == DATASHEET_SHA256 and sha256(D94_IMAGE) == D94_SHA256 and len(image) == 32
    pinout_ok = all(
        marker in pinout
        for marker in (
            "1   /OE0",
            "2   select B",
            "14  select A",
            "D101.7 (Q0) <-> D94.14 (A4)",
            "D101.1 /OE0 and data inputs D101.3/.5/.6 remain boundary nets",
        )
    )
    hdl_ok = all(
        marker in devices
        for marker in (
            "module kp12_mux",
            "wire [1:0] sel = {a1, a0};",
            "assign q0 = oe0_n ? 1'bz : d0[sel];",
        )
    ) and all(marker in tb for marker in ("q0 !== d0[sel]", "q0 !== 1'bz", "KP12-MUX: PASS"))

    register3_rows: list[list[object]] = []
    d94_logic_ok = True
    for a4 in (0, 1):
        for a3 in (0, 1):
            for a2 in (0, 1):
                address = (a4 << 4) | (a3 << 3) | (a2 << 2) | 0b11
                raw = image[address]
                d0 = not bool(raw & 0x01)
                d2 = not bool(raw & 0x04)
                d3 = not bool(raw & 0x08)
                expected = (
                    (d0 and not d2 and not d3)
                    if a4 == 0
                    else (not d0 and d2 == bool(a3 and not a2) and d3 == bool((not a3) and a2))
                )
                d94_logic_ok &= expected
                register3_rows.append(
                    [a4, a3, a2, f"`{address:02X}`", f"`{raw:02X}`", "yes" if d0 else "no", "yes" if d2 else "no", "yes" if d3 else "no"]
                )

    checks = [
        ("TI SN74LS253 PDF and validated D94 image hashes match", artifact_ok),
        ("D101 all-pin board mapping matches the measured/source model", pin_map_ok),
        ("D101 /OE0, D03, D01, and D00 remain honest singleton boundaries", singleton_boundaries_ok),
        ("D101 Q0, D02 ladder, and EARLY/LATE selects preserve exact closed endpoints", closed_local_nodes_ok),
        ("R92/R99 physical values remain 1.3 kΩ / 4.7 kΩ", resistor_values_ok),
        ("Local pinout interpretation separates closed and open D101 pins", pinout_ok),
        ("HDL and exhaustive test preserve select order and high-impedance disable", hdl_ok),
        ("Physical D94 register-3 rows obey the exact A4 steering contract", d94_logic_ok),
    ]
    passed = all(ok for _, ok in checks)
    status = "D101 FIRST HALF LOGIC-CONSTRAINED / FOUR PINS MEASUREMENT-GATED" if passed else "D101 CONSTRAINT REPORT FAILED"

    lines = [
        "# D101 first-half reconstruction constraints",
        "",
        f"Status: **{status}**",
        "",
        "D101 is the target-board К555КП12 / SN74LS253 dual 4:1 multiplexer.",
        "Its Q1 write-precompensation half is source-closed. This report narrows",
        "the separate Q0 half that drives D94 A4 without inventing the four",
        "remaining conductors.",
        "",
        "## Command",
        "",
        "```sh",
        "python3 scripts/report_d101_reconstruction_constraints.py",
        "sync/kp12_check.sh",
        "```",
        "",
        "## Evidence checks",
        "",
        "| Check | Result |",
        "| --- | --- |",
    ]
    lines.extend(table_row([name, "PASS" if ok else "FAIL"]) for name, ok in checks)
    lines.extend(
        [
            "",
            "## Exact pin disposition",
            "",
            "The TI truth table calls physical pin 2 select `B` and pin 14 select",
            "`A`. Repository signal names `A1`/`A0` preserve the same ordering.",
            "",
            "| Pin | Device role | Board net | State |",
            "| ---: | --- | --- | --- |",
        ]
    )
    open_pins = {"1", "3", "5", "6"}
    for pin in sorted(EXPECTED_PIN_NETS, key=int):
        actual = pin_nets[pin]
        state = "MEASURE" if pin in open_pins else "CLOSED"
        lines.append(table_row([pin, PIN_ROLES[pin], f"`{actual}`" if actual else "-", state]))

    lines.extend(
        [
            "",
            "## Datasheet-exact Q0 selection",
            "",
            "When `/OE0` is high, Q0 is high impedance. When `/OE0` is low,",
            "Q0 equals the selected input; there is no inversion.",
            "",
            "| EARLY / B | LATE / A | Selected input | Physical pin | Board state |",
            "| ---: | ---: | --- | ---: | --- |",
            "| 0 | 0 | D00 | 6 | unresolved |",
            "| 0 | 1 | D01 | 5 | unresolved |",
            "| 1 | 0 | D02 | 4 | R92/R99 ladder from D95.14 density-control conductor |",
            "| 1 | 1 | D03 | 3 | unresolved |",
            "",
            "R92=1.3 kΩ joins the D95.14 density-control conductor to D101.4;",
            "R99=4.7 kΩ returns D101.4 to ground. With an ideal 5 V source high,",
            "the passive divider is nominally 3.92 V. This is a probe prediction,",
            "not a measured threshold or proof of the other three data inputs.",
            "",
            "## Physical D94 register-3 constraint",
            "",
            "The table below reads the validated `.092` image directly. `yes` means",
            "the open-collector output is programmed active (raw bit zero). A1:A0",
            "is fixed at `11`, the only register address where A4 changes D0/D2/D3.",
            "",
            "| A4 / Q0 | A3 / qualified /WR | A2 / IORD | Address | Raw | D0 active | /RE active | /WE active |",
            "| ---: | ---: | ---: | ---: | ---: | --- | --- | --- |",
        ]
    )
    lines.extend(table_row(row) for row in register3_rows)
    lines.extend(
        [
            "",
            "Therefore A4 low always asserts D94 D0 and releases both D93 strobes",
            "at register 3. A4 high always releases D0 and restores the mutually",
            "exclusive direction-appropriate `/RE` or `/WE` strobe. No other FDC",
            "register address depends on A4.",
            "",
            "## Conditional D0-to-enable test",
            "",
            "D94.1/D0 and D101.1 `/OE0` are both active-low, pull/tri-state-related",
            "singleton boundaries, while D101.Q0 already feeds D94.A4. That makes a",
            "D94.1-to-D101.1 continuity test high-information, but it does **not**",
            "prove those pins share copper. The owner measurement found only R8 on",
            "D94.1, and the source model deliberately keeps the nets separate.",
            "",
            "If chip-removed continuity does join D94.1 to D101.1, then an A4-low",
            "register-3 row enables Q0 and the selected D00-D03 value immediately",
            "drives A4. A selected zero is consistent with the low state; a selected",
            "one drives A4 high, causing D94 D0 to release and `/OE0` to return high.",
            "This is a conditional digital implication only; analog settling and TTL",
            "floating-high behavior still require a powered capture.",
            "",
            "If repeated chip-removed checks isolate D94.1 from D101.1 and every",
            "nearby support pin, record D94 D0 as deliberately R8-pull-up-only and",
            "continue tracing D101 `/OE0` independently. Do not merge the boundary",
            "nets from functional resemblance.",
            "",
            "## Minimal closure sequence",
            "",
            "1. Remove D94 and D101; measure D94.1 to D101.1 directly, then repeat",
            "   D94.1 against the nearby D99/D101 support pins.",
            "2. With D101 removed, identify D101.1, .3, .5, and .6 remote endpoints.",
            "   Preserve pin 4 as the already-closed R92/R99 ladder.",
            "3. Only after continuity closure, capture EARLY, LATE, `/OE0`, Q0/A4,",
            "   D94 D0, `/RE`, and `/WE` during port `1F` transfers.",
            "4. Promote copper only when the direct measurements agree; otherwise",
            "   retain the four explicit boundary nets or document a redesign.",
            "",
            "## Reconstruction boundary",
            "",
            "Closed automatically: device truth table, select order, Q0 destination,",
            "D02 ladder, D94 register-3 steering truth, and exact probe states.",
            "Still physical: D101.1 `/OE0`, D03/pin3, D01/pin5, D00/pin6, the",
            "D94 D0 hidden-load disposition, and powered analog behavior.",
        ]
    )

    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    print(f"Status: {status}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
