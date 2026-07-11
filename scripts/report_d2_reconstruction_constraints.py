#!/usr/bin/env python3
"""Generate the D2 .037 PROM reconstruction constraints report."""
from __future__ import annotations

import json
import re
import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "kicad" / "juku.board.json"
DSN = ROOT / "kicad" / "juku.dsn"
PCB = ROOT / "kicad" / "juku.kicad_pcb"
REPORT = ROOT / "docs" / "d2-reconstruction-constraints.md"
FIRMWARE = ROOT / "ref" / "firmware"
SYMBOLIC = ROOT / "ref" / "reconstructed-proms" / "d2_037_symbolic_truth.csv"

# Direct reads from the full-resolution factory sheet.  These are deliberately
# kept separate from board nets so factory-sheet and later photo evidence remain
# distinguishable in the generated report.
SCHEMATIC_LEADS = {
    "4": ("VIDEO_CYCLE", "sheet 1 label `VIDEO CYCLE` enters D2 A3/pin 4"),
    "2": ("XACK_N", "sheet 1 label `-XACK` enters D2 A5/pin 2"),
    "15": ("WREQ_N", "sheet 1 label `-WREQ` enters D2 A7/pin 15"),
    "12": ("D2_WAIT_RAW", "sheet 1 D2 D0/pin 12 enters D105 pin 9"),
    "13": ("GND", "sheet 1 D2 V1/pin 13 is tied low"),
    "14": ("GND", "sheet 1 D2 V2/pin 14 is tied low"),
}


def read(path: str) -> str:
    return (ROOT / path).read_text(errors="replace")


def marker(path: str, *needles: str) -> bool:
    text = read(path)
    return all(needle in text for needle in needles)


def table_row(values: list[object]) -> str:
    return "| " + " | ".join(str(value).replace("|", "/") for value in values) + " |"


def load_board() -> dict:
    return json.loads(BOARD.read_text())


def d2_chip(board: dict) -> dict:
    for chip in board["chips"]:
        if chip.get("ref") == "D2":
            return chip
    raise SystemExit("D2 not found in board JSON")


def net_for_pin(board: dict, ref: str, pin: str) -> tuple[str, str] | None:
    for name, net in board["nets"].items():
        if [ref, pin] in net.get("nodes", []):
            return name, net.get("src", "")
    return None


def dsn_pin_nets(ref: str) -> dict[str, str]:
    text = DSN.read_text(errors="replace")
    found: dict[str, str] = {}
    for match in re.finditer(
        r"\(net\s+([^\s()]+)\s+\(pins\s+([^)]*)\)\s*\)",
        text,
        flags=re.S,
    ):
        name = match.group(1)
        pins = re.findall(r"([A-Z]+\d+-\d+[A-Z]?)", match.group(2))
        for pinref in pins:
            if pinref.startswith(f"{ref}-"):
                found[pinref.split("-", 1)[1]] = name
    return found


def matching_block(text: str, start: int) -> str:
    depth = 0
    in_string = False
    escaped = False
    for pos in range(start, len(text)):
        char = text[pos]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return text[start : pos + 1]
    raise ValueError("unterminated S-expression")


def pcb_footprint_block(ref: str) -> str:
    text = PCB.read_text(errors="replace")
    ref_pos = text.find(f'(property "Reference" "{ref}"')
    if ref_pos < 0:
        return ""
    start = text.rfind("\n\t(footprint ", 0, ref_pos)
    if start < 0:
        return ""
    return matching_block(text, start + 1)


def pcb_pin_nets(ref: str) -> dict[str, str]:
    block = pcb_footprint_block(ref)
    if not block:
        return {}
    found: dict[str, str] = {}
    for match in re.finditer(r'\n\t\t\(pad\s+"([^"]+)"', block):
        pin = match.group(1)
        pad_block = matching_block(block, match.start() + 3)
        net = re.search(r'\(net\s+\d+\s+"([^"]+)"\)', pad_block)
        if net:
            found[pin] = net.group(1)
    return found


def firmware_candidates() -> list[str]:
    if not FIRMWARE.exists():
        return []
    suffixes = (".037", ".037.hex", "_037.hex")
    return sorted(
        str(path.relative_to(ROOT))
        for path in FIRMWARE.iterdir()
        if path.name.lower().endswith(suffixes)
    )


