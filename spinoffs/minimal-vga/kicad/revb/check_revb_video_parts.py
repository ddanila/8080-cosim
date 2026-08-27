#!/usr/bin/env python3
"""R5.V4 exact Video parts, land-pattern, socket and bus-connector gate."""
from __future__ import annotations

import copy
import json
import math
import os
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARTS_FILE = HERE / "video-parts.json"
VIDEO_FILE = HERE / "video.board.json"

TYPE_PACKAGE = {
    "OSC_25M175": (14, 7.62),
    "ST_HC393": (14, 7.62), "HCT_08": (14, 7.62), "ACT_08": (14, 7.62),
    "ACT_157": (16, 7.62), "ACT_161": (16, 7.62), "TTL_283": (16, 7.62),
    "ALS_166": (16, 7.62),
    "ACT_273": (20, 7.62), "HCT_245": (20, 7.62),
    "GAL22V10_HDEC": (24, 7.62), "GAL22V10_VDEC": (24, 7.62),
    "GAL22V10_CTRL": (24, 7.62), "SRAM_FB": (32, 15.24),
}
SOCKET_KEY = {14: "dip14_socket", 16: "dip16_socket", 20: "dip20_socket",
              24: "dip24_socket", 32: "dip32_socket"}
EXPECTED_MPN = {
    "vga": "200-015-213L537", "oscillator": "ECS-100A-251.7",
    "framebuffer_sram": "AS6C1008-55PCN", "video_gals": "ATF22V10C-15PU",
    "card_bus_base": "TSW-139-08-S-S-RA", "card_bus_ext": "TSW-110-08-S-S-RA",
    "backplane_bus_base": "SSW-139-01-S-S", "backplane_bus_ext": "SSW-110-01-S-S",
    "dip14_socket": "1-2199298-3", "dip16_socket": "1-2199298-4",
    "dip20_socket": "1-2199298-6", "dip24_socket": "1-2199298-8",
    "dip32_socket": "1-2199300-2", "bulk_capacitor": "ECA-1HM470",
}


def close(a: float, b: float, tol: float = 0.006) -> bool:
    return math.isclose(a, b, abs_tol=tol)


def pad_records(text: str) -> list[tuple[str, float, float, float]]:
    records = []
    pattern = re.compile(
        r'\(pad\s+"([^"]+)"\s+thru_hole\s+\S+\s+\(at\s+([-\d.]+)\s+([-\d.]+)\)'
        r'.{0,180}?\(drill\s+([-\d.]+)\)', re.S)
    for number, x, y, drill in pattern.findall(text):
        records.append((number, float(x), float(y), float(drill)))
    return records


def library_footprint_path(name: str) -> Path:
    lib, footprint = name.split(":")
    root = HERE if lib == "VJUGA" else Path(os.environ.get("KICAD_FOOTPRINTS", ""))
    return root / f"{lib}.pretty" / f"{footprint}.kicad_mod"


