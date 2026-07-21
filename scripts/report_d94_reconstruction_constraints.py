#!/usr/bin/env python3
"""Generate the D94 .092 PROM reconstruction constraints report."""
from __future__ import annotations

import json
import re
import csv
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "kicad" / "juku.board.json"
DSN = ROOT / "kicad" / "juku.dsn"
PCB = ROOT / "kicad" / "juku.kicad_pcb"
REPORT = ROOT / "docs" / "d94-reconstruction-constraints.md"
FIRMWARE = ROOT / "ref" / "firmware"
ARTIFACT_SCAN_DIRS = ("ref", "roms", "media", "docs", "hdl", "kicad", "scripts", "sync")
PHOTO_ENDPOINTS = ROOT / "ref" / "photos" / "juku-pcb-2" / "endpoints.csv"
PHYSICAL_D94 = ROOT / "ref" / "physical-proms" / "validated" / "d94_092.raw.bin"
PHYSICAL_D94_SHA256 = "bcf942a87ee70adb1a16cebb7f018cf8f491ea2a74db0b0a5dd7d5c8db8a29e0"


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
        net = re.search(r'\(net\s+\d+\s+"([^"]+)"\)', pad_block)
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


def remaining_output_departures() -> dict[str, str]:
    """Return component-side observations proving copper leaves D94 D3-D7 pads."""
    observations: dict[str, str] = {}
    with PHOTO_ENDPOINTS.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row.get("refdes") != "D94" or row.get("pin") not in {"4", "5", "6", "7", "9"}:
                continue
            if not row.get("endpoint_id", "").startswith("seed-component-"):
                continue
            note = row.get("note", "")
            if "copper" in note or "trace runs" in note or "local departure" in note:
                observations[row["pin"]] = note
    return observations


def address_input_observations() -> dict[str, dict[str, str]]:
    """Return reviewed two-sided local-fit records for D94 A0-A4."""
    observations: dict[str, dict[str, str]] = {}
    with PHOTO_ENDPOINTS.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            pin = row.get("pin", "")
            if row.get("refdes") != "D94" or pin not in {"10", "11", "12", "13", "14"}:
                continue
            endpoint_id = row.get("endpoint_id", "")
            side = (
                "component" if endpoint_id.startswith("seed-component-")
                else "solder" if endpoint_id.startswith("seed-solder-")
                else ""
            )
            if (
                side
                and row.get("confidence") == "local-package-fit"
                and row.get("review_state") == "measurement"
                and row.get("reviewer")
            ):
                observations.setdefault(pin, {})[side] = (
                    f"{row.get('image', '-')}@({row.get('x_px', '-')},{row.get('y_px', '-')})"
                )
    return observations


def address_space_rows(table: bytes) -> list[str]:
    rows = []
    for address in range(32):
        inputs = {f"A{bit}": (address >> bit) & 1 for bit in range(5)}
        rows.append(
            "| "
            + f"{address:02d} | "
            + " | ".join(str(inputs[name]) for name in ("A4", "A3", "A2", "A1", "A0"))
            + f" | `{table[address]:02X}` |"
        )
    return rows


