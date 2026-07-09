#!/usr/bin/env python3
"""Generate the D94 .092 PROM reconstruction constraints report."""
from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "kicad" / "juku.board.json"
DSN = ROOT / "kicad" / "juku.dsn"
PCB = ROOT / "kicad" / "juku.kicad_pcb"
REPORT = ROOT / "docs" / "d94-reconstruction-constraints.md"
FIRMWARE = ROOT / "ref" / "firmware"
ARTIFACT_SCAN_DIRS = ("ref", "roms", "media", "docs", "hdl", "kicad", "scripts", "sync")


def read(path: str) -> str:
    return (ROOT / path).read_text(errors="replace")


def marker(path: str, *needles: str) -> bool:
    text = read(path)
    return all(needle in text for needle in needles)


def load_board() -> dict:
    return json.loads(BOARD.read_text())


def d94_chip(board: dict) -> dict:
    for chip in board["chips"]:
        if chip.get("ref") == "D94":
            return chip
    raise SystemExit("D94 not found in board JSON")


def net_for_pin(board: dict, ref: str, pin: str) -> tuple[str, str] | None:
    for name, net in board["nets"].items():
        for node in net.get("nodes", []):
            if node == [ref, pin]:
                return name, net.get("src", "")
    return None


def net_nodes(board: dict, name: str) -> list[list[str]]:
    return board["nets"].get(name, {}).get("nodes", [])


def format_nodes(nodes: list[list[str]]) -> str:
    if not nodes:
        return "-"
    return ", ".join(f"`{ref}.{pin}`" for ref, pin in nodes)


def dsn_pin_nets(ref: str) -> dict[str, str]:
    text = DSN.read_text(errors="replace")
    found: dict[str, str] = {}
    for match in re.finditer(r"\(net\s+([^\s()]+)\s+\(pins\s+([^)]*)\)\s*\)", text, flags=re.S):
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
    suffixes = (".092", ".092.hex", "_092.hex")
    return sorted(
        str(path.relative_to(ROOT))
        for path in FIRMWARE.iterdir()
        if path.name.lower().endswith(suffixes)
    )


def repo_092_artifact_candidates() -> list[str]:
    suffixes = (".092", ".092.hex", "_092.hex", "106.092", "106.092.hex")
    candidates: list[str] = []
    for dirname in ARTIFACT_SCAN_DIRS:
        base = ROOT / dirname
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            name = path.name.lower()
            if any(name.endswith(suffix) for suffix in suffixes):
                candidates.append(str(path.relative_to(ROOT)))
    return sorted(candidates)


def address_space_rows() -> list[str]:
    rows = []
    for address in range(32):
        ba = {
            "BA15": (address >> 4) & 1,
            "BA14": (address >> 3) & 1,
            "BA13": (address >> 2) & 1,
            "BA12": (address >> 1) & 1,
            "BA11": address & 1,
        }
        rows.append(
            "| "
            + f"{address:02d} | "
            + " | ".join(str(ba[name]) for name in ("BA15", "BA14", "BA13", "BA12", "BA11"))
            + " | unknown |"
        )
    return rows


