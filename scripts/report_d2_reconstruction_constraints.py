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
    "2": ("IORC_N", "sheet 1 label `-XACK` enters D2 A5/pin 2 at X1/D29 `-IORC` coordinate 106C"),
    "15": ("WREQ_N", "sheet 1 label `-WREQ` enters D2 A7/pin 15"),
    # The saved DSN still contains the older D2_WAIT_RAW interpretation, but
    # direct owner continuity supersedes it in the authoritative source model.
    "12": ("READY_D", "owner continuity: D2 D0/pin 12 enters D30 pin 2 and R6"),
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
    intentional_nc = {str(pin) for ref, pin in board.get("no_connects", []) if ref == "D2"}
    nc_outputs_ok = intentional_nc == {"9", "10", "11"}

    pin_rows: list[str] = []
    signal_nets: list[str] = []
    for pin, role in sorted(pin_roles.items(), key=role_key):
        net = net_for_pin(board, "D2", pin)
        if net is None:
            if pin in intentional_nc:
                pin_rows.append(table_row([pin, role, "NC", "factory symbol draws only D0/pin12; explicit no-connect"] ))
            else:
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
                "present" if name else "intentional NC in source" if pin in intentional_nc else "missing in DSN",
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
                "present" if name else "intentional NC" if pin in intentional_nc else "unnetted in PCB",
            ])
        )

    candidates = firmware_candidates()
    physical_image = ROOT / "ref/physical-proms/validated/d2_037.raw.bin"
    physical_image_ok = physical_image.exists() and physical_image.stat().st_size == 256
    symbolic_rows = list(csv.DictReader(SYMBOLIC.open())) if SYMBOLIC.exists() else []
    symbolic_ok = (
        len(symbolic_rows) == 256
        and all(row.get("D0") == "?" for row in symbolic_rows)
        and symbolic_rows[0].get("prom_address_hex") == "0x00"
        and symbolic_rows[-1].get("prom_address_hex") == "0xFF"
    )
    identity_ok = board_type == "WAIT_PROM" and "ДГШ5.106.037" in str(prov)
    d9 = next((item for item in board["chips"] if item.get("ref") == "D9"), {})
    io_decoder_superseded = (
        d9.get("type") == "IO_DEC138"
        and "Physical D2 is a separate КР556РТ4 bus/wait part" in str(d9.get("prov", {}))
    )
    fallback_boundary = marker(
        "docs/reconstructed-prom-fallbacks.md",
        "PHYSICAL RT4 TABLES ADOPTED",
        "953be4bf899e02f0885ecef53e4f9d26469b8d78ceea87394aa35cd28df0255b",
    )
    owner_evidence = marker(
        "docs/d2-physical-dump-and-continuity.md",
        "Three preserved complete reads agreed",
        "D2.12  <-> D30.2",
        "D105.9  <-> D1.17 DBIN",
        "D13.12 <-> D6.11 <-> D6.12",
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
        "preserve the physical `.037` table",
        "pins 9-11 have no destination and are explicit no-connects",
    )
    all_signal_pins_netted = (
        len(signal_nets) == len(pin_roles)
        and len(dsn_nets) >= len(pin_roles)
        and len(pcb_nets) >= len(pin_roles)
    )
    address_pins = {"1", "2", "3", "4", "5", "6", "7", "15"}
    source_inputs_closed = all(net_for_pin(board, "D2", pin) for pin in address_pins)
    source_inputs_in_pcb = all(pin in pcb_nets for pin in address_pins)
    if identity_ok and source_inputs_closed and physical_image_ok and owner_evidence:
        status = "D2 PHYSICAL TABLE ADOPTED / CONNECTIVITY GUARDED"
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
        "the processor-board `D2` К556РТ4 PROM (`ДГШ5.106.037`). It separates",
        "the validated physical table from older reconstruction assumptions.",
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
            "256 input vectors. Its D0 cells remain `?` as a topology constraint;",
            "the separately named validated raw programming image carries the",
            "owner-observed values without rewriting this historical constraint file.",
            "",
            "The named schematic leads above are pin-level source evidence, not a",
            "claim that the D2 truth table is known. Each proved pin is promoted",
            "independently; the July-2026 paired D2/D4 local fits close all eight",
            "inputs. Three validated owner captures, including a separate power cycle,",
            "now establish the physical raw table.",
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
                "D2 unused outputs are explicit no-connects",
                "PASS" if nc_outputs_ok else "FAIL",
                "pins 9, 10, 11; factory symbol draws only D0/pin12",
            ]),
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
                "Validated physical `.037` raw programming image exists",
                "PASS" if physical_image_ok else "FAIL",
                "`ref/physical-proms/validated/d2_037.raw.bin`"
                if physical_image_ok else "missing or not 256 bytes",
            ]),
            table_row([
                "Old D2-as-I/O-decode path is superseded",
                "PASS" if io_decoder_superseded else "FAIL",
                "`kicad/juku.board.json` D9 identity and provenance",
            ]),
            table_row([
                "D2 physical-table provenance is preserved",
                "PASS" if fallback_boundary else "FAIL",
                "`docs/reconstructed-prom-fallbacks.md`",
            ]),
            table_row([
                "Owner dump and corrected continuity are recorded",
                "PASS" if owner_evidence else "FAIL",
                "`docs/d2-physical-dump-and-continuity.md`",
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
            "- Direct owner continuity supersedes the false D2.12->D105.9 path:",
            "  D2.12 joins D30.2 and R6 in the READY latch input.",
            "- Two complete same-session reads matched at every address with zero",
            "  unstable rows; all four outputs agreed. A third separately power-cycled",
            "  capture validates to the same authoritative raw SHA256.",
            "",
            "## Reconstruction Boundary",
            "",
            "- Known: D2 is a socketed К556РТ4 PROM and current project evidence",
            "  identifies it as programmed drawing `ДГШ5.106.037`.",
            "- Known: the older behavioral D2 I/O-decode model is not physical D2",
            "  programming truth; D9 is the current chip-select decoder.",
            "- Known: all eight inputs are traced and D0/pin12 feeds D30 READY data.",
            "  The factory symbol draws only D0; pins9-11 are explicit no-connects.",
            "- Known: D105.10 is the pulled-up edge-bus `H` net shared with D13.13;",
            "  it gates CPU DBIN through D105 into D5 and is not the −5 V supply.",
            "- Known: `ref/physical-proms/validated/d2_037.raw.bin` is the 256-byte",
            "  authoritative raw low-nibble image, reproduced from all three captures.",
            "- Remaining closure is historical comparison against a programming-disk",
            "  file or independent future read, not recovery of the current chip table.",
            "",
        ]
    )
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    evidence_ok = all((identity_ok, io_decoder_superseded, fallback_boundary, official_bom_lead, raw_pin_table_lead, symbolic_ok, physical_image_ok, owner_evidence, nc_outputs_ok))
    return 0 if evidence_ok and status != "D2 RECONSTRUCTION INPUTS CHANGED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
