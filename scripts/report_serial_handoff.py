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


def pin_is_nc(board: dict, ref: str, pin: str) -> bool:
    return [ref, pin] in board.get("no_connects", [])


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
            "D11 TXEMPTY is source-proved NC",
            chip(board, "D11").get("pins", {}).get("18") == "TXEMPTY"
            and pin_is_nc(board, "D11", "18"),
            "full-resolution sheet-1 omits pin 18 from the drawn USART symbol",
        )
    )
    checks.append(
        (
            "D11 power-pin endpoints are modeled",
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
    checks.append((
        "D13 reset inverter is assigned and only section 11->10 remains unused",
        all(pin_is_nc(board, "D13", pin) for pin in ("10", "11"))
        and has_node(board, "RESET", "D13", "9")
        and has_node(board, "FDC_RESET_N", "D13", "8")
        and has_node(board, "FDC_RESET_N", "D93", "19")
        and has_node(board, "D6_V_ENABLE", "D13", "12")
        and has_node(board, "D105_10_H", "D13", "13"),
        "sheet-1 plus owner continuity use sections 1->2, 3->4, 5->6, 9->8, and 13->12; only 11->10 is unused",
    ))
    checks.append(
        (
            "D57 baud output reaches D11 TxC/RxC",
            has_node(board, "PIT_BAUD", "D11", "9")
            and has_node(board, "PIT_BAUD", "D11", "25")
            and board["nets"]["PIT_BAUD"].get("source_risk") is False,
            "native sheet-2 `BAUD R.` handoff and sheet-1 TxC/RxC fork",
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
        "D3 sections absent from the older sheet are owner-measured into D6",
        has_node(board, "D26_PC1_D3_I3", "D3", "3")
        and has_node(board, "D3_O4_D6_A6", "D3", "4")
        and has_node(board, "D26_PC0_D3_I5", "D3", "5")
        and has_node(board, "D3_O6_D6_A5", "D3", "6"),
        "chip-removed `.009` continuity: /PC1->D3.3/.4->D6.1 and /PC0->D3.5/.6->D6.2",
    ))
    checks.append((
        "8259 SP/EN is strapped high for standalone master mode",
        has_node(board, "P5V", "D10", "16")
        and marker("hdl/juku_top.v", "wire pic_sp_en = 1'b1", ".sp_en(pic_sp_en)"),
        "sheet-1 A-rail arrow; `P5V`",
    ))
    checks.append((
        "8259 cascade outputs are source-proved unused",
        all(pin_is_nc(board, "D10", pin) for pin in ("12", "13", "15")),
        "full-resolution sheet-1 PIC symbol omits CAS0/CAS1/CAS2 pins 12/13/15",
    ))
    checks.append((
        "USART ready outputs reach PIC IR2/IR3",
        has_node(board, "USART_RXRDY_IRQ", "D11", "14")
        and has_node(board, "USART_RXRDY_IRQ", "D10", "20")
        and has_node(board, "USART_TXRDY_IRQ", "D11", "15")
        and has_node(board, "USART_TXRDY_IRQ", "D10", "21")
        and marker("hdl/juku_top.v", ".rxrdy(ser_rxrdy)", ".txrdy(ser_txrdy)",
                   ".ir3(ser_txrdy)", ".ir2(ser_rxrdy)"),
        "native sheet-1 direct loops; pinned MAME primary-USART IR2/IR3 mapping",
    ))
    checks.append((
        "Tape-run interrupt preserves the exact-revision stale-sheet boundary",
        board["nets"].get("TAPE_RUN_INT", {}).get("nodes") == [["D10", "22"]]
        and marker(
            "kicad/juku.board.json",
            "complete recovered .009 sheet 3 is the replacement FDC circuit",
            "contains no matching TAPE RUN INT continuation",
        ),
        ".009 sheet 1: IR4=(3) TAPE RUN INT; complete .009 sheet 3: no matching continuation",
    ))
    checks.append((
        "Runnable ROMBIOS keeps stale tape IR4 masked",
        marker(
            "sync/ekdos_ioseq_reference.py",
            'find_event(events, "OUT", 0x01, 0xDF)',
            '("PIC unmask", pic_unmask, "02D6", 30524, 0xDF)',
        )
        and marker(
            "hdl/sim/juku_top_periph_bus_tb.v",
            "io_write(8'h01, 8'hDF);",
            "unmask IR5, matching ROMBIOS frame path",
        ),
        "exact ekta37 event at 0x02D6 writes mask 0xDF: IR4 masked, IR5 enabled",
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
    checks.append((
        "UP2 fourth receiver output is owner-closed NC",
        has_node(board, "GND", "D104", "7")
        and pin_is_nc(board, "D104", "10")
        and "disproving the former D94.13/R87.1 merge" in chip(board, "D104").get("prov", {}).get("pins", "")
        and "pin7 shares D94.13" not in chip(board, "D104").get("prov", {}).get("pins", "")
        and marker("hdl/juku_top.v", ".x4_in(1'b0)",
                   ".x4_out());  // photo: pin 7 -> R30 lower; source assigns GND; pin 10 NC"),
        "D104.7 reaches R30 lower on visible front copper; source assigns that pad to GND, pending owner-board rail measurement; D104.10 is NC",
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
            "X3.7 is signal ground on CS00015",
            marker(
                "docs/owner-measured-facts.md",
                "`X3.7` is signal ground on Arvutimuuseum machine `CS00015`.",
                "owner continuity, 2026-08-01",
            ),
            "owner continuity, 2026-08-01",
        )
    )
    checks.append(
        (
            "Factory wire W20 closes D3.10 to the S_TTL connector island",
            has_node(board, "S_TTL_D3", "D3", "10")
            and has_node(board, "S_TTL_D3", "W20", "2")
            and has_node(board, "S_TTL", "W20", "1")
            and has_node(board, "S_TTL", "A23", "1")
            and board["nets"]["S_TTL"].get("wire_link")
            == {"ref": "W20", "other_net": "S_TTL_D3"},
            "assembly wire W20; `S_TTL_D3` -> `S_TTL`",
        )
    )
    checks.append(
        (
            "USART model and loopback test contain required code markers",
            marker(
                "hdl/devices.v",
                "module usart_8251",
                "Minimal async 8N1 shifter",
                "wire tx_allowed = tx_enable & ~cts_n",
            )
            and marker(
                "hdl/sim/usart_8251_tb.v",
                "USART8251: PASS",
                "holding-to-shift status",
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
        "SERIAL CORE GUARDED / PHYSICAL LEVELS PENDING"
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
        "the X3 line-driver/receiver wiring. It checks code markers for a minimal",
        "bus-visible 8251-style async Tx/Rx slice with separate transmit holding",
        "and shift stages; it does not claim",
        "external X3 loopback or full protocol-mode coverage.",
        "",
        "## Command",
        "",
        "Run from the repository root with Python 3. The generator overwrites",
        "`docs/serial-handoff.md`, including when a checked invariant fails.",
        "",
        "```sh",
        "python3 scripts/report_serial_handoff.py",
        "```",
        "",
        "The generator checks JSON endpoint and provenance invariants, selected HDL",
        "and test-source markers, and recorded diagnostic evidence. It does not",
        "run the USART simulation, perform LVS, inspect PCB copper, or measure",
        "line levels. For device behavior, run the guard from the repository root",
        "with Bash, Python 3, and Icarus Verilog (`iverilog` and `vvp`):",
        "",
        "```sh",
        "sync/serial_check.sh",
        "```",
        "",
        "The guard uses temporary simulation files and regenerates this report",
        "after the USART simulation passes.", "",
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
        "USART_RXRDY_IRQ",
        "USART_TXRDY_IRQ",
        "S_SOUT",
        "S_RTS",
        "S_DTP",
        "S_TTL",
        "S_TTL_D3",
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
            "- D11 serial-side pins are carried through the modeled D14/D32/D3/D12",
            "  output drivers and D104 receiver to X3 signal pins. D3.10 reaches",
            "  X3.3 through the explicit W20 assembly-wire closure.",
            "- Owner continuity on Arvutimuuseum machine `CS00015` identifies X3 pin 7 as",
            "  signal ground.  This closes the ground contact for the current diagnostic",
            "  cable; it does not silently rewrite the still-separate generic A27 harness",
            "  boundary in the reconstructed PCB without a corresponding board-side chase.",
            "- `sync/serial_check.sh` tests a scoped USART behavior slice:",
            "  mode/command writes, the `TxRDY=0,TxEMPTY=0` holding-full state,",
            "  the `TxRDY=1,TxEMPTY=0` holding-to-shift transition, final",
            "  `TxEMPTY=1`, RxRDY, command-driven RTS/DTR, and one 8N1 byte",
            "  through a digital TxD->RxD loopback with active-low CTS asserted.",
            "  PTY attachment likewise represents an attached harness with CTS",
            "  active; on hardware the Nano/level-shifter must drive X3 CTS low",
            "  before reset because an open MC1489-class input yields inactive CTS.",
            "  This follows the [Intel 8251A datasheet](https://community.intel.com/cipcp26785/attachments/cipcp26785/programmable-devices/89914/1/P8251A.pdf)",
            "  CTS gating and the [TI MC1489 datasheet](https://www.ti.com/lit/ds/symlink/mc1489a.pdf)",
            "  open-input output guarantee.",
            "- D104's fourth receiver input pin 7 is separate from D94.13 (~84 kΩ).",
            "  The marked notch-down package has an uninterrupted front copper path",
            "  from pin 7 to R30's lower pad. The exact-source model assigns that",
            "  pad to ground; owner-board rail polarity still needs a meter check.",
            "  Exact `.009` sheet 1 draws only",
            "  sections 4→13, 5→12, and 6→11, omitting the fourth 7→10 section; direct",
            "  owner continuity on 2026-07-21 closes output pin 10 as NC. A D11-local fit",
            "  photo-registers its package but does not prove pin 7's rail. The ground",
            "  assignment uses component copper and R30's source endpoint.",
            "- D11 auxiliary pins without a net or explicit NC:",
            "  " + (", ".join(
                f"{pin}:{role}" for pin, role in AUXILIARY_PINS.items()
                if not pin_is_netted(board, "D11", pin) and not pin_is_nc(board, "D11", pin)
            ) or "none; all are dispositioned") + ".",
            "- Native sheet 1 directly loops D11 RxRDY pin14 to PIC IR2 pin20 and",
            "  D11 TxRDY pin15 to PIC IR3 pin21. The separately labeled off-sheet",
            "  `(3)` RxRDY/TxRDY arrows belong to the alternate interface. Exact `.009`",
            "  sheet 1 source-closes IR0 to X2.214 and IR1 to X2.218/D27 PB7.",
            "  They are separate from the sheet-3 FDC conditioner; direct FDC-to-PIC",
            "  assignments must not be inferred from the older behavioral model.",
            "- The same `.009` sheet 1 retains `IR4=(3) TAPE RUN INT`, but the",
            "  complete replacement FDC sheet 3 has no matching continuation.",
            "  D10.22 remains an unmatched endpoint, not an NC or inferred FDC input.",
            "  Its front route is obscured by cable/adhesive and no solder-side departure",
            "  is exposed. With power removed, probe pin 22 near `(2456,1305)` in `200415237` or",
            "  `(3438,1028)` in `200522685`; image identities and row anchors are in the",
            "  [D10 photo registration](../ref/photos/juku-pcb-2/local-package-registration.json).",
            "  The recorded ekta37 mask `0xDF` enables only frame IR5 and masks IR4;",
            "  it does not resolve the physical continuation.",
            "- Wired USART ready signals do not establish interrupt service in the",
            "  runnable HDL: its PIC is a register stub, and the separate `intr_ctl`",
            "  helper services the synthetic frame tick only. Cosim services USART",
            "  IR2/IR3 as well; see [interrupt behavior](hardware-map.md#interrupt-and-keyboard-behavior).",
            "- Full-resolution sheet 1 proves D11.16 `SYNDET` on the lower S4 throw.",
            "  D11.18 `TXEMPTY` is absent from the drawn USART symbol and modeled NC.",
            "- This guard does not qualify external X3 loopback, electrical levels,",
            "  or the complete 8251 synchronous and parity-mode behavior. Physical",
            "  session qualifications belong to their machine-specific records.",
            "",
        ]
    )
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    return 0 if all_pass(rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
