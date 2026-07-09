#!/usr/bin/env python3
"""Generate the D94 .092 PROM reconstruction constraints report."""
from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "kicad" / "juku.board.json"
DSN = ROOT / "kicad" / "juku.dsn"
REPORT = ROOT / "docs" / "d94-reconstruction-constraints.md"
FIRMWARE = ROOT / "ref" / "firmware"


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


def firmware_candidates() -> list[str]:
    if not FIRMWARE.exists():
        return []
    suffixes = (".092", ".092.hex", "_092.hex")
    return sorted(
        str(path.relative_to(ROOT))
        for path in FIRMWARE.iterdir()
        if path.name.lower().endswith(suffixes)
    )


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

    candidates = firmware_candidates()
    hdl_placeholder = marker(
        "hdl/devices.v",
        "module re3_prom_092",
        "D94 = programmed part ДГШ5.106.092",
        "assign d = 8'hFF",
    )
    hdl_unconnected = marker("hdl/juku_top.v", "re3_prom_092 U_D94", ".d()")
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
            "## Current Evidence Checks",
            "",
            "| Check | Result | Evidence |",
            "| --- | --- | --- |",
            f"| Board identity names D94 as `.092`, not stale `.113` | {'PASS' if board_identity_ok else 'FAIL'} | `kicad/juku.board.json` type `{board_type or 'missing'}` |",
            f"| Address pins D94.10-D94.14 are traced | {'PASS' if address_ok else 'FAIL'} | board JSON nets |",
            f"| DSN agrees on D94 power/address and lacks output nets | {'PASS' if dsn_ok and not dsn_output_nets else 'FAIL'} | `kicad/juku.dsn` D94 pins |",
            f"| Enable pin D94.15 is traced | {'PASS' if enable_ok else 'FAIL'} | board JSON nets |",
            f"| Any D94 output net is traced | {'PASS' if output_nets else 'FAIL'} | {', '.join(f'`{n}`' for n in output_nets) if output_nets else 'no D94 output nets in board JSON'} |",
            f"| `.092` firmware artifact exists | {'PASS' if candidates else 'FAIL'} | {', '.join(f'`{c}`' for c in candidates) if candidates else '`ref/firmware/` has no `.092` artifact'} |",
            f"| `.113/.117` scans are guarded as not-D94 | {'PASS' if scanned_not_d94 else 'FAIL'} | `docs/re3-firmware-inspection.md` |",
            f"| HDL placeholder is explicitly inert | {'PASS' if hdl_placeholder else 'FAIL'} | `hdl/devices.v::re3_prom_092` |",
            f"| `juku_top` leaves D94 data outputs unconnected | {'PASS' if hdl_unconnected else 'FAIL'} | `hdl/juku_top.v` |",
            f"| Video slot audit is still D94-pending | {'PASS' if video_audit_pending else 'FAIL'} | `docs/video-slot-timing-audit.md` |",
            "",
            "## Reconstruction Boundary",
            "",
            "- Known: D94 is present in the .009 FDC quadrant and its five address",
            "  inputs are wired to `BA11..BA15`.",
            "- Unknown: D94 pin 15 (`E_N`) and the eight D94 output destinations are",
            "  not traced/netted in `kicad/juku.board.json` or `kicad/juku.dsn`, and no",
            "  `ДГШ5.106.092` programming table or dump is present under",
            "  `ref/firmware/`.",
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
    return 0 if board_identity_ok and address_ok and dsn_ok and hdl_placeholder and hdl_unconnected and scanned_not_d94 and video_audit_pending else 1


if __name__ == "__main__":
    raise SystemExit(main())