def main() -> int:
    board = load_board()
    chip = d94_chip(board)
    pin_roles: dict[str, str] = chip.get("pins", {})
    address_pins = [(pin, role) for pin, role in pin_roles.items() if role.startswith("A")]
    output_pins = [(pin, role) for pin, role in pin_roles.items() if role.startswith("D")]
    enable_pins = [(pin, role) for pin, role in pin_roles.items() if role == "E_N"]
    board_type = str(chip.get("type", ""))
    board_identity_ok = board_type == "RE3_PROM_092"
    dsn_nets = dsn_pin_nets("D94")
    pcb_nets = pcb_pin_nets("D94")

    address_rows: list[str] = []
    address_ok = True
    for pin, role in sorted(address_pins, key=lambda item: item[1]):
        net = net_for_pin(board, "D94", pin)
        if net is None:
            address_ok = False
            address_rows.append(f"| {pin} | {role} | - | MISSING |")
        else:
            name, src = net
            address_rows.append(f"| {pin} | {role} | `{name}` | {src or '-'} |")

    output_rows: list[str] = []
    output_nets: list[str] = []
    for pin, role in sorted(output_pins, key=lambda item: int(item[0])):
        net = net_for_pin(board, "D94", pin)
        if net is None:
            output_rows.append(f"| {pin} | {role} | - | not traced/netted |")
        else:
            name, src = net
            output_nets.append(name)
            output_rows.append(f"| {pin} | {role} | `{name}` | {src or '-'} |")

    enable_rows: list[str] = []
    enable_ok = True
    for pin, role in enable_pins:
        net = net_for_pin(board, "D94", pin)
        if net is None:
            enable_ok = False
            enable_rows.append(f"| {pin} | {role} | - | MISSING |")
        else:
            name, src = net
            enable_rows.append(f"| {pin} | {role} | `{name}` | {src or '-'} |")

    dsn_pin_roles = dict(pin_roles)
    dsn_pin_roles.update({"8": "GND", "16": "VCC"})
    all_report_pins = sorted(dsn_pin_roles, key=lambda pin: int(pin))
    dsn_rows = []
    dsn_expected = {
        "8": "GND",
        "10": "BA11",
        "11": "BA12",
        "12": "BA13",
        "13": "BA14",
        "14": "BA15",
        "16": "P5V",
    }
    dsn_ok = True
    for pin in all_report_pins:
        role = dsn_pin_roles[pin]
        name = dsn_nets.get(pin)
        expected = dsn_expected.get(pin)
        if name is None:
            dsn_rows.append(f"| {pin} | {role} | - | missing in DSN |")
            if role.startswith("A"):
                dsn_ok = False
        else:
            result = "PASS" if expected is None or name == expected else f"expected `{expected}`"
            dsn_rows.append(f"| {pin} | {role} | `{name}` | {result} |")
            if expected is not None and name != expected:
                dsn_ok = False

    dsn_output_nets = [
        dsn_nets[pin]
        for pin, role in output_pins
        if pin in dsn_nets
    ]
    pcb_rows = []
    pcb_ok = bool(pcb_nets)
    for pin in all_report_pins:
        role = dsn_pin_roles[pin]
        name = pcb_nets.get(pin)
        expected = dsn_expected.get(pin)
        if name is None:
            pcb_rows.append(f"| {pin} | {role} | - | unnetted in PCB |")
            if role.startswith("A"):
                pcb_ok = False
        else:
            result = "PASS" if expected is None or name == expected else f"expected `{expected}`"
            pcb_rows.append(f"| {pin} | {role} | `{name}` | {result} |")
            if expected is not None and name != expected:
                pcb_ok = False
    pcb_output_nets = [
        pcb_nets[pin]
        for pin, role in output_pins
        if pin in pcb_nets
    ]
    d94_signal_pins = [pin for pin, role in pin_roles.items() if role.startswith("D") or role == "E_N"]
    v3_rc_nodes = net_nodes(board, "V3_RC")
    v3_rc_board_no_d94 = bool(v3_rc_nodes) and all(node[0] != "D94" for node in v3_rc_nodes)
    v3_rc_dsn_no_d94 = all(dsn_nets.get(pin) != "V3_RC" for pin in d94_signal_pins)
    v3_rc_pcb_no_d94 = all(pcb_nets.get(pin) != "V3_RC" for pin in d94_signal_pins)
    v3_rc_not_d94_evidence = v3_rc_board_no_d94 and v3_rc_dsn_no_d94 and v3_rc_pcb_no_d94

    candidates = firmware_candidates()
    repo_candidates = repo_092_artifact_candidates()
    hdl_placeholder = marker(
        "hdl/devices.v",
        "module re3_prom_092",
        "D94 = programmed part ДГШ5.106.092",
        "assign d = 8'hFF",
    )
    hdl_unconnected = marker("hdl/juku_top.v", "re3_prom_092 U_D94", ".d()")
    official_bom_lead = marker(
        "ref/photos/juku-pcb-2/BODGE-TRIAGE.md",
        "D94 = К155РЕ3 #2",
        "progr. .092",
    )
    reused_refdes_guard = marker(
        "ref/photos/juku-pcb-2/BODGE-TRIAGE.md",
        "sheet-3's D94-D108 refdes were re-used for the FDC-era parts",
        "The drawing's D94-D108 are the К561 CMOS TAPE cluster",
    )
    historical_113_conflict = marker(
        "ref/photos/juku-pcb-2/BODGE-TRIAGE.md",
        ".113 (D94): a 2K-granular decode of A000-BFFF",
        "role-assumed; .113 -> D94",
    )
    scanned_not_d94 = marker(
        "docs/re3-firmware-inspection.md",
        "Status: **PASS**",
        "D94 `.092`",
        "neither table is present",
    )
    video_audit_pending = marker(
        "docs/video-slot-timing-audit.md",
        "Status: **VIDEO SLOT TIMING AUDITED / D94 PROM DUMP PENDING**",
    )

    can_reconstruct = (
        address_ok
        and enable_ok
        and bool(output_nets)
        and bool(dsn_output_nets)
        and bool(candidates)
    )
    status = "D94 RECONSTRUCTION READY" if can_reconstruct else "D94 RECONSTRUCTION CONSTRAINED / DUMP REQUIRED"

    lines = [
        "# D94 .092 reconstruction constraints",
        "",
        f"Status: **{status}**",
        "",
        "This generated report records what the repo can currently prove about",
        "the .009 FDC-era `D94` К155РЕ3 PROM (`ДГШ5.106.092`) before attempting",
        "any reverse-engineered or burnable replacement table.",
        "",
        "## Command",
        "",
        "```sh",
        "python3 scripts/report_d94_reconstruction_constraints.py",
        "```",
        "",
        "## Address / Enable Pins",
        "",
        f"Board identity: D94 type is `{board_type or 'missing'}`.",
        "",
        "Address summary: D94.10-D94.14 map to `BA11..BA15` in the board JSON.",
        "",
        "| Pin | Role | Net | Source |",
        "| ---: | --- | --- | --- |",
    ]
    lines.extend(address_rows)
    lines.extend(enable_rows)
    lines.extend(
        [
            "",
            "## Output Pins",
            "",
            "| Pin | Role | Net | Source |",
            "| ---: | --- | --- | --- |",
        ]
    )
    lines.extend(output_rows)
    lines.extend(
        [
            "",
            "## KiCad DSN Cross-check",
            "",
            "The routed DSN independently exposes only D94 power/ground and address",
            "connections. It does not provide the missing enable/output nets.",
            "",
            "| Pin | Role | DSN Net | Result |",
            "| ---: | --- | --- | --- |",
        ]
    )
    lines.extend(dsn_rows)
    lines.extend(
        [
            "",
            "## KiCad PCB Cross-check",
            "",
            "The authoritative PCB file agrees with the DSN: D94 has power/ground and",
            "address nets only; enable and all data outputs remain unnetted there too.",
            "",
            "| Pin | Role | PCB Net | Result |",
            "| ---: | --- | --- | --- |",
        ]
    )
    lines.extend(pcb_rows)
    lines.extend(
        [
            "",
            "## Current Evidence Checks",
            "",
            "| Check | Result | Evidence |",
            "| --- | --- | --- |",
            f"| Board identity names D94 as `.092`, not stale `.113` | {'PASS' if board_identity_ok else 'FAIL'} | `kicad/juku.board.json` type `{board_type or 'missing'}` |",
            f"| Address pins D94.10-D94.14 are traced | {'PASS' if address_ok else 'FAIL'} | board JSON nets |",
            f"| DSN agrees on D94 power/address and lacks output nets | {'PASS' if dsn_ok and not dsn_output_nets else 'FAIL'} | `kicad/juku.dsn` D94 pins |",
            f"| PCB agrees on D94 power/address and lacks output nets | {'PASS' if pcb_ok and not pcb_output_nets else 'FAIL'} | `kicad/juku.kicad_pcb` D94 footprint pads |",
            f"| `V3_RC` is present but not D94 enable/output evidence | {'PASS' if v3_rc_not_d94_evidence else 'FAIL'} | board nodes {format_nodes(v3_rc_nodes)}; DSN/PCB D94 signal pins are not on `V3_RC` |",
            f"| Enable pin D94.15 is traced | {'PASS' if enable_ok else 'FAIL'} | board JSON nets |",
            f"| Any D94 output net is traced | {'PASS' if output_nets else 'FAIL'} | {', '.join(f'`{n}`' for n in output_nets) if output_nets else 'no D94 output nets in board JSON'} |",
            f"| `.092` firmware artifact exists | {'PASS' if candidates else 'FAIL'} | {', '.join(f'`{c}`' for c in candidates) if candidates else '`ref/firmware/` has no `.092` artifact'} |",
            f"| Repository-wide `.092` artifact filename exists | {'PASS' if repo_candidates else 'FAIL'} | {', '.join(f'`{c}`' for c in repo_candidates) if repo_candidates else 'no `.092` / `106.092` artifact filename under ref/roms/media/docs/hdl/kicad/scripts/sync'} |",
            f"| Official .009 BOM/photo notes identify D94 as `.092` | {'PASS' if official_bom_lead else 'FAIL'} | `ref/photos/juku-pcb-2/BODGE-TRIAGE.md` iteration 68 |",
            f"| Reused D94 refdes/tape-cluster history is guarded | {'PASS' if reused_refdes_guard else 'FAIL'} | `ref/photos/juku-pcb-2/BODGE-TRIAGE.md` iterations 56/68 |",
            f"| Historical `.113 -> D94` assumption is still visible as a conflict | {'PASS' if historical_113_conflict else 'FAIL'} | `ref/photos/juku-pcb-2/BODGE-TRIAGE.md` iterations 68/70 |",
            f"| `.113/.117` scans are guarded as not-D94 | {'PASS' if scanned_not_d94 else 'FAIL'} | `docs/re3-firmware-inspection.md` |",
            f"| HDL placeholder is explicitly inert | {'PASS' if hdl_placeholder else 'FAIL'} | `hdl/devices.v::re3_prom_092` |",
            f"| `juku_top` leaves D94 data outputs unconnected | {'PASS' if hdl_unconnected else 'FAIL'} | `hdl/juku_top.v` |",
            f"| Video slot audit is still D94-pending | {'PASS' if video_audit_pending else 'FAIL'} | `docs/video-slot-timing-audit.md` |",
            "",
            "## Textual / Photo Survey Leads",
            "",
            "- The official .009 BOM trail identifies the FDC-era D94 as the second",
            "  К155РЕ3, programmed as `ДГШ5.106.092`.",
            "- Earlier D94 references in the sheet-3/tape-cluster survey are known",
            "  refdes reuse history, not evidence for the FDC-era timing PROM.",
            "- The old `.113 -> D94` note remains in the raw campaign log, but the",
            "  current guarded firmware inspection supersedes it: `.113/.117` belong",
            "  to the `.106.103`-family owner-scan evidence and are not a burnable",
            "  D94 `.092` substitute.",
            "- These textual leads establish identity and negative evidence only. They",
            "  do not provide D94 pin 15, D0-D7 destinations, or PROM contents.",
            "- The nearby `V3_RC` RC node is traced as `R17.1`, `C99.1`, and `D9.6`",
            "  in board JSON/DSN, but D94 pin 15 and D0-D7 are not tied to it in",
            "  board JSON, DSN, or PCB evidence. It cannot substitute for the missing",
            "  D94 enable/output continuity.",
            "",
            "## Address Space",
            "",
            "D94 is a 32 x 8 PROM. The address pins are traced, so the reachable",
            "rows are mechanically known, but every row byte is still unknown because",
            "the D0-D7 destinations and `.092` programming table/dump are absent.",
            "",
            "| Row | BA15 | BA14 | BA13 | BA12 | BA11 | D7..D0 |",
            "| ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    lines.extend(address_space_rows())
    lines.extend(
        [
            "",
            "## Reconstruction Boundary",
            "",
            "- Known: D94 is present in the .009 FDC quadrant and its five address",
            "  inputs are wired to `BA11..BA15`.",
            "- Unknown: D94 pin 15 (`E_N`) and the eight D94 output destinations are",
            "  not traced/netted in `kicad/juku.board.json`, `kicad/juku.dsn`,",
            "  `kicad/juku.kicad_pcb`, or the audited text/photo notes, and no",
            "  `ДГШ5.106.092` programming table or dump is present under the",
            "  repository artifact scan.",
            "- The traced `V3_RC` RC network is a negative cross-check here, not a",
            "  replacement source for D94: its current nodes are `R17.1`, `C99.1`,",
            "  and `D9.6`, with no D94 signal endpoint in JSON, DSN, or PCB.",
            "- Content ambiguity alone is 256 unknown bits (`2^256` possible 32-byte",
            "  PROM tables) before even assigning those bits to physical destination",
            "  nets or enable timing.",
            "- Therefore a burnable D94 image is not derivable from current repo",
            "  evidence. The correct next automatic action is to keep this constraint",
            "  report fresh; the next data-unlocking action is an owner dump or a",
            "  recovered programming-disk `.092` table.",
            "- Do not reuse `.113` or `.117` as D94: those scans are guarded as",
            "  `.106.103`-family evidence, not the processor-module `.092` content.",
        ]
    )

    REPORT.write_text("\n".join(lines) + "\n")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    print(f"Status: {status}")
    return 0 if (
        board_identity_ok
        and address_ok
        and dsn_ok
        and pcb_ok
        and official_bom_lead
        and reused_refdes_guard
        and historical_113_conflict
        and v3_rc_not_d94_evidence
        and hdl_placeholder
        and hdl_unconnected
        and scanned_not_d94
        and video_audit_pending
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
