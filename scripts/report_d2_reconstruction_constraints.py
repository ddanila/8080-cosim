#!/usr/bin/env python3
"""Generate the D2 .037 PROM reconstruction constraints report."""
from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "kicad" / "juku.board.json"
DSN = ROOT / "kicad" / "juku.dsn"
PCB = ROOT / "kicad" / "juku.kicad_pcb"
REPORT = ROOT / "docs" / "d2-reconstruction-constraints.md"
FIRMWARE = ROOT / "ref" / "firmware"


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
        net = re.search(r'\(net\s+"([^"]+)"\)', pad_block)
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
    identity_ok = board_type == "DEC_PROM" and "ДГШ5.106.037" in str(prov)
    io_decoder_superseded = marker(
        "docs/transcription/io.md",
        "D2 = К556РТ4",
        "bus-arbitration/wait PROM",
        "must not be treated as a burnable I/O-decode image",
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
    status = (
        "D2 RECONSTRUCTION CONSTRAINED / DUMP REQUIRED"
        if identity_ok and not signal_nets and not dsn_nets and not pcb_nets and not candidates
        else "D2 RECONSTRUCTION INPUTS CHANGED"
    )

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
            "## KiCad DSN Cross-check",
            "",
            "The routed DSN currently exposes no D2 signal nets. This agrees with",
            "the deferred-net boundary in `kicad/juku.board.json`.",
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
            "The final PCB source currently exposes no D2 signal pad nets. This",
            "agrees with the deferred-net boundary in `kicad/juku.board.json`",
            "and `kicad/juku.dsn`.",
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
                "`.037` firmware artifact exists",
                "PASS" if candidates else "FAIL",
                ", ".join(f"`{item}`" for item in candidates)
                if candidates
                else "`ref/firmware/` has no `.037` artifact",
            ]),
            table_row([
                "Old D2-as-I/O-decode path is superseded",
                "PASS" if io_decoder_superseded else "FAIL",
                "`docs/transcription/io.md`",
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
            "",
            "## Reconstruction Boundary",
            "",
            "- Known: D2 is a socketed К556РТ4 PROM and current project evidence",
            "  identifies it as programmed drawing `ДГШ5.106.037`.",
            "- Known: the older behavioral D2 I/O-decode model is not physical D2",
            "  programming truth; D9 is the current chip-select decoder.",
            "- Unknown: D2 address/input rails, V1/V2 handling, D0 destination, and",
            "  `.037` contents are not traced/netted in current board JSON, DSN,",
            "  or final PCB source, and no programming table or dump is present",
            "  under `ref/firmware/`.",
            "- Therefore a burnable D2 image is not derivable from current repo",
            "  evidence. The correct automatic action is to keep this constraint",
            "  report fresh; the data-unlocking action is a programming-disk file",
            "  or a repeated physical dump.",
            "",
        ]
    )
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    return 0 if status == "D2 RECONSTRUCTION CONSTRAINED / DUMP REQUIRED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
