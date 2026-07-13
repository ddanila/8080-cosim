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

    dsn_pin_roles = dict(pin_roles)
    dsn_pin_roles.update({"8": "GND", "16": "VCC"})
    all_report_pins = sorted(dsn_pin_roles, key=lambda pin: int(pin))
    dsn_rows = []
    retired_dsn_inputs = {"10": "BA11", "11": "BA12", "12": "BA13", "13": "BA14", "14": "BA15"}
    dsn_expected = {"8": "GND", "16": "P5V"}
    dsn_ok = True
    for pin in all_report_pins:
        role = dsn_pin_roles[pin]
        name = dsn_nets.get(pin)
        expected = dsn_expected.get(pin)
        if name is None:
            dsn_rows.append(f"| {pin} | {role} | - | missing in DSN |")
        else:
            if pin in retired_dsn_inputs and name == retired_dsn_inputs[pin]:
                result = "STALE scaffold mapping"
            else:
                result = "PASS" if expected is None or name == expected else f"expected `{expected}`"
            dsn_rows.append(f"| {pin} | {role} | `{name}` | {result} |")
            if expected is not None and name != expected:
                dsn_ok = False
    dsn_retains_retired_inputs = all(
        dsn_nets.get(pin) == name for pin, name in retired_dsn_inputs.items()
    )

    dsn_output_nets = [
        dsn_nets[pin]
        for pin, role in output_pins
        if pin in dsn_nets
    ]
    pcb_rows = []
    pcb_ok = bool(pcb_nets)
    pcb_expected = {
        **dsn_expected,
        "10": "D94_A0_BOUNDARY",
        "11": "D94_A1_BOUNDARY",
        "12": "D94_A2_BOUNDARY",
        "13": "D94_A3_BOUNDARY",
        "14": "D94_A4_BOUNDARY",
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
    hdl_inputs_boundary = marker(
        "hdl/juku_top.v",
        "wire [4:0] d94_a_boundary",
        ".a(d94_a_boundary)",
        "no .009 source proves that mapping",
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
        "media/disks/JUKPROG1.CPM | none | none | none",
        "media/disks/JUKPROG2.CPM | none | none | none",
        "media/disks/JUKPROGX.CPM | none | none | none",
        "cannot rule out an unidentified binary table with no embedded identifier",
    )
    video_audit_independent = marker(
        "docs/video-slot-timing-audit.md",
        "Status: **VIDEO SLOT TIMING AUDITED / PHYSICAL SLOT SCHEDULE PENDING**",
        "D94 is not used as video-timing evidence",
    )
    output_departures = remaining_output_departures()
    all_remaining_outputs_depart = set(output_departures) == {"4", "5", "6", "7", "9"}
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
        "Address summary: all five address inputs are explicit continuity boundaries.",
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
            "The held routed DSN predates this provenance correction and still carries",
            "the retired BA11..BA15 scaffold mapping. It is retained as stale-package",
            "evidence, not independent proof of the D94 input sources.",
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
            "The authoritative source PCB includes accepted photo-traced outputs; the",
            "older routed DSN remains a held engineering snapshot until cluster reroute.",
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
            f"| D94 address input sources are traced | {'PASS' if address_traced else 'FAIL'} | pins 10-14 remain continuity boundaries |",
            f"| Retired D94 BA11..BA15 mapping is absent from the source model | {'PASS' if retired_ba_mapping_absent else 'FAIL'} | board JSON BA nets |",
            f"| Held routed DSN is identified with the retired input mapping | {'PASS' if dsn_ok and dsn_retains_retired_inputs and not dsn_output_nets else 'FAIL'} | `kicad/juku.dsn` D94 pins |",
            f"| PCB agrees with current board-model D94 output nets | {'PASS' if pcb_ok and pcb_outputs_match else 'FAIL'} | `kicad/juku.kicad_pcb` D94 footprint pads |",
            f"| `V3_RC` is present but not D94 enable/output evidence | {'PASS' if v3_rc_not_d94_evidence else 'FAIL'} | board nodes {format_nodes(v3_rc_nodes)}; DSN/PCB D94 signal pins are not on `V3_RC` |",
            f"| Enable pin D94.15 is traced | {'PASS' if enable_ok else 'FAIL'} | board JSON nets |",
            f"| Enable pad/fanout is represented as an unresolved boundary | {'PASS' if enable_accounted and not enable_ok else 'FAIL'} | `D94_EN_BOUNDARY` |",
            f"| Any D94 output net is traced | {'PASS' if output_nets else 'FAIL'} | {', '.join(f'`{n}`' for n in output_nets) if output_nets else 'no D94 output nets in board JSON'} |",
            f"| Every D94 output pad has an explicit net/boundary | {'PASS' if len(output_nets) == len(output_pins) else 'FAIL'} | {len(output_nets)}/{len(output_pins)} output pins netted |",
            f"| Every unresolved D94 output has a photographed copper departure | {'PASS' if all_remaining_outputs_depart else 'FAIL'} | component-side local-fit observations for pins {', '.join(sorted(output_departures, key=int)) or '-'} |",
            f"| Captured table asserts only D0-D3; D4-D7 stay released | {'PASS' if output_activity_ok else 'FAIL'} | exhaustive 32-row physical table classification |",
            f"| Validated `.092` physical image exists and matches SHA256 | {'PASS' if physical_table_ok else 'FAIL'} | `{PHYSICAL_D94.relative_to(ROOT)}` / `{PHYSICAL_D94_SHA256}` |",
            f"| Official .009 BOM/photo notes identify D94 as `.092` | {'PASS' if official_bom_lead else 'FAIL'} | `ref/photos/juku-pcb-2/BODGE-TRIAGE.md` |",
            f"| Reused D94 refdes/tape-cluster history is guarded | {'PASS' if reused_refdes_guard else 'FAIL'} | `ref/photos/juku-pcb-2/BODGE-TRIAGE.md` |",
            f"| `.113/.117` scans are guarded as not-D94 | {'PASS' if scanned_not_d94 else 'FAIL'} | `docs/re3-firmware-inspection.md` |",
            f"| Vendored programming disks have a guarded PROM-name/marker audit | {'PASS' if programming_media_audited else 'FAIL'} | `docs/vendored-disk-catalog.md` |",
            f"| HDL adopts physical open-collector table | {'PASS' if hdl_physical_table else 'FAIL'} | `hdl/devices.v::re3_prom_092` |",
            f"| HDL keeps D94 A0-A4 off the retired BA mapping | {'PASS' if hdl_inputs_boundary else 'FAIL'} | `hdl/juku_top.v` boundary vector |",
            f"| `juku_top` connects the three accepted local FDC controls | {'PASS' if hdl_connected else 'FAIL'} | `hdl/juku_top.v` |",
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
            "  `.037`/`.038`/`.039`/`.092`/RT4/RE3 marker. An unidentified binary",
            "  table remains possible, so this is negative search evidence rather than",
            "  proof that the programming bytes are absent from every unlabelled blob.",
            "- A 2026-07-13 indexed-web search for exact `ДГШ5.106.092`,",
            "  `ДГШ5.106.092 Juku`, `Juku К155РЕ3 092 dump`, and",
            "  `Juku ES-101 floppy PROM D94` returned no programming table, binary,",
            "  scan, repository, or collector listing for this artifact. Generic Juku",
            "  history and generic К155РЕ3 references do not constrain its contents.",
            "- Local two-sided fits and continuous copper now establish D0-D2 as the",
            "  private `FDC_RE_N`, `FDC_CS_N`, and `FDC_WE_N` rails. Textual sources",
            "  still do not provide A0-A4, pin 15, or D3-D7 destinations; physical",
            "  captures now provide the PROM contents.",
            "- Git history proves the former A0-A4=`BA11..BA15` assignment entered in",
            "  commit `ed69b9d` as an FDC scaffold explicitly described as the same",
            "  convention as D8. No `.009` electrical source or owner measurement was",
            "  cited. The source PCB now represents pins 10-14 as measurement boundaries.",
            "- Validated local package fits now preserve exact original-image coordinates",
            "  for D94.10-.14 on both sides. Component copper is socket-obscured and",
            "  the solder crop has no uniquely traceable remote endpoints, so these are",
            "  reviewed measurement records rather than promoted electrical nets.",
            "- Registered component-side local fits show copper departing every remaining",
            "  output pad D3-D7 (pins 4-7 and 9), now represented by explicit boundary",
            "  nets. Their far destinations remain unknown, so none may be removed from",
            "  the PCB as NC. The captured program nevertheless keeps D4-D7 released at",
            "  every row; only D3 among those five can affect circuit behavior.",
            "- The nearby `V3_RC` RC node is traced as `R17.1`, `C99.1`, and `D9.6`",
            "  in board JSON/DSN, but D94 inputs A0-A4, pin 15, and D3-D7 are not tied to it in",
            "  board JSON, DSN, or PCB evidence. It cannot substitute for the missing",
            "  D94 input/enable/output continuity.",
            "- A 2026-07-11 high-resolution recheck projected D93.2 and D93.4 from",
            "  the validated reflected D94 solder fit into the same source image.",
            "  Neither pad shows an obvious solder-side fanout, while D94.15 still",
            "  cannot be followed to a unique endpoint across the adjacent tile.",
            "  This is useful negative photo evidence, not a substitute for continuity.",
            "",
            "## Input-mapping correction and control constraint",
            "",
            "The three proved output destinations and physical table reject the old",
            "scaffold mapping as a closed physical claim:",
            "",
            "- D94.D0 and D94.D2 terminate at the separate active-low D93 `/RE` and",
            "  `/WE` inputs. An FDC register must support both reads and writes at the",
            "  same port address.",
            "- If A0-A4 were only `BA11..BA15`, the same PROM row would drive both cycle",
            "  directions and could not independently select `/RE` versus `/WE`.",
            "- That mapping was never measured; it was copied by analogy from D8. The",
            "  contradiction therefore narrows the next work to the actual D94 input",
            "  sources, plus any wired/open-collector branches at D93.2/.4 and pin 15.",
            "",
            "This does not refute the accepted local D94-to-D93 copper. It removes a",
            "false source claim and makes the required measurement explicit: map pins",
            "10-15 and every branch from D93.2/.4 before assigning row semantics.",
            "",
            "## Address Space",
            "",
            "D94 is a 32 x 8 PROM. The table below uses reader input indices A4..A0;",
            "it intentionally makes no claim about their board signal sources. Unknown",
            "input wiring or D3-D7 destinations do not make captured bits unknown.",
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
            "- Known: D94 is present in the .009 FDC quadrant; all five address input",
            "  pads are modeled, but their remote sources are not yet known.",
            "- Known output destinations: D0-D2 drive the private D93 read/select/write",
            "  controls `FDC_RE_N`, `FDC_CS_N`, and `FDC_WE_N`.",
            "- Known content: three matching reads including a power-cycled read yield",
            f"  raw SHA256 `{PHYSICAL_D94_SHA256}`.",
            "- Unknown: D94 A0-A4/pins 10-14, pin 15's upstream source, and D3-D7 far",
            "  destinations remain unresolved behind explicit boundary nets.",
            "- D3-D7 are destination-unknown, not unused: registered component-side",
            "  photographs prove copper leaves all five output pads.",
            "- D4-D7 are physically wired but program-inert: raw bits 4-7 remain one",
            "  (open-collector released) at all 32 captured rows. D3 is the only",
            "  behaviorally active output whose far destination is still unknown.",
            "- The traced `V3_RC` RC network is a negative cross-check here, not a",
            "  replacement source for D94: its current nodes are `R17.1`, `C99.1`,",
            "  and `D9.6`, with no D94 signal endpoint in JSON, DSN, or PCB.",
            "- D94 is now classified as an FDC control/decode PROM because its only",
            "  proved outputs terminate at D93. It is not evidence for the separate",
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
    return 0 if (
        board_identity_ok
        and address_accounted
        and all_address_inputs_registered
        and not address_traced
        and retired_ba_mapping_absent
        and dsn_ok
        and dsn_retains_retired_inputs
        and pcb_ok
        and official_bom_lead
        and reused_refdes_guard
        and v3_rc_not_d94_evidence
        and physical_table_ok
        and hdl_physical_table
        and hdl_connected
        and hdl_inputs_boundary
        and pcb_outputs_match
        and scanned_not_d94
        and programming_media_audited
        and video_audit_independent
        and enable_accounted
        and not enable_ok
        and all_remaining_outputs_depart
        and output_activity_ok
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