def verify(contract: dict, board: dict) -> list[str]:
    errors: list[str] = []
    parts = contract.get("parts", {})
    required = {"vga", "oscillator", "framebuffer_sram", "video_gals",
                "card_bus_base", "card_bus_ext", "backplane_bus_base",
                "backplane_bus_ext", "bulk_capacitor", *SOCKET_KEY.values()}
    if set(parts) != required:
        errors.append(f"parts keys differ: {sorted(set(parts) ^ required)}")
        return errors
    for key, part in parts.items():
        if part.get("mpn") != EXPECTED_MPN[key] or not part.get("manufacturer"):
            errors.append(f"{key}: exact MPN differs from {EXPECTED_MPN[key]}")
        for field in ("datasheet", "order_source", "availability_snapshot"):
            if not part.get(field):
                errors.append(f"{key}: {field} missing")

    by_ref = {part["ref"]: part for part in board["chips"]}
    expected_types = {
        "J_VGA": "DSUB15HD", "U1": "OSC_25M175", "U21": "SRAM_FB",
        "U5": "GAL22V10_HDEC", "U6": "GAL22V10_VDEC", "U7": "GAL22V10_CTRL",
        "C_BULK": "C_ELEC_47U",
    }
    for ref, typ in expected_types.items():
        if by_ref.get(ref, {}).get("type") != typ:
            errors.append(f"{ref}: expected {typ}")
    if by_ref.get("J_VGA", {}).get("pins", {}).get("SH") != "GND":
        errors.append("J_VGA shell/board locks are not bonded to GND")

    # Derive sockets from actual U1..U23 packages. U1's four-lead full can uses the
    # same 14-position socket grid; all 23 active packages therefore remain replaceable.
    socket_counts = Counter()
    for ref, part in by_ref.items():
        if not ref.startswith("U"):
            continue
        package = TYPE_PACKAGE.get(part["type"])
        if package is None:
            errors.append(f"{ref}: no socket/package contract for {part['type']}")
            continue
        pins, width = package
        socket_counts[pins] += 1
        if ref not in {"U1", "U5", "U6", "U7", "U21"} and not close(width, 7.62):
            errors.append(f"{ref}: unexpected non-300mil logic package")
    for pins, key in SOCKET_KEY.items():
        if parts[key].get("quantity") != socket_counts[pins]:
            errors.append(f"{key}: quantity {parts[key].get('quantity')} != derived {socket_counts[pins]}")
        package = parts[key].get("package", {})
        if package.get("pins") != pins or not close(package.get("row_spacing_mm", 0),
                                                    15.24 if pins == 32 else 7.62):
            errors.append(f"{key}: socket geometry differs")
    if sum(socket_counts.values()) != 23:
        errors.append(f"socket coverage is {sum(socket_counts.values())}/23")
    if parts["framebuffer_sram"].get("package") != {
            "pins": 32, "row_spacing_mm": 15.24, "pitch_mm": 2.54}:
        errors.append("framebuffer SRAM package geometry differs")
    if parts["video_gals"].get("package") != {
            "pins": 24, "row_spacing_mm": 7.62, "pitch_mm": 2.54}:
        errors.append("Video GAL package geometry differs")
    expected_bus_packages = {
        "card_bus_base": {"pins": 39, "pitch_mm": 2.54, "post_mm": 5.84,
                          "tail_mm": 2.29, "square_post_mm": 0.635, "min_drill_mm": 1.00},
        "card_bus_ext": {"pins": 10, "pitch_mm": 2.54, "post_mm": 5.84,
                         "tail_mm": 2.29, "square_post_mm": 0.635, "min_drill_mm": 1.00},
        "backplane_bus_base": {"pins": 39, "pitch_mm": 2.54, "tail_mm": 2.64,
                               "min_drill_mm": 1.00, "height_mm": 8.51},
        "backplane_bus_ext": {"pins": 10, "pitch_mm": 2.54, "tail_mm": 2.64,
                              "min_drill_mm": 1.00, "height_mm": 8.51},
    }
    for key, expected in expected_bus_packages.items():
        if parts[key].get("package") != expected:
            errors.append(f"{key}: lead/body geometry differs")

    # Exact NorComp recommended PCB layout: unusual 7+8 solder-tail rows, not a
    # generic 5+5+5 high-density D-sub land pattern.
    vga = parts["vga"]
    if vga.get("footprint") != "VJUGA:NorComp_200-015-213L537":
        errors.append("VGA footprint is not exact NorComp land pattern")
    expected_vga_geometry = {
        "signal_holes": 15, "signal_drill": 0.70, "signal_row_separation": 1.50,
        "signal_x_step": 0.762, "signal_span_x": 10.668, "board_lock_holes": 2,
        "board_lock_drill": 2.10, "board_lock_span_x": 16.00,
        "pcb_edge_from_top_signal_row": 2.50, "mating_face_from_pcb_edge": 5.80,
        "shell_width": 30.81, "shell_height": 12.55, "courtyard_clearance": 0.25,
    }
    if vga.get("geometry_mm") != expected_vga_geometry:
        errors.append("VGA datasheet geometry contract differs")
    fp_text = (HERE / "VJUGA.pretty" / "NorComp_200-015-213L537.kicad_mod").read_text()
    pads = pad_records(fp_text)
    signal = {n: (x, y, d) for n, x, y, d in pads if n.isdigit()}
    shell = [(x, y, d) for n, x, y, d in pads if n == "SH"]
    expected_xy = {
        "1": (0, 0), "2": (-2.286, 1.5), "3": (-4.572, 0),
        "4": (-6.858, 1.5), "5": (-9.144, 0), "6": (0.762, 1.5),
        "7": (-1.524, 0), "8": (-3.810, 1.5), "9": (-6.096, 0),
        "10": (-8.382, 1.5), "11": (-0.762, 1.5), "12": (-3.048, 0),
        "13": (-5.334, 1.5), "14": (-7.620, 0), "15": (-9.906, 1.5),
    }
    if set(signal) != set(expected_xy):
        errors.append("VGA signal pad set is not 1..15")
    for pin, (ex, ey) in expected_xy.items():
        got = signal.get(pin)
        if not got or not close(got[0], ex) or not close(got[1], ey) or not close(got[2], 0.70):
            errors.append(f"VGA pad {pin}: expected ({ex},{ey}) drill 0.70, got {got}")
    if len(shell) != 2 or any(not close(d, 2.10) for _, _, d in shell):
        errors.append("VGA board locks are not 2 x 2.10mm")
    elif not close(abs(shell[1][0] - shell[0][0]), 16.00):
        errors.append("VGA board-lock span is not 16.00mm")
    geometry_tokens = (
        '(start -20.227 -2.25) (end 11.083 8.55)',
        '(start -19.977 2.50) (end 10.833 2.50)',
        '(start -19.977 8.30) (end 10.833 8.30)',
    )
    if any(token not in fp_text for token in geometry_tokens):
        errors.append("VGA courtyard, PCB edge or mating-face geometry differs")

    # Resolved footprint maps must use the exact mechanical orientations on all cards.
    for card in ("mem", "io", "cpu", "video"):
        path = HERE / f"footprints.{card}.json"
        if not path.exists():
            errors.append(f"{path.name}: missing")
            continue
        fmap = json.loads(path.read_text())
        expected = [parts["card_bus_base"]["footprint"], parts["card_bus_ext"]["footprint"]]
        if fmap.get("REVB_BUS_39_10") != expected:
            errors.append(f"{card}: card bus footprints are not exact right-angle headers")
    bp_path = HERE / "footprints.backplane.json"
    if bp_path.exists():
        fmap = json.loads(bp_path.read_text())
        expected = [parts["backplane_bus_base"]["footprint"],
                    parts["backplane_bus_ext"]["footprint"]]
        if fmap.get("REVB_BUS_39_10") != expected:
            errors.append("backplane bus footprints are not exact vertical sockets")
    else:
        errors.append("footprints.backplane.json: missing")

    for key in ("card_bus_base", "card_bus_ext", "backplane_bus_base", "backplane_bus_ext"):
        spec = parts[key]
        fp_path = library_footprint_path(spec["footprint"])
        if not fp_path.is_file():
            errors.append(f"{key}: footprint file missing")
            continue
        records = [(n, x, y, d) for n, x, y, d in pad_records(fp_path.read_text()) if n.isdigit()]
        pins = spec["package"]["pins"]
        if len(records) != pins or min((r[3] for r in records), default=0) < spec["package"]["min_drill_mm"]:
            errors.append(f"{key}: pad count/drill differs from selected connector")
        centres = sorted((x, y) for _, x, y, _ in records)
        if centres:
            span = max(max(x for x, _ in centres) - min(x for x, _ in centres),
                       max(y for _, y in centres) - min(y for _, y in centres))
            if not close(span, (pins - 1) * spec["package"]["pitch_mm"]):
                errors.append(f"{key}: pin-row pitch/span differs")
    video_map = json.loads((HERE / "footprints.video.json").read_text()) if (
        HERE / "footprints.video.json").exists() else {}
    for typ, key in (("DSUB15HD", "vga"), ("OSC_25M175", "oscillator"),
                     ("SRAM_FB", "framebuffer_sram")):
        if video_map.get(typ) != parts[key]["footprint"]:
            errors.append(f"video footprint map: {typ} differs from {parts[key]['mpn']}")
    for typ in ("GAL22V10_HDEC", "GAL22V10_VDEC", "GAL22V10_CTRL"):
        if video_map.get(typ) != parts["video_gals"]["footprint"]:
            errors.append(f"video footprint map: {typ} differs")

    bulk = parts["bulk_capacitor"]
    if bulk.get("footprint") != "Capacitor_THT:CP_Radial_D6.3mm_P2.50mm" or not bulk.get("polarized"):
        errors.append("bulk capacitor footprint/polarity differs")
    if bulk.get("package") != {"diameter_mm": 6.30, "height_mm": 12.20,
                               "lead_pitch_mm": 2.50, "lead_diameter_mm": 0.50,
                               "min_drill_mm": 0.60}:
        errors.append("bulk capacitor body/lead geometry differs")
    osc = parts["oscillator"]
    if (osc.get("frequency_mhz"), osc.get("supply_v"), osc.get("max_current_ma"),
            osc.get("body_mm"), osc.get("pins")) != (
            25.175, [4.75, 5.25], 70, [20.86, 13.20, 5.08],
            {"1": "NC", "7": "GND_CASE", "8": "OUTPUT", "14": "VCC5"}):
        errors.append("oscillator electrical/body/pin contract differs")

    # Full-can oscillator grid is 15.24 x 7.62 mm with exactly pins 1/7/8/14.
    fp_root = Path(os.environ.get("KICAD_FOOTPRINTS", ""))
    osc_path = fp_root / "Oscillator.pretty" / "Oscillator_DIP-14.kicad_mod"
    if osc_path.is_file():
        osc_pads = {n: (x, y, d) for n, x, y, d in pad_records(osc_path.read_text())}
        expected_osc = {"1": (0.0, 0.0), "7": (15.24, 0.0),
                        "8": (15.24, -7.62), "14": (0.0, -7.62)}
        if set(osc_pads) != set(expected_osc):
            errors.append("oscillator footprint pad set is not 1/7/8/14")
        for pin, (x, y) in expected_osc.items():
            got = osc_pads.get(pin)
            if not got or not close(got[0], x) or not close(got[1], y) or got[2] < 0.80:
                errors.append(f"oscillator pad {pin}: wrong DIP-14 grid/drill {got}")
    else:
        errors.append("Oscillator_DIP-14 footprint cannot be inspected")

    # Exact oscillator choice must flow into the conservative power model.
    power = json.loads((HERE / "video-power-audit.json").read_text())
    if power["current_budget_ma"]["video"]["oscillator"] != parts["oscillator"]["max_current_ma"]:
        errors.append("oscillator datasheet maximum is not reflected in power budget")
    return errors