def verify_minimized_logic(table: bytes) -> bool:
    """Exhaustively guard the minimized active-low output equations."""
    if len(table) != 32:
        return False
    for address, value in enumerate(table):
        a0 = bool(address & 0x01)
        a1 = bool(address & 0x02)
        a2 = bool(address & 0x04)
        a3 = bool(address & 0x08)
        a4 = bool(address & 0x10)
        qualify = a4 or not a1 or not a0
        expected_asserted = (
            (not a4) and a1 and a0,
            a3 != a2,
            a3 and (not a2) and qualify,
            (not a3) and a2 and qualify,
            False,
            False,
            False,
            False,
        )
        captured_asserted = tuple(not bool(value & (1 << bit)) for bit in range(8))
        if captured_asserted != expected_asserted:
            return False
    return True


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
    physical_table = PHYSICAL_D94.read_bytes() if PHYSICAL_D94.exists() else b""
    physical_table_ok = (
        len(physical_table) == 32
        and hashlib.sha256(physical_table).hexdigest() == PHYSICAL_D94_SHA256
    )

    address_rows: list[str] = []
    address_accounted = True
    address_traced = True
    for pin, role in sorted(address_pins, key=lambda item: item[1]):
        net = net_for_pin(board, "D94", pin)
        if net is None:
            address_accounted = False
            address_traced = False
            address_rows.append(f"| {pin} | {role} | - | MISSING |")
        else:
            name, src = net
            address_rows.append(f"| {pin} | {role} | `{name}` | {src or '-'} |")
            if re.search(r"boundary|unresolved|unknown|retired|assumption", f"{name} {src}", re.I):
                address_traced = False

    output_rows: list[str] = []
    output_nets: list[str] = []
    output_asserted_rows: dict[str, list[int]] = {}
    for pin, role in sorted(output_pins, key=lambda item: int(item[0])):
        bit = int(role[1:])
        asserted = [row for row, value in enumerate(physical_table) if not (value & (1 << bit))]
        output_asserted_rows[role] = asserted
        activity = (
            "invariant released"
            if not asserted
            else "asserts at rows " + ", ".join(f"{row:02d}" for row in asserted)
        )
        net = net_for_pin(board, "D94", pin)
        if net is None:
            if ["D94", pin] in board.get("no_connects", []):
                output_nets.append("NC")
                output_rows.append(f"| {pin} | {role} | `NC` | {activity} | owner/photo-confirmed PCB no-connect |")
            else:
                output_rows.append(f"| {pin} | {role} | - | {activity} | not traced/netted |")
        else:
            name, src = net
            output_nets.append(name)
            output_rows.append(f"| {pin} | {role} | `{name}` | {activity} | {src or '-'} |")

    enable_rows: list[str] = []
    enable_ok = True
    enable_accounted = False
    for pin, role in enable_pins:
        net = net_for_pin(board, "D94", pin)
        if net is None:
            enable_ok = False
            enable_rows.append(f"| {pin} | {role} | - | MISSING |")
        else:
            name, src = net
            enable_accounted = True
            enable_rows.append(f"| {pin} | {role} | `{name}` | {src or '-'} |")
            if re.search(r"boundary|unresolved|cannot be uniquely|unknown|pending", src, re.I):
                enable_ok = False
    enable_output_isolated = net_for_pin(board, "D94", "15")[0] != net_for_pin(board, "D94", "2")[0]

    dsn_pin_roles = dict(pin_roles)
    dsn_pin_roles.update({"8": "GND", "16": "VCC"})
    all_report_pins = sorted(dsn_pin_roles, key=lambda pin: int(pin))
    dsn_rows = []
    retired_dsn_inputs = {"10": "BA11", "11": "BA12", "12": "BA13", "13": "BA14", "14": "BA15"}
    dsn_expected = {
        pin: net_for_pin(board, "D94", pin)[0]
        for pin in all_report_pins
        if net_for_pin(board, "D94", pin) is not None
    }
    dsn_ok = True
    for pin in all_report_pins:
        role = dsn_pin_roles[pin]
        name = dsn_nets.get(pin)
        expected = dsn_expected.get(pin)
        if name is None:
            dsn_rows.append(f"| {pin} | {role} | - | missing in DSN |")
        else:
            result = "PASS" if expected is None or name == expected else f"expected `{expected}`"
            dsn_rows.append(f"| {pin} | {role} | `{name}` | {result} |")
            if expected is not None and name != expected:
                dsn_ok = False
    dsn_retains_retired_inputs = all(
        dsn_nets.get(pin) == name for pin, name in retired_dsn_inputs.items()
    )
    dsn_matches_source_model = dsn_ok and not dsn_retains_retired_inputs

    dsn_output_nets = [
        dsn_nets[pin]
        for pin, role in output_pins
        if pin in dsn_nets
    ]
    pcb_rows = []
    pcb_ok = bool(pcb_nets)
    pcb_expected = {
        **dsn_expected,
        "10": "BA0",
        "11": "BA1",
        "12": "IORD",
        "13": "IOWR",
        "14": "D94_A4_D101_Q0",
    }
    for pin in all_report_pins:
        role = dsn_pin_roles[pin]
        name = pcb_nets.get(pin)
        expected = pcb_expected.get(pin)
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

    candidates = [str(PHYSICAL_D94.relative_to(ROOT))] if physical_table_ok else []
    repo_candidates = candidates
    hdl_physical_table = marker(
        "hdl/devices.v",
        "module re3_prom_092",
        "three matching reads",
        "assign d[0] = (!e_n && !raw[0])",
    )
    hdl_connected = marker("hdl/juku_top.v", "re3_prom_092 U_D94", "fdc_prom_re_n", "fdc_prom_cs_n", "fdc_prom_we_n")
    hdl_runnable_physical = marker(
        "hdl/juku_top.v",
        "Runnable behavioral core consumes the physical .092 PROM strobes",
        "wire fdc_model_cs_n = fdc_prom_cs_n;",
        "wire fdc_model_re_n = fdc_prom_re_n;",
        "wire fdc_model_we_n = fdc_prom_we_n;",
    ) and marker(
        "hdl/sim/juku_top_periph_bus_tb.v",
        "D94 /RE did not assert during FDC read",
        "D94 /WE did not assert during FDC write",
        "D94 D0 did not assert for low-A4 register-3 cycle",
    )
    hdl_inputs_measured = marker(
        "hdl/juku_top.v",
        "Owner continuity supersedes",
        "iowr_n, iord_n, BA[1], BA[0]",
        "D104.7 is separate (~84 kohm to A3)",
    )
    pcb_outputs_match = all(pcb_nets.get(pin) == net_for_pin(board, "D94", pin)[0]
                            for pin, _ in output_pins if net_for_pin(board, "D94", pin))
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
    scanned_not_d94 = marker(
        "docs/re3-firmware-inspection.md",
        "Status: **PASS**",
        "D94 `.092`",
        "neither scanned table represents those parts",
    )
    programming_media_audited = marker(
        "docs/vendored-disk-catalog.md",
        "## Programming-media PROM search",
        "media/disks/JUKPROG1.CPM | D94 .092 | 79 | 76 | none",
        "media/disks/JUKPROG2.CPM | D94 .092 | 49 | 76 | none",
        "media/disks/JUKPROGX.CPM | D94 .092 | 25 | 76 | none",
        "a proprietary, permuted, compressed, or otherwise transformed encoding",
    )
    video_audit_independent = marker(
        "docs/video-slot-timing-audit.md",
        "Status: **VIDEO SLOT TIMING AUDITED / PHYSICAL SLOT SCHEDULE PENDING**",
        "D94 is not used as video-timing evidence",
    )
    output_departures = remaining_output_departures()
    # The old pin-4 boundary was superseded by direct D94.4->D93.2 continuity.
    # Full-resolution review makes D4/pin5 an explicit NC, separate from D93.1's stub.
    # Photo evidence records local copper departures, while exact-revision drawing
    # review plus owner continuity closes D5-D7 as electrically NC.
    d5_d7_owner_closed_nc = all(
        net_for_pin(board, "D94", pin) is not None
        and len(net_nodes(board, net_for_pin(board, "D94", pin)[0])) == 1
        and "electrically NC" in net_for_pin(board, "D94", pin)[1]
        for pin in ("6", "7", "9")
    ) and set(output_departures) >= {"6", "7", "9"}
    address_observations = address_input_observations()
    all_address_inputs_registered = (
        set(address_observations) == {"10", "11", "12", "13", "14"}
        and all(set(sides) == {"component", "solder"} for sides in address_observations.values())
    )
    retired_ba_mapping_absent = all(
        ["D94", str(pin)] not in net_nodes(board, f"BA{pin + 1}")
        for pin in range(10, 15)
    )
    active_outputs = {role for role, rows in output_asserted_rows.items() if rows}
    output_activity_ok = active_outputs == {"D0", "D1", "D2", "D3"}
    minimized_logic_ok = verify_minimized_logic(physical_table)

    status = "D94 PHYSICAL TABLE ADOPTED / CONNECTIVITY GUARDED" if physical_table_ok else "D94 PHYSICAL TABLE FAILED"

    lines = [
        "# D94 .092 reconstruction constraints",
        "",
        f"Status: **{status}**",
        "",
        "This generated report records what the repo can currently prove about",
        "the .009 FDC-era `D94` К155РЕ3 PROM (`ДГШ5.106.092`). Its repeated",
        "physical table is now burnable truth; unresolved connectivity is kept separate.",
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
        "Address summary: all five address inputs are owner-continuity-closed nets.",
        "The former `BA11..BA15` mapping came from the original FDC scaffold's",
        "same-as-D8 analogy, not from `.009` scan, photo, or owner continuity evidence.",
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
            "| Pin | Role | Net | Captured activity | Source |",
            "| ---: | --- | --- | --- | --- |",
        ]
    )
    lines.extend(output_rows)
    lines.extend(
        [
            "",
            "## KiCad DSN Cross-check",
            "",
            "This table records the held freerouting DSN. It intentionally predates the",
            "2026-07-19 corrections; mismatches are migration evidence, not accepted",
            "connectivity. Board JSON and the regenerated KiCad schematic are authoritative.",
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
            "This table records the authoritative source PCB used by the promoted route.",
            "Its D94 pad nets are checked directly against the board model; the routed",
            "candidate identity gate separately proves the promoted board has the same pads.",
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
            f"| Every D94 address input is explicitly accounted | {'PASS' if address_accounted else 'FAIL'} | board JSON nets |",
            f"| Every D94 address input has reviewed two-sided photo coordinates | {'PASS' if all_address_inputs_registered else 'FAIL'} | local-package-fit measurement rows for pins {', '.join(sorted(address_observations, key=int)) or '-'} |",
            f"| D94 address input sources are traced | {'PASS' if address_traced else 'FAIL'} | direct owner continuity/source nets for pins 10-14 |",
            f"| Retired D94 BA11..BA15 mapping is absent from the source model | {'PASS' if retired_ba_mapping_absent else 'FAIL'} | board JSON BA nets |",
            f"| Held freerouting DSN matches the current D94 mapping | {'PASS' if dsn_matches_source_model else 'HELD'} | `kicad/juku.dsn` is a routed engineering snapshot; authoritative connectivity is board JSON/schematic |",
            f"| Source PCB agrees with current board-model D94 output nets | {'PASS' if pcb_ok and pcb_outputs_match else 'FAIL'} | `kicad/juku.kicad_pcb`; promoted route has exact source-pad identity |",
            f"| `V3_RC` is present but not D94 enable/output evidence | {'PASS' if v3_rc_not_d94_evidence else 'FAIL'} | board nodes {format_nodes(v3_rc_nodes)}; DSN/PCB D94 signal pins are not on `V3_RC` |",
            f"| Enable pin D94.15 is traced | {'PASS' if enable_ok else 'FAIL'} | board JSON nets |",
            f"| Enable pin15 is isolated from output pin2 | {'PASS' if enable_output_isolated else 'FAIL'} | direct owner continuity; distinct board nets |",
            f"| Any D94 output net is traced | {'PASS' if output_nets else 'FAIL'} | {', '.join(f'`{n}`' for n in output_nets) if output_nets else 'no D94 output nets in board JSON'} |",
            f"| Every D94 output pad has an explicit net/boundary | {'PASS' if len(output_nets) == len(output_pins) else 'FAIL'} | {len(output_nets)}/{len(output_pins)} output pins netted |",
            f"| D94 D5-D7 are owner/drawing-closed NC despite local copper stubs | {'PASS' if d5_d7_owner_closed_nc else 'FAIL'} | owner continuity 2026-07-21 plus component-side observations for pins {', '.join(sorted(output_departures, key=int)) or '-'} |",
            f"| Captured table asserts only D0-D3; D4-D7 stay released | {'PASS' if output_activity_ok else 'FAIL'} | exhaustive 32-row physical table classification |",
            f"| Minimized active-low equations reproduce all 256 captured bits | {'PASS' if minimized_logic_ok else 'FAIL'} | exhaustive address/output comparison against the physical image |",
            f"| Validated `.092` physical image exists and matches SHA256 | {'PASS' if physical_table_ok else 'FAIL'} | `{PHYSICAL_D94.relative_to(ROOT)}` / `{PHYSICAL_D94_SHA256}` |",
            f"| Official .009 BOM/photo notes identify D94 as `.092` | {'PASS' if official_bom_lead else 'FAIL'} | `ref/photos/juku-pcb-2/BODGE-TRIAGE.md` |",
            f"| Reused D94 refdes/tape-cluster history is guarded | {'PASS' if reused_refdes_guard else 'FAIL'} | `ref/photos/juku-pcb-2/BODGE-TRIAGE.md` |",
            f"| `.113/.117` scans are guarded as not-D94 | {'PASS' if scanned_not_d94 else 'FAIL'} | `docs/re3-firmware-inspection.md` |",
            f"| Vendored programming disks have a guarded PROM-name/marker/exact-table audit | {'PASS' if programming_media_audited else 'FAIL'} | `docs/vendored-disk-catalog.md` |",
            f"| HDL adopts physical open-collector table | {'PASS' if hdl_physical_table else 'FAIL'} | `hdl/devices.v::re3_prom_092` |",
            f"| HDL adopts measured D94 A0-A4 mapping | {'PASS' if hdl_inputs_measured else 'FAIL'} | `hdl/juku_top.v`; BA0, BA1, IORD, D105.3 qualified /WR, D101.7 |",
            f"| `juku_top` connects the three accepted local FDC controls | {'PASS' if hdl_connected else 'FAIL'} | `hdl/juku_top.v` |",
            f"| Runnable FDC consumes and cycle-checks physical D94 strobes | {'PASS' if hdl_runnable_physical else 'FAIL'} | simulation-only upstream fits remain explicit in `hdl/juku_top.v`; `hdl/sim/juku_top_periph_bus_tb.v` |",
            f"| Video slot audit does not rely on D94 | {'PASS' if video_audit_independent else 'FAIL'} | `docs/video-slot-timing-audit.md` |",
            "",
            "## Textual / Photo Survey Leads",
            "",
            "- The official .009 BOM trail identifies the FDC-era D94 as the second",
            "  К155РЕ3, programmed as `ДГШ5.106.092`.",
            "- Earlier D94 references in the sheet-3/tape-cluster survey are known",
            "  refdes reuse history, not evidence for the FDC-era timing PROM.",
            "- The guarded firmware inspection establishes that `.113/.117` belong",
            "  to the `.106.103`-family owner-scan evidence and are not a burnable",
            "  D94 `.092` substitute. The repeated physical `.092` image is authoritative.",
            "- The guarded `JUKPROG1`/`JUKPROG2`/`JUKPROGX` audit finds no active",
            "  candidate filename, recoverable deleted filename, or strong raw ASCII",
            "  `.037`/`.038`/`.039`/`.092`/RT4/RE3 marker. It also finds no exact",
            "  validated raw/asserted table in full images or reconstructed active files",
            "  under byte, reversed-address, ASCII/Intel-hex, or packed-nibble encodings.",
            "  Proprietary, permuted, compressed, or otherwise transformed data remains",
            "  possible, so this is negative search evidence rather than proof of absence.",
            "- A 2026-07-13 indexed-web search for exact `ДГШ5.106.092`,",
            "  `ДГШ5.106.092 Juku`, `Juku К155РЕ3 092 dump`, and",
            "  `Juku ES-101 floppy PROM D94` returned no programming table, binary,",
            "  scan, repository, or collector listing for this artifact. Generic Juku",
            "  history and generic К155РЕ3 references do not constrain its contents.",
            "- Direct owner continuity supersedes the mirrored-pin local interpretation:",
            "  enable pin15 reaches D93.3 CS; D1/pin2 reaches D99.9 and R89;",
            "  D2/pin3 reaches D93.4 /RE and R88; D3/pin4 reaches D93.2 /WE and R87.",
            "  Address inputs A0/A1/A2/A3/A4 reach BA0, BA1, IORD,",
            "  D105.3 qualified /WR, and D101.7 respectively. R8 is the 2 kohm",
            "  pull-up-only D94.1 branch; D0's hidden load remains open, while",
            "  owner continuity and exact-revision drawing review close D5-D7 as NC. Physical",
            "  captures now provide the PROM contents.",
            "- Git history proves the former A0-A4=`BA11..BA15` assignment entered in",
            "  commit `ed69b9d` as an FDC scaffold explicitly described as the same",
            "  convention as D8. No `.009` electrical source was cited. Direct owner",
            "  continuity now replaces all five scaffold inputs with measured nets.",
            "- Validated local package fits now preserve exact original-image coordinates",
            "  for D94.10-.14 on both sides. Component copper is socket-obscured and",
            "  the solder crop has no uniquely traceable remote endpoints, so these are",
            "  reviewed measurement records rather than promoted electrical nets.",
            "- Registered component-side local fits show copper departing D3-D7",
            "  (pins 4-7 and 9). Direct continuity closes D3/pin4 to D93.2; the",
            "  full-resolution exposed-socket recheck separates D4/pin5 from D93.1.",
            "  D93.1 owns the visible open stub; D4/pin5 is a PCB no-connect.",
            "  D5/pin6 reaches a proved plated local handoff",
            "  at (2266,1828) px, but independent D93/D94 cross-side projections",
            "  disagree by 54.2 px. Owner continuity and the exact `.009 E3` drawing",
            "  now close D5-D7 as electrically NC despite those local stubs. D0/pin1 is",
            "  destination-unresolved. The captured program keeps D4-D7 released",
            "  at every row; D0 and the now-closed D3 are behaviorally active.",
            "- The nearby `V3_RC` RC node is traced as `R17.1`, `C99.1`, and `D9.6`",
            "  in board JSON/DSN, but D94 pin 15 and D3-D7 are not tied to it in",
            "  board JSON, DSN, or PCB evidence. It cannot substitute for the missing",
            "  D94 input/enable/output continuity.",
            "- A 2026-07-11 high-resolution recheck projected D93.2 and D93.4 from",
            "  the validated reflected D94 solder fit into the same source image.",
            "  Neither pad shows an obvious solder-side fanout. Owner continuity now",
            "  closes D94.15->D93.3 and corrects D94.2 to D99.9/R89, demonstrating why the",
            "  earlier local mirrored-pin interpretation was insufficient.",
            "",
            "## Input-mapping correction and control constraint",
            "",
            "The three proved output destinations and physical table reject the old",
            "scaffold mapping as a closed physical claim:",
            "",
            "- D94.D2 and D94.D3 terminate at the separate active-low D93 `/RE` and",
            "  `/WE` inputs. An FDC register must support both reads and writes at the",
            "  same port address.",
            "- If A0-A4 were only `BA11..BA15`, the same PROM row would drive both cycle",
            "  directions and could not independently select `/RE` versus `/WE`.",
            "- That mapping was never measured; it was copied by analogy from D8.",
            "  Owner continuity now supplies the actual five input sources.",
            "",
            "This does not refute the accepted local D94-to-D93 copper. It removes a",
            "false source claim. Remaining decode work is the upstream enable source,",
            "D0 hidden-load status, and guarded D29.4/IORD recheck.",
            "",
            "## Minimized asserted-output logic",
            "",
            "Define `S(Dn)=1` when the open-collector output is programmed active",
            "(captured raw bit `0`), and define the shared qualifier",
            "`Q = A4 | !A1 | !A0`. Exhaustive comparison against all 32 addresses",
            "gives:",
            "",
            "| Output | Exact asserted equation | Physical destination |",
            "| --- | --- | --- |",
            "| `S(D0)` | `!A4 & A1 & A0` | R8 2 kΩ pull-up-only boundary |",
            "| `S(D1)` | `A3 xor A2` | D99.9 / R89 pull-up |",
            "| `S(D2)` | `A3 & !A2 & Q` | D93 `/RE` |",
            "| `S(D3)` | `!A3 & A2 & Q` | D93 `/WE` |",
            "| `S(D4..D7)` | `0` | owner/drawing-closed NC outputs; always released |",
            "",
            "These equations sharpen, but do not replace, continuity evidence:",
            "",
            "- D2 `/RE` and D3 `/WE` are mutually exclusive and select opposite",
            "  one-hot states of A3/A2. This proves the PROM is a cycle-control",
            "  decoder rather than an address-only register decoder.",
            "- A2 is owner-measured to active-low `IORD`. Therefore, while `Q` is",
            "  true on a selected FDC register cycle, the equations require A3=1",
            "  for a read (`IORD`=0 -> `/RE` asserted) and A3=0 for a write",
            "  (`IORD`=1 -> `/WE` asserted). A3 must consequently be polarity-",
            "  equivalent to active-low `IOWR` during those cycles. This is an exact",
            "  firmware-derived prediction is now physically closed: D94.13 belongs",
            "  to D105.3 qualified peripheral `/WR`, while D5.27 is the distinct raw",
            "  `IOWR_N` input to D7.10. D104.7 is separate (~84 kΩ to D94.13).",
            "- At BA1:BA0=`11` with A4 low, `Q` becomes false, both D93 strobes",
            "  release, and D0 asserts independently of A3/A2. A live D0 branch",
            "  probe should therefore target exactly that row condition.",
            "  Conversely, A4 high restores the normal D93 read/write strobes at",
            "  register 3. Because A4 cancels out of `Q` at every other BA1:BA0",
            "  value, D101.Q0 is exactly a register-3 transfer-steering qualifier;",
            "  this does not identify the alternate D0 load or D101's broader role.",
            "- D4-D7 cannot change digital behavior for any captured address. Owner",
            "  continuity closes D5-D7 as NC; photographed local stubs remain layout evidence.",
            "- The equations constrain A3's selected-cycle function but do not prove",
            "  its electrical source; A4 semantics and D0's far endpoint likewise",
            "  remain electrical/source boundaries rather than inferred nets.",
            "",
            "## Address Space",
            "",
            "D94 is a 32 x 8 PROM. The table below uses reader input indices A4..A0;",
            "the board mapping is now A0=BA0, A1=BA1, A2=IORD, A3=D105.3 qualified /WR,",
            "and A4=D101.7. D5-D7 are owner/drawing-closed NC.",
            "",
            "| Row | A4 | A3 | A2 | A1 | A0 | D7..D0 |",
            "| ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    lines.extend(address_space_rows(physical_table))
    lines.extend(
        [
            "",
            "## Reconstruction Boundary",
            "",
            "- Known: D94 is present in the .009 FDC quadrant and all five address",
            "  inputs have direct owner-continuity mappings.",
            "- Known control destinations: D94 enable pin15 reaches D93.3 CS; D1/pin2",
            "  reaches D99.9/R89; D2/pin3 reaches D93.4/R88 RE; and D3/pin4",
            "  reaches D93.2/R87 WE. D4/pin5 is a PCB no-connect, while",
            "  D93.1 owns a separate open stub.",
            "  D5-D7/pins6,7,9 are also NC by exact-revision drawing review and",
            "  owner continuity on 2026-07-21.",
            "  D0/pin1 has only R8 2 kΩ to +5 V in the measured scope.",
            "- Known content: three matching reads including a power-cycled read yield",
            f"  raw SHA256 `{PHYSICAL_D94_SHA256}`.",
            "- Known pull-up values: alternate-angle owner photography reads `6К2` on",
            "  R87 and R88; R89 is partly socket-obscured but visually identical. The",
            "  equipment list's separately designated `ДГШ5.087.009` group contains",
            "  exactly three МЛТ-0,125 6.2 kΩ ±5% parts as corroboration. The readable",
            "  target-board pair and identical third body close R87/R88/R89 as 6.2 kΩ.",
            "- Unknown: the shared CS/enable upstream source and D0 hidden-branch status.",
            "- Firmware-derived prediction: D94 A3 must equal active-low `IOWR` on",
            "  selected FDC cycles. Confirm by continuity to D5.27 or simultaneous",
            "  operating-level capture; do not merge the nets from this constraint.",
            "- Runnable-model disposition: the behavioral FDC now consumes the",
            "  physical table's `/RE` and `/WE`. Its decoded enable, A3=`IOWR`, and",
            "  pulled-high A4 sources are simulation-only fits; Yosys/LVS keeps the",
            "  measured physical nets separate and unresolved.",
            "  The fast bus guard also forces A4 low on register 3 and proves D0",
            "  asserts while both D93 strobes release, without assigning D0 a load.",
            "- D5-D7 are electrically NC. Registered component-side photographs show",
            "  only local copper departures, which continuity does not extend to a load.",
            "- D4-D7 are program-inert: raw bits 4-7 remain one",
            "  (open-collector released) at all 32 captured rows. D3 is the only",
            "  closed active output; D0 is behaviorally active and destination-unknown.",
            "- The traced `V3_RC` RC network is a negative cross-check here, not a",
            "  replacement source for D94: its current nodes are `R17.1`, `C99.1`,",
            "  and `D9.6`, with no D94 signal endpoint in JSON, DSN, or PCB.",
            "- D94 is now classified as an FDC control/decode PROM because its proved",
            "  functional outputs and D4's inert/back-bias route terminate at D93.",
            "  It is not evidence for the separate",
            "  shared-DRAM video-slot schedule.",
            "- The 256-bit content ambiguity is closed. The remaining ambiguity is",
            "  electrical: enable timing and the far ends/branches of output nets.",
            "- The physical image is burnable, but that alone cannot release the FDC",
            "  circuit or the replica PCB while those continuity boundaries remain.",
            "- Do not reuse `.113` or `.117` as D94: those scans are guarded as",
            "  `.106.103`-family evidence, not the processor-module `.092` content.",
        ]
    )

    REPORT.write_text("\n".join(lines) + "\n")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    print(f"Status: {status}")
    gates = {
        "board_identity": board_identity_ok,
        "address_accounted": address_accounted,
        "address_inputs_registered": all_address_inputs_registered,
        "address_sources_traced": address_traced,
        "retired_ba_mapping_absent": retired_ba_mapping_absent,
        "official_bom": official_bom_lead,
        "reused_refdes_guard": reused_refdes_guard,
        "v3_rc_excluded": v3_rc_not_d94_evidence,
        "physical_table": physical_table_ok,
        "hdl_table": hdl_physical_table,
        "hdl_controls": hdl_connected,
        "hdl_runnable_physical": hdl_runnable_physical,
        "hdl_inputs": hdl_inputs_measured,
        "re3_lineage": scanned_not_d94,
        "programming_media_audit": programming_media_audited,
        "video_audit_independent": video_audit_independent,
        "enable_accounted": enable_accounted,
        "enable_traced": enable_ok,
        "enable_output_isolated": enable_output_isolated,
        "remaining_output_departures": d5_d7_owner_closed_nc,
        "output_activity": output_activity_ok,
        "minimized_logic": minimized_logic_ok,
    }
    failed = [name for name, ok in gates.items() if not ok]
    if failed:
        print("Failed gates: " + ", ".join(failed))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
