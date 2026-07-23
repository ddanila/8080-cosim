#!/usr/bin/env python3
"""Guard data-sheet eligibility for the replica's WD1793 and 4164 candidates."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BOARD_PATH = ROOT / "kicad" / "juku.board.json"
SOURCE_PCB = ROOT / "kicad" / "juku.kicad_pcb"
ROUTED_PCB = ROOT / "kicad" / "juku_routed.kicad_pcb"
DRAM_DATASHEET = ROOT / "ref" / "datasheets" / "mk4564-64kx1-dram.pdf"
DRAM_REFERENCE = ROOT / "ref" / "datasheets" / "k565ru5-pinout.txt"
FDC_DATASHEET = ROOT / "ref" / "wd1772-vg93" / "fd179x-01-datasheet.pdf"
FDC_REFERENCE = ROOT / "ref" / "datasheets" / "kr1818vg93-pinout.txt"
FDC_CLOCK_MAP = ROOT / "ref" / "schematics" / "fdc-clock-mux-map.md"
REPORT_PATH = ROOT / "docs" / "replica-candidate-parts-readiness.md"

DRAM_SHA256 = "8a6169963c020c1ff8b3c413356ed8f354b9963b77dab8f9bd2af22560c44093"
FDC_SHA256 = "e51aef0933d88e7705f6f774ffb3238e8e8096bd9b9d774a985d95ef5766e3ce"
DRAM_REFS = tuple(f"D{number}" for number in range(84, 92))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def nodes(board: dict[str, Any], net: str) -> set[tuple[str, str]]:
    return {tuple(node) for node in board["nets"][net]["nodes"]}


def chip(board: dict[str, Any], ref: str) -> dict[str, Any]:
    return next(item for item in board["chips"] if item.get("ref") == ref)


def footprint_name(text: str, ref: str) -> str:
    marker = f'(property "Reference" "{ref}"'
    marker_at = text.find(marker)
    if marker_at < 0:
        return ""
    footprint_at = text.rfind('(footprint "', 0, marker_at)
    if footprint_at < 0:
        return ""
    match = re.match(r'\(footprint "([^"]+)"', text[footprint_at:])
    return match.group(1) if match else ""


def add_check(
    checks: list[dict[str, str | bool]], name: str, passed: bool, evidence: str
) -> None:
    checks.append({"name": name, "pass": passed, "evidence": evidence})


def table_row(values: list[object]) -> str:
    return "| " + " | ".join(str(value).replace("|", "/") for value in values) + " |"


def build() -> tuple[list[dict[str, str | bool]], list[str]]:
    board = json.loads(BOARD_PATH.read_text(encoding="utf-8"))
    dram_text = DRAM_REFERENCE.read_text(encoding="utf-8")
    fdc_text = FDC_REFERENCE.read_text(encoding="utf-8")
    clock_text = FDC_CLOCK_MAP.read_text(encoding="utf-8")
    pcb_texts = {
        path: path.read_text(encoding="utf-8", errors="replace")
        for path in (SOURCE_PCB, ROUTED_PCB)
    }
    checks: list[dict[str, str | bool]] = []

    populated_dram = [chip(board, ref) for ref in DRAM_REFS]
    address_pins = {"5", "6", "7", "9", "10", "11", "12", "13"}
    add_check(
        checks,
        "Target bank identity and population match",
        all(
            item.get("type") == "RU5" and item.get("marking") == "К565РУ5Г"
            for item in populated_dram
        ),
        "D84-D91 are eight populated К565РУ5Г devices",
    )
    add_check(
        checks,
        "All populated DRAM sockets retain the JEDEC 4164 pin classes",
        all(
            item["pins"].get("1") == "NC_VBB_OPTION"
            and item["pins"].get("2") == "DI"
            and item["pins"].get("3") == "WE_N"
            and item["pins"].get("4") == "RAS_N"
            and {item["pins"].get(pin) for pin in address_pins}
            == {f"MA{bit}" for bit in range(8)}
            and item["pins"].get("14") == "DO_"
            and item["pins"].get("15") == "CAS_N"
            and item["pins"].get("16") == "VSS_GND"
            for item in populated_dram
        ),
        "pins 2/3/4/14/15/16 = DIN/WE/RAS/DOUT/CAS/GND; pins 5-7,9-13 = MA0-MA7",
    )
    add_check(
        checks,
        "DRAM option rails preserve the required conditional +5 V configuration",
        all((ref, "8") in nodes(board, "RAIL_G") for ref in DRAM_REFS)
        and all((ref, "1") in nodes(board, "RAIL_H") for ref in DRAM_REFS)
        and {("E4", "1"), ("E4", "2"), ("E4", "3")}
        <= nodes(board, "P12V") | nodes(board, "RAIL_G") | nodes(board, "P5V")
        and ("E4", "1") in nodes(board, "P12V")
        and ("E4", "2") in nodes(board, "RAIL_G")
        and ("E4", "3") in nodes(board, "P5V"),
        "E4.1=+12 V, E4.2=DRAM pin-8 rail, E4.3=+5 V; 4164 requires E4 2-3",
    )
    add_check(
        checks,
        "MK4564 primary artifact and interpreted eligibility facts are pinned",
        sha256(DRAM_DATASHEET) == DRAM_SHA256
        and all(
            marker in dram_text
            for marker in (
                "MK4564(P/N/J/E)-12",
                "Package: 16 pins",
                "8   VCC (+5 V)",
                "16  VSS (GND)",
                "128 cycles / 2 ms",
                "MK4564-12 =",
                "120 ns / 220 ns",
            )
        ),
        "Mostek MK4564-12: JEDEC 64Kx1, single +5 V, 120 ns access, 220 ns cycle, 128/2 ms refresh",
    )
    add_check(
        checks,
        "DRAM source and routed footprints accept the dual-in-line candidate",
        all(
            footprint_name(pcb_texts[path], ref) == "DIP-16_W7.62mm"
            for path in (SOURCE_PCB, ROUTED_PCB)
            for ref in DRAM_REFS
        ),
        "D84-D91 use 16-pin, 7.62 mm-row, 2.54 mm-pitch DIP footprints",
    )

    d93 = chip(board, "D93")
    expected_d93 = {
        "1": "NC_BACK_BIAS", "2": "WE_N", "3": "CS_N", "4": "RE_N",
        "5": "A0", "6": "A1", "7": "DAL0", "8": "DAL1", "9": "DAL2",
        "10": "DAL3", "11": "DAL4", "12": "DAL5", "13": "DAL6",
        "14": "DAL7", "15": "STEP", "16": "DIRC", "17": "EARLY",
        "18": "LATE", "19": "MR_N", "20": "VSS_GND", "21": "VCC_5V",
        "22": "TEST", "23": "HLT", "24": "CLK", "25": "RG",
        "26": "RCLK", "27": "RAW_READ", "28": "HLD", "29": "TG43",
        "30": "WG", "31": "WDATA", "32": "READY", "33": "WF_VFOE",
        "34": "TR00", "35": "INDEX", "36": "WPRT", "37": "DDEN",
        "38": "DRQ", "39": "INTRQ", "40": "VDD_12V",
    }
    add_check(
        checks,
        "D93 carries the complete FD1793 pin contract",
        d93.get("type") == "VG93_FDC" and d93.get("pins") == expected_d93,
        "all 40 host, drive, separator, status, clock, and supply pins match",
    )
    add_check(
        checks,
        "FD179X primary artifact and interpreted supply/clock facts are pinned",
        sha256(FDC_DATASHEET) == FDC_SHA256
        and all(
            marker in fdc_text
            for marker in (
                "Package: 40 pins",
                "20  GND",
                "21  +5 V",
                "24  CLK",
                "40  +12 V",
            )
        ),
        "FD1793: pin20 GND, pin21 +5 V, pin40 +12 V, 1 MHz mini-drive clock",
    )
    add_check(
        checks,
        "Board rails and D95 provide the FD1793 operating configuration",
        ("D93", "20") in nodes(board, "GND")
        and ("D93", "21") in nodes(board, "P5V")
        and ("D93", "40") in nodes(board, "P12V")
        and nodes(board, "FDC_CLK") == {("D93", "24"), ("D95", "7")}
        and "`5″/8″=0` -> controller 1 MHz" in clock_text,
        "D93 has GND/+5 V/+12 V and D95 selects the source-proved 1 MHz mini-drive clock",
    )
    add_check(
        checks,
        "FDC source and routed footprints accept the plastic candidate",
        all(
            footprint_name(pcb_texts[path], "D93") == "DIP-40_W15.24mm"
            for path in (SOURCE_PCB, ROUTED_PCB)
        ),
        "FD1793B-01 plastic package: 40 pins, 0.600-inch rows, 0.100-inch pitch",
    )

    holds = [
        "Fit E4 only in the 2-3 position and verify DRAM pin 8 is +5 V before seating any MK4564; the source model preserves all three pads but does not claim the installed jumper position.",
        "The MK4564-12 maximum access/cycle figures are faster than the recorded 200 ns РУ5Г grade, but unresolved physical CAS/slot timing still requires a scope or staged memory test.",
        "Do not seat the FD1793 until the remaining D96/D99/D101 support-device continuity and powered-behavior gates close; verify D93 clocks and host strobes at the socket.",
        "Live seller stock, authenticity, date-code condition, pricing, purchase authorization, receipt inspection, and tester results remain procurement-time evidence.",
    ]
    return checks, holds


def write_report(checks: list[dict[str, str | bool]], holds: list[str]) -> None:
    lines = [
        "# Replica candidate-part readiness",
        "",
        "Status date: **2026-07-23**.",
        "",
        "Status: **DATA-SHEET COMPATIBILITY GUARDED / E4, RECEIPT, AND BENCH ACCEPTANCE OPEN**.",
        "",
        "This report closes the static pinout, voltage, clock/refresh, speed-grade,",
        "and package questions for two functional-build candidates. It is not a",
        "vendor cart, stock claim, received-part test, or authorization to seat parts.",
        "",
        "## Command",
        "",
        "```sh",
        "python3 scripts/report_replica_candidate_parts.py",
        "```",
        "",
        "## Guarded checks",
        "",
        "| Check | Result | Evidence |",
        "| --- | --- | --- |",
    ]
    lines.extend(
        table_row([item["name"], "PASS" if item["pass"] else "FAIL", item["evidence"]])
        for item in checks
    )
    lines.extend([
        "",
        "## Eligible functional-build candidates",
        "",
        "| Board role | Candidate | Static disposition |",
        "| --- | --- | --- |",
        table_row([
            "D84-D91 К565РУ5Г bank",
            "Mostek MK4564-12 in the manufacturer's 16-pin dual-in-line option",
            "Pin/function, +5 V, 128-cycle/2 ms refresh, 120 ns access, 220 ns cycle, and footprint eligible; E4 must bridge 2-3",
        ]),
        table_row([
            "D93 КР1818ВГ93",
            "Western Digital FD1793B-01 plastic DIP",
            "Complete pin contract, +5/+12 V rails, 1 MHz mini-drive mode, and 0.600-inch DIP footprint eligible",
        ]),
        "",
        "The candidate names are deliberately exact enough to reject a wrong package",
        "or voltage family. Other 4164/1793 manufacturers and grades remain unapproved",
        "until added here with their own primary data.",
        "",
        "## Remaining acceptance gates",
        "",
    ])
    lines.extend(f"- {item}" for item in holds)
    lines.extend([
        "",
        "## Primary evidence",
        "",
        f"- Mostek `MK4564(P/N/J/E)-12` data sheet SHA-256: `{DRAM_SHA256}`.",
        f"- Western Digital `FD179X-01` data sheet SHA-256: `{FDC_SHA256}`.",
        "- Board pin and rail authority: `kicad/juku.board.json`.",
        "- Package authority: source and promoted routed KiCad PCBs.",
        "",
    ])
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    checks, holds = build()
    write_report(checks, holds)
    print(f"Wrote {REPORT_PATH.relative_to(ROOT)}")
    failed = [item["name"] for item in checks if not item["pass"]]
    if failed:
        print("CANDIDATE PARTS: FAIL — " + "; ".join(str(item) for item in failed))
        return 1
    print("CANDIDATE PARTS: STATIC COMPATIBILITY PASS / PHYSICAL ACCEPTANCE OPEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