def role_key(item: tuple[str, str]) -> tuple[int, int]:
    pin, role = item
    group = 0 if role.startswith("A") else 1 if role.startswith("V") else 2
    return group, int(pin)


def main() -> int:
    board = load_board()
    chip = d2_chip(board)
    pin_roles: dict[str, str] = chip.get("pins", {})
    board_type = str(chip.get("type", ""))
    prov = chip.get("prov", {})
    dsn_nets = dsn_pin_nets("D2")
    pcb_nets = pcb_pin_nets("D2")

    pin_rows: list[str] = []
    signal_nets: list[str] = []
    for pin, role in sorted(pin_roles.items(), key=role_key):
        net = net_for_pin(board, "D2", pin)
        if net is None:
            lead = SCHEMATIC_LEADS.get(pin)
            if lead:
                pin_rows.append(table_row([pin, role, f"`{lead[0]}` (not netted)", lead[1]]))
            else:
                pin_rows.append(table_row([pin, role, "-", "not traced/netted"]))
        else:
            name, src = net
            signal_nets.append(name)
            pin_rows.append(table_row([pin, role, f"`{name}`", src or "-"]))

    dsn_rows: list[str] = []
    for pin, role in sorted(pin_roles.items(), key=role_key):
        name = dsn_nets.get(pin)
        dsn_rows.append(
            table_row([
                pin,
                role,
                f"`{name}`" if name else "-",
                "present" if name else "missing in DSN",
            ])
        )

    pcb_rows: list[str] = []
    for pin, role in sorted(pin_roles.items(), key=role_key):
        name = pcb_nets.get(pin)
        pcb_rows.append(
            table_row([
                pin,
                role,
                f"`{name}`" if name else "-",
                "present" if name else "unnetted in PCB",
            ])
        )

    candidates = firmware_candidates()
    symbolic_rows = list(csv.DictReader(SYMBOLIC.open())) if SYMBOLIC.exists() else []
    symbolic_ok = (
        len(symbolic_rows) == 256
        and all(row.get("D0") == "?" for row in symbolic_rows)
        and symbolic_rows[0].get("prom_address_hex") == "0x00"
        and symbolic_rows[-1].get("prom_address_hex") == "0xFF"
    )
    identity_ok = board_type == "DEC_PROM" and "ДГШ5.106.037" in str(prov)
    d9 = next((item for item in board["chips"] if item.get("ref") == "D9"), {})
    io_decoder_superseded = (
        d9.get("type") == "IO_DEC138"
        and "Physical D2 is a separate КР556РТ4 bus/wait part" in str(d9.get("prov", {}))
    )
    fallback_boundary = marker(
        "docs/reconstructed-prom-fallbacks.md",
        "No D2 image is exported",
        "ДГШ5.106.037",
    )
    official_bom_lead = marker(
        "ref/photos/juku-pcb-2/BODGE-TRIAGE.md",
        "D2 = РТ4 .037",
        "D6 = .038",
    )
    raw_pin_table_lead = marker(
        "ref/photos/juku-pcb-2/BODGE-TRIAGE.md",
        "The D2 pin table from sheet 1 is:",
        "A0-A7=5/6/7/4/3/2/1/15",
        "All D2 inputs are now modeled and routed",
        "its PROM contents remain deferred",
    )
    all_signal_pins_netted = (
        len(signal_nets) == len(pin_roles)
        and len(dsn_nets) >= len(pin_roles)
        and len(pcb_nets) >= len(pin_roles)
    )
    address_pins = {"1", "2", "3", "4", "5", "6", "7", "15"}
    source_inputs_closed = all(net_for_pin(board, "D2", pin) for pin in address_pins)
    source_inputs_in_pcb = all(pin in pcb_nets for pin in address_pins)
    if identity_ok and all_signal_pins_netted and candidates:
        status = "D2 RECONSTRUCTION READY"
    elif identity_ok and not signal_nets and not dsn_nets and not pcb_nets and not candidates:
        status = "D2 RECONSTRUCTION CONSTRAINED / DUMP REQUIRED"
    elif identity_ok and source_inputs_closed and source_inputs_in_pcb and not candidates:
        status = "D2 INPUTS TRACED / DUMP REQUIRED"
    elif identity_ok and signal_nets and not all_signal_pins_netted and not candidates:
        status = "D2 RECONSTRUCTION PARTIALLY TRACED / DUMP REQUIRED"
    else:
        status = "D2 RECONSTRUCTION INPUTS CHANGED"

    lines = [
        "# D2 .037 reconstruction constraints",
        "",
        f"Status: **{status}**",
        "",
        "This generated report records what the repo can currently prove about",
        "the processor-board `D2` К556РТ4 PROM (`ДГШ5.106.037`) before attempting",
        "any reverse-engineered or burnable replacement table.",
        "",
        "## Command",
        "",
        "```sh",
        "python3 scripts/report_d2_reconstruction_constraints.py",
        "```",
        "",
        "## Identity",
        "",
        table_row(["Field", "Value"]),
        table_row(["---", "---"]),
        table_row(["Board type", f"`{board_type or 'missing'}`"]),
        table_row(["Programmed drawing", "`ДГШ5.106.037`" if identity_ok else "-"]),
        table_row(["Current role", "bus-arbitration/wait PROM, not I/O decode"]),
        "",
        "## Board JSON Pins",
        "",
        table_row(["Pin", "Role", "Net", "Source"]),
        table_row(["---:", "---", "---", "---"]),
    ]
    lines.extend(pin_rows)
    lines.extend(
        [
            "",
            "## Exact PROM Address Index",
            "",
            "The traced physical address byte is:",
            "",
            "`{WREQ_N, A10, XACK_N, A14, CAS/VIDEO_CYCLE, A9, A15, A12}`",
            "",
            "Therefore `prom_address = (WREQ_N<<7) + (A10<<6) + (XACK_N<<5) +",
            "(A14<<4) + (CAS_VIDEO_CYCLE<<3) + (A9<<2) + (A15<<1) + A12`.",
            "`ref/reconstructed-proms/d2_037_symbolic_truth.csv` enumerates all",
            "256 input vectors. Every D0 cell is deliberately `?`; the CSV is a",
            "constraint artifact, not a programmer image.",
            "",
            "The named schematic leads above are pin-level source evidence, not a",
            "claim that the D2 truth table is known. Each proved pin is promoted",
            "independently; the July-2026 paired D2/D4 local fits close all eight",
            "inputs while the programmed contents remain a separate boundary.",
            "",
            "## KiCad DSN Cross-check",
            "",
            "The saved routed DSN predates the five photo-traced address inputs.",
            "Its missing rows are a reroute boundary, not missing source evidence.",
            "",
            table_row(["Pin", "Role", "DSN Net", "Result"]),
            table_row(["---:", "---", "---", "---"]),
        ]
    )
    lines.extend(dsn_rows)
    lines.extend(
        [
            "",
            "## KiCad PCB Cross-check",
            "",
            "The authoritative PCB source exposes every proved D2 input and adds",
            "one idempotent solder-side segment for each D2-to-D4 address route.",
            "",
            table_row(["Pin", "Role", "PCB Net", "Result"]),
            table_row(["---:", "---", "---", "---"]),
        ]
    )
    lines.extend(pcb_rows)
    lines.extend(
        [
            "",
            "## Current Evidence Checks",
            "",
            table_row(["Check", "Result", "Evidence"]),
            table_row(["---", "---", "---"]),
            table_row([
                "Board identity names D2 as `.037` RT4",
                "PASS" if identity_ok else "FAIL",
                "`kicad/juku.board.json`",
            ]),
            table_row([
                "Any D2 signal net is traced",
                "PASS" if signal_nets else "FAIL",
                ", ".join(f"`{net}`" for net in signal_nets)
                if signal_nets
                else "no D2 signal nets in board JSON",
            ]),
            table_row([
                "Any D2 signal appears in DSN",
                "PASS" if dsn_nets else "FAIL",
                ", ".join(f"`{pin}`=`{net}`" for pin, net in sorted(dsn_nets.items()))
                if dsn_nets
                else "no D2 pins in DSN nets",
            ]),
            table_row([
                "Any D2 signal appears in PCB",
                "PASS" if pcb_nets else "FAIL",
                ", ".join(f"`{pin}`=`{net}`" for pin, net in sorted(pcb_nets.items()))
                if pcb_nets
                else "no D2 pins in PCB nets",
            ]),
            table_row([
                "256-row symbolic address table is non-burnable",
                "PASS" if symbolic_ok else "FAIL",
                "all D0 values are `?`" if symbolic_ok else "missing/malformed symbolic CSV",
            ]),
            table_row([
                "`.037` firmware artifact exists",
                "PASS" if candidates else "FAIL",
                ", ".join(f"`{item}`" for item in candidates)
                if candidates
                else "`ref/firmware/` has no `.037` artifact",
            ]),
            table_row([
                "Old D2-as-I/O-decode path is superseded",
                "PASS" if io_decoder_superseded else "FAIL",
                "`kicad/juku.board.json` D9 identity and provenance",
            ]),
            table_row([
                "No reconstructed D2 fallback is exported",
                "PASS" if fallback_boundary else "FAIL",
                "`docs/reconstructed-prom-fallbacks.md`",
            ]),
            table_row([
                "Official BOM/photo trail identifies `.037/.038` pair",
                "PASS" if official_bom_lead else "FAIL",
                "`ref/photos/juku-pcb-2/BODGE-TRIAGE.md`",
            ]),
            table_row([
                "Evidence summary preserves the traced D2 pin table",
                "PASS" if raw_pin_table_lead else "FAIL",
                "`ref/photos/juku-pcb-2/BODGE-TRIAGE.md`",
            ]),
            "",
            "## Evidence Reconciliation",
            "",
            "- The official `.009` BOM/photo reconciliation identifies D2 as `.037`",
            "  and D6 as `.038`.",
            "- The surviving sheet-1 evidence records the physical D2 pin table",
            "  `A0-A7=5/6/7/4/3/2/1/15`, `V1/V2=13/14`, `DO=12`, but explicitly",
            "  originally deferred the other five input nets.",
            "- The July-2026 two-sided D2 fit plus an independent D4 solder-row fit",
            "  now traces D2.1/.3/.5/.6/.7 to D4.1/.3/.5/.6/.7, closing all",
            "  physical inputs without claiming a burnable `.037` image.",
            "",
            "## Reconstruction Boundary",
            "",
            "- Known: D2 is a socketed К556РТ4 PROM and current project evidence",
            "  identifies it as programmed drawing `ДГШ5.106.037`.",
            "- Known: the older behavioral D2 I/O-decode model is not physical D2",
            "  programming truth; D9 is the current chip-select decoder.",
            "- Known: all eight D2 inputs and D0/pin 12 to D105.9 are routed in the",
            "  authoritative board model/source PCB. The saved routed snapshot",
            "  still predates the five new D2-to-D4 routes.",
            "- Known: D105.10 is a separate named off-sheet `H` input. The sheet's",
            "  power legend does not identify it as −5 V; that former assignment",
            "  masked D2 logically and has been removed from every PCB/route artifact.",
            "  The routed snapshot consequently carries one honest −5 V airwire; a legal",
            "  replacement route remains a fabrication blocker.",
            "- Simulation default: unresolved `H` defaults low to preserve the formerly",
            "  constant-low gate behavior, without claiming that `H` is a supply. The deep",
            "  cosim forces CPU `ready=1`, so its separate late mismatch cannot constrain H.",
            "- Unknown: the `.037` truth table; no programming table or dump is present",
            "  under `ref/firmware/`.",
            "- The factory sheet draws only D0/pin 12 from the four-output RT4",
            "  package; unused output pins 9-11 are explicit no-connects in the",
            "  board model and do not add unknown truth-table destinations.",
            "- Unknown: the source and timing of `H`; even a functional WAIT fallback",
            "  must preserve that input boundary rather than tie it to a supply.",
            "- Therefore a burnable D2 image is not derivable from current repo",
            "  evidence. The correct automatic action is to keep this constraint",
            "  report fresh; the data-unlocking action is a programming-disk file",
            "  or a repeated physical dump.",
            "",
        ]
    )
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    evidence_ok = all((identity_ok, io_decoder_superseded, fallback_boundary, official_bom_lead, raw_pin_table_lead, symbolic_ok))
    return 0 if evidence_ok and status != "D2 RECONSTRUCTION INPUTS CHANGED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
