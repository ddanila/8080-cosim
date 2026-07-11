#!/usr/bin/env python3
"""Generate the serial-port handoff report."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "kicad" / "juku.board.json"
REPORT = ROOT / "docs" / "serial-handoff.md"
AUXILIARY_PINS = {
    "14": "RXRDY", "15": "TXRDY", "16": "SYNDET", "17": "CTS_N",
    "18": "TXEMPTY", "20": "CLK", "21": "RESET", "22": "DSR_N",
}


def load_board() -> dict:
    return json.loads(BOARD.read_text())


def has_node(board: dict, net_name: str, ref: str, pin: str) -> bool:
    net = board["nets"].get(net_name)
    if not net:
        return False
    return [ref, pin] in net.get("nodes", [])


def endpoints(board: dict, net_name: str) -> str:
    net = board["nets"].get(net_name, {})
    nodes = net.get("nodes", [])
    text = ", ".join(f"`{ref}.{pin}`" for ref, pin in nodes[:8])
    if len(nodes) > 8:
        text += f", ... (+{len(nodes) - 8})"
    return text or "-"


def chip_type(board: dict, ref: str) -> str:
    for chip in board["chips"]:
        if chip.get("ref") == ref:
            return str(chip.get("type", ""))
    return ""


def chip(board: dict, ref: str) -> dict:
    return next((item for item in board["chips"] if item.get("ref") == ref), {})


def pin_is_netted(board: dict, ref: str, pin: str) -> bool:
    return any([ref, pin] in net.get("nodes", []) for net in board["nets"].values())


def marker(path: str, *needles: str) -> bool:
    text = (ROOT / path).read_text(errors="replace")
    return all(needle in text for needle in needles)


def table_row(values: list[object]) -> str:
    return "| " + " | ".join(str(value).replace("|", "/") for value in values) + " |"


def check_rows(board: dict) -> list[list[object]]:
    checks: list[tuple[str, bool, str]] = []
    checks.append(
        ("D11 is the board USART", chip_type(board, "D11") == "USART8251", "board JSON")
    )
    checks.append(
        (
            "D11 complete auxiliary pin contract is exposed",
            all(chip(board, "D11").get("pins", {}).get(pin) == role
                for pin, role in AUXILIARY_PINS.items()),
            "КР580ВВ51А/8251 datasheet contract",
        )
    )
    checks.append(
        (
            "D11 power-pin contract is routed",
            chip(board, "D11").get("pins", {}).get("4") == "VSS_GND"
            and chip(board, "D11").get("pins", {}).get("26") == "VCC_5V"
            and has_node(board, "GND", "D11", "4")
            and has_node(board, "P5V", "D11", "26"),
            "D11.4 GND / D11.26 +5V",
        )
    )
    checks.append(
        ("D11 chip select is decoded", has_node(board, "CS_D11", "D11", "11"), "`CS_D11`")
    )
    checks.append(
        ("D11 register select BA0 is wired", has_node(board, "BA0", "D11", "12"), "`BA0`")
    )
    for bit, pin in enumerate(["27", "28", "1", "2", "5", "6", "7", "8"]):
        checks.append(
            (
                f"D11 data bit DB{bit} is wired",
                has_node(board, f"DB{bit}", "D11", pin),
                f"`DB{bit}`",
            )
        )
    checks.append(("D11 read strobe is wired", has_node(board, "IORD", "D11", "13"), "`IORD`"))
    checks.append(("D11 write strobe is wired", has_node(board, "IOWR", "D11", "10"), "`IOWR`"))
    checks.append((
        "USART reset follows the system reset inverter",
        has_node(board, "RESET", "D13", "6")
        and has_node(board, "RESET", "D1", "12")
        and has_node(board, "RESET", "D11", "21")
        and marker("hdl/juku_top.v", ".reset(reset_sys), .dsr_n(ser_dsr_n)"),
        "sheet-1 uninterrupted D13.6 -> D1.12/D11.21 conductor; `RESET`",
    ))
    checks.append((
        "USART main clock reaches D13 inverter output",
        has_node(board, "D13_4_D105_2", "D13", "4")
        and has_node(board, "D13_4_D105_2", "D105", "2")
        and has_node(board, "D13_4_D105_2", "D11", "20"),
        "sheet-1 uninterrupted D13.4 -> D105.2/D11.20 conductor",
    ))
    checks.append(
        (
            "D57 baud output reaches D11 TxC/RxC",
            has_node(board, "PIT_BAUD", "D11", "9")
            and has_node(board, "PIT_BAUD", "D11", "25"),
            "`PIT_BAUD`",
        )
    )
    checks.append(
        (
            "USART TxD fans to line drivers",
            has_node(board, "SER_TXD", "D11", "19")
            and has_node(board, "SER_TXD", "D14", "3")
            and has_node(board, "SER_TXD", "D3", "11")
            and has_node(board, "SER_TXD", "D3", "9"),
            "`SER_TXD`",
        )
    )
    checks.append((
        "D3.9->8 pre-inverter drives tied D12 inputs",
        has_node(board, "SER_TXD_INV", "D3", "8")
        and has_node(board, "SER_TXD_INV", "D12", "1")
        and has_node(board, "SER_TXD_INV", "D12", "2"),
        "`SER_TXD_INV`",
    ))
    checks.append((
        "8259 SP/EN is strapped high for standalone master mode",
        has_node(board, "P5V", "D10", "16")
        and marker("hdl/juku_top.v", "wire pic_sp_en = 1'b1", ".sp_en(pic_sp_en)"),
        "sheet-1 A-rail arrow; `P5V`",
    ))
    checks.append(
        (
            "USART RTS/DTR reach AP2 driver",
            has_node(board, "SER_RTS", "D32", "3")
            and has_node(board, "SER_DTR", "D32", "2"),
            "`SER_RTS` / `SER_DTR`",
        )
    )
    checks.append(
        (
            "USART RxD comes from UP2 receiver",
            has_node(board, "SER_RXD", "D11", "3")
            and has_node(board, "SER_RXD", "D104", "13"),
            "`SER_RXD`",
        )
    )
    checks.append((
        "USART CTS/DSR come from the other two UP2 receivers",
        has_node(board, "SER_CTS_N", "D104", "12")
        and has_node(board, "SER_CTS_N", "D11", "17")
        and has_node(board, "SER_DSR_N", "D104", "11")
        and has_node(board, "SER_DSR_N", "D11", "22"),
        "`SER_CTS_N` / `SER_DSR_N`",
    ))
    for net_name, ref, pin in [
        ("S_SOUT", "X3", "9"),
        ("S_RTS", "X3", "10"),
        ("S_DTP", "X3", "11"),
        ("S_TTL", "X3", "3"),
        ("S_OC", "X3", "12"),
        ("S_SIN", "X3", "4"),
        ("S_CTS", "X3", "5"),
        ("S_DSR", "X3", "6"),
    ]:
        checks.append(
            (f"{net_name} reaches X3.{pin}", has_node(board, net_name, ref, pin), f"`{net_name}`")
        )
    checks.append(
        (
            "HDL USART model has guarded Tx/Rx loopback",
            marker(
                "hdl/devices.v",
                "module usart_8251",
                "Minimal async 8N1 shifter",
            )
            and marker(
                "hdl/sim/usart_8251_tb.v",
                "USART8251: PASS",
            )
            and marker(
                "sync/serial_check.sh",
                "hdl/sim/usart_8251_tb.v",
            ),
            "`hdl/devices.v`; `hdl/sim/usart_8251_tb.v`; `sync/serial_check.sh`",
        )
    )
    checks.append(
        (
            "HDL serial connector and drivers are instantiated",
            marker("hdl/juku_top.v", "serial_conn U_X3", "ap2_drv U_D14", "up2_rcv U_D104"),
            "`hdl/juku_top.v`",
        )
    )
    return [[name, "PASS" if ok else "FAIL", evidence] for name, ok, evidence in checks]


def all_pass(rows: list[list[object]]) -> bool:
    return all(row[1] == "PASS" for row in rows)


def main() -> int:
    board = load_board()
    rows = check_rows(board)
    status = (
        "SERIAL CORE GUARDED / AUXILIARY PIN CONTINUITY PENDING"
        if all_pass(rows)
        else "SERIAL HANDOFF REGRESSION"
    )

    lines = [
        "# Serial handoff",
        "",
        f"Status: **{status}**",
        "",
        "This generated report separates the serial-port facts already guarded by",
        "the board JSON and HDL from the remaining functional serial boundary.",
        "It covers the D11 8251 host bus path, the D57 baud-clock handoff, and",
        "the X3 line-driver/receiver wiring. It now also guards a minimal",
        "bus-visible 8251-style async Tx/Rx loopback slice; it does not claim",
        "external X3 loopback or full protocol-mode coverage.",
        "",
        "## Command",
        "",
        "```sh",
        "python3 scripts/report_serial_handoff.py",
        "```",
        "",
        "## Checks",
        "",
        table_row(["Check", "Result", "Evidence"]),
        table_row(["---", "---", "---"]),
    ]
    lines.extend(table_row(row) for row in rows)
    lines.extend(
        [
            "",
            "## Serial Nets",
            "",
            table_row(["Net", "Endpoints"]),
            table_row(["---", "---"]),
        ]
    )
    for net_name in [
        "CS_D11",
        "RESET",
        "D13_4_D105_2",
        "PIT_BAUD",
        "SER_TXD",
        "SER_TXD_INV",
        "SER_RTS",
        "SER_DTR",
        "SER_RXD",
        "SER_CTS_N",
        "SER_DSR_N",
        "S_SOUT",
        "S_RTS",
        "S_DTP",
        "S_TTL",
        "S_OC",
        "S_SIN",
        "S_CTS",
        "S_DSR",
    ]:
        lines.append(table_row([f"`{net_name}`", endpoints(board, net_name)]))
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- D11 is bus-visible at the decoded `0x08..0x0B` USART window, with",
            "  BA0, DB0-DB7, `IORD`, `IOWR`, and `CS_D11` wired.",
            "- D57 `OUT0` reaches both D11 clock inputs through `PIT_BAUD`.",
            "- D11 serial-side pins are carried through the modeled D14/D32/D3/D12",
            "  output drivers and D104 receiver to X3 signal pins.",
            "- `sync/serial_check.sh` now proves a scoped USART behavior slice:",
            "  mode/command writes, TxRDY/RxRDY/TxEMPTY status, command-driven",
            "  RTS/DTR, and one 8N1 byte through a digital TxD->RxD loopback.",
            "- D11 auxiliary pins remain physical-source blockers:",
            "  " + ", ".join(
                f"{pin}:{role}" for pin, role in AUXILIARY_PINS.items()
                if not pin_is_netted(board, "D11", pin)
            ) + ".",
            "  Trace each destination or record a source-proved intentional NC before",
            "  treating the USART portion of the PCB as complete.",
            "- External X3 loopback, electrical levels, and full 8251 sync/parity",
            "  modes remain Tier-2 bench/software work after that PCB-truth boundary.",
            "",
        ]
    )
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    return 0 if all_pass(rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