def main() -> int:
    contract = json.loads(PARTS_FILE.read_text())
    board = json.loads(VIDEO_FILE.read_text())
    errors = verify(contract, board)
    if "--self-test" in sys.argv:
        wrong_socket = copy.deepcopy(contract)
        wrong_socket["parts"]["dip16_socket"]["quantity"] -= 1
        if not verify(wrong_socket, board):
            errors.append("socket-count mutation escaped")
        wrong_mpn = copy.deepcopy(contract)
        wrong_mpn["parts"]["vga"]["footprint"] = (
            "Connector_Dsub:DSUB-15-HD_Socket_Horizontal_P2.29x1.90mm_"
            "EdgePinOffset3.03mm_Housed_MountingHolesOffset4.94mm")
        if not verify(wrong_mpn, board):
            errors.append("generic-HD15 mutation escaped")
    if errors:
        for error in errors:
            print(f"REVB-VIDEO-PARTS: FAIL {error}", file=sys.stderr)
        return 1
    suffix = " + wrong-socket/HD15 controls" if "--self-test" in sys.argv else ""
    print("REVB-VIDEO-PARTS: PASS 23/23 sockets, exact VGA/oscillator/SRAM/GALs, "
          "card/backplane bus orientations and tall/polarized parts" + suffix)
    return 0


if __name__ == "__main__":
    sys.exit(main())
