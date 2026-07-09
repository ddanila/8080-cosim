#!/usr/bin/env python3
"""Generate the serial-port handoff report."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "kicad" / "juku.board.json"
REPORT = ROOT / "docs" / "serial-handoff.md"


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
            and has_node(board, "SER_TXD", "D12", "1"),
            "`SER_TXD`",
        )
    )
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
            and has_node(board, "SER_RXD", "D104", "2"),
            "`SER_RXD`",
        )
    )
    for net_name, ref, pin in [
        ("S_SOUT", "X3", "29"),
        ("S_RTS", "X3", "30"),
        ("S_DTP", "X3", "51"),
        ("S_TTL", "X3", "23"),
        ("S_OC", "X3", "32"),
        ("S_SIN", "X3", "33"),
    ]:
        checks.append(
            (f"{net_name} reaches X3.{pin}", has_node(board, net_name, ref, pin), f"`{net_name}`")
        )
    checks.append(
        (
            "HDL USART shell exposes idle serial outputs",
            marker(
                "hdl/devices.v",
                "module usart_8251",
                "Full serial engine is a boundary",
                "assign txd = 1'b1",
            ),
            "`hdl/devices.v`",
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
        "SERIAL BUS-SIDE HANDOFF READY / PROTOCOL BOUNDARY"
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
        "the X3 line-driver/receiver wiring. It does not claim a complete 8251",
        "protocol engine or an external loopback proof.",
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
        "PIT_BAUD",
        "SER_TXD",
        "SER_RTS",
        "SER_DTR",
        "SER_RXD",
        "S_SOUT",
        "S_RTS",
        "S_DTP",
        "S_TTL",
        "S_OC",
        "S_SIN",
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
            "- The current HDL USART shell is intentionally boot-safe: bus registers",
            "  latch and read back, while serial-side outputs idle. A real 8251",
            "  transmit/receive engine and external loopback remain future Tier-2",
            "  functional work, not PCB-truth blockers.",
            "",
        ]
    )
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    return 0 if all_pass(rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
