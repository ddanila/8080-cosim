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
    "1": "FDC_IMDRG",
    "2": "FDC_EARLY_SEL",
    "3": "D101_D02_R92_R99",
    "4": "D101_D02_R92_R99",
    "5": "D101_D02_R92_R99",
    "6": "D101_D02_R92_R99",
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
    input_tie_ok = nodes(board, "D101_D02_R92_R99") == {
        ("D101", "3"), ("D101", "4"), ("D101", "5"), ("D101", "6"),
        ("R92", "1"), ("R99", "2"), ("D96", "9"),
    }
    closed_local_nodes_ok = (
        nodes(board, "FDC_IMDRG") == {("D26", "38"), ("D101", "1")}
        and nodes(board, "D94_A4_D101_Q0") == {("D94", "14"), ("D101", "7")}
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
            "D101.1 /OE0 is drawn as IMDRG from D26 PA6/pin38",
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

    other_registers_ok = all(
        image[address] == image[address | 0x10]
        for address in range(16)
        if address & 0b11 != 0b11
    )

    checks = [
        ("TI SN74LS253 PDF and validated D94 image hashes match", artifact_ok),
        ("D101 all-pin JSON mapping matches the expected source/owner model", pin_map_ok),
        ("D101 section-A JSON net contains the expected seven endpoints", input_tie_ok),
        ("IMDRG, Q0, and EARLY/LATE JSON nets match the expected endpoints", closed_local_nodes_ok),
        ("R92/R99 modeled values match 1.3 kΩ / 4.7 kΩ", resistor_values_ok),
        ("Local pinout interpretation separates source and physical D101 evidence", pinout_ok),
        ("HDL/test contains selected select-order and disable markers", hdl_ok),
        ("Physical D94 register-3 rows obey the exact A4 steering contract", d94_logic_ok),
        ("Other D94 register rows are independent of A4", other_registers_ok),
    ]
    passed = all(ok for _, ok in checks)
    status = "D101 FIRST HALF LOGIC-CONSTRAINED / FIVE SOURCE JOINS MEASUREMENT-GATED" if passed else "D101 CONSTRAINT REPORT FAILED"

    lines = [
        "# D101 first-half reconstruction constraints",
        "",
        f"Status: **{status}**",
        "",
        "D101 is the target-board К555КП12 / SN74LS253 dual 4:1 multiplexer.",
        "Its Q1 write-precompensation half is source-closed. This report narrows",
        "the separate Q0 half that drives D94 A4. The drawing closes /OE0",
        "to D26 PA6/IMDRG and joins D96.9 Q2 to all four section-A data inputs. Physical",
        "continuity of IMDRG, D96.9, and three data-input branches remains unmeasured.",
        "",
        "## Command",
        "",
        "Run from the repository root. The report requires standard-library Python 3;",
        "the simulation requires Bash and Icarus Verilog (`iverilog` and `vvp`).",
        "The generator replaces this report and exits 1 if any listed check fails.",
        "",
        "```sh",
        "python3 scripts/report_d101_reconstruction_constraints.py",
        "sync/kp12_check.sh",
        "```",
        "",
        "The generator checks the pinned PDF/image hashes, JSON pin/net/value",
        "invariants, selected pinout and HDL/test text markers, and all 32 D94",
        "image rows for the A4 contract. It does not execute the mux simulation or inspect",
        "physical components. Run `sync/kp12_check.sh` separately for simulation.", "",
        "CLOSED below means represented by source or owner evidence; it does not",
        "certify every physical joint. SOURCE-CLOSED / MEASURE flags the listed",
        "D101 pins awaiting direct continuity, with D96.9 checked separately.", "",
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
        state = "SOURCE-CLOSED / MEASURE" if pin in open_pins else "CLOSED"
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
            "| 0 | 0 | D00 | 6 | source-joined to D02/R92/R99; physical check pending |",
            "| 0 | 1 | D01 | 5 | source-joined to D02/R92/R99; physical check pending |",
            "| 1 | 0 | D02 | 4 | owner-visible R92/R99 ladder from D95.14 density-control conductor |",
            "| 1 | 1 | D03 | 3 | source-joined to D02/R92/R99; physical check pending |",
            "",
            "R92=1.3 kΩ joins the D95.14 density-control conductor to D101.4;",
            "R99=4.7 kΩ returns D101.4 to ground. With an ideal 5 V source high,",
            "the passive divider is nominally 3.92 V. This is a probe prediction,",
            "not a measured threshold or proof of the other three physical joins.",
            "If those joins exist on the board, Q0's selected data is the same",
            "for every EARLY/LATE combination whenever IMDRG enables section A.",
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
            "## D0-to-IMDRG isolation test",
            "",
            "D94.1/D0 and D101.1 `/OE0` (D26 PA6/IMDRG) are separate in the",
            "source model; the drawing does **not** join those pins. Owner continuity found only R8",
            "on D94.1; further chip-removed checks must establish the hidden-load",
            "disposition within their measured scope. Do not merge D0 and IMDRG",
            "from functional resemblance. Any measured join requires source/board",
            "reconciliation before runtime inference: it would also connect D94's",
            "open-collector output to D26 PA6.",
            "",
            "## Minimal closure sequence",
            "",
            "1. Remove D94 and D101; measure D94.1 to D101.1 directly, then repeat",
            "   D94.1 against the nearby D99/D101 support pins.",
            "2. With D96 and D101 removed, confirm D101.1-D26.38 IMDRG continuity and",
            "   check D96.9 and D101.3/.5/.6 each against D101.4/R92.1/R99.2. Preserve",
            "   pin 4 as the already-closed R92/R99 ladder.",
            "3. Only after continuity closure, capture EARLY, LATE, `/OE0`, Q0/A4,",
            "   D94 D0, `/RE`, and `/WE` during port `1F` transfers.",
            "4. Promote copper only when the direct measurements agree; otherwise",
            "   split any disproved source joins or document a redesign.",
            "",
            "## Reconstruction boundary",
            "",
            "Derived constraints: mux select order and the eight D94 register-3 rows.",
            "The canonical model records the source and owner connections above.",
            "Runnable HDL omits the D97/D102/D101 precompensation chain and holds",
            "D94 A4 high; these Q0 constraints describe the structural/source path.",
            "Still physical: D101.1-D26.38 IMDRG continuity, input ties at",
            "D96.9 and D101.3/.5/.6, the D94 D0 hidden-load disposition, and",
            "powered analog behavior.",
        ]
    )

    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    print(f"Status: {status}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
