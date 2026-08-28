#!/usr/bin/env python3
"""R5.J1 JLCPCB geometry, layer and upload-archive profile gate."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
import zipfile
from collections import Counter
from pathlib import Path, PurePosixPath

try:
    import pcbnew
except Exception as exc:  # pragma: no cover - CAD-less CI uses the tier-suite skip
    print(f"R5.J1 JLCPCB profile: pcbnew unavailable: {exc}")
    raise SystemExit(2)

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
FAB = REPO / "fab" / "minimal-vga" / "revb"
PROFILE_PATH = HERE / "jlcpcb-profile.json"


def mm(value):
    return pcbnew.ToMM(value)


def expected_filenames(card, spec, profile):
    suffixes = list(profile["archive"]["two_layer_suffixes"])
    if spec["copper_layers"] == 4:
        suffixes += profile["archive"]["four_layer_additional_suffixes"]
    return {f"{card}.drl" if suffix == "drl" else f"{card}-{suffix}"
            for suffix in suffixes}


def archive_errors(card, members, profile):
    spec = profile["boards"][card]
    wanted_names = expected_filenames(card, spec, profile)
    paths = [PurePosixPath(name) for name in members if not name.endswith("/")]
    errors = []
    if any(path.is_absolute() or ".." in path.parts for path in paths):
        errors.append("unsafe archive path")
    if len(paths) != len(set(paths)):
        errors.append("duplicate archive member")
    if profile["archive"]["single_top_directory"]:
        if any(len(path.parts) != 2 or path.parts[0] != card for path in paths):
            errors.append("members must be inside exactly one card-named directory")
    names = {path.name for path in paths}
    if names != wanted_names:
        errors.append(f"production names differ: missing={sorted(wanted_names-names)}, "
                      f"unexpected={sorted(names-wanted_names)}")
    forbidden_ext = {x.lower() for x in profile["archive"]["forbidden_extensions"]}
    forbidden_text = profile["archive"]["forbidden_name_fragments"]
    for path in paths:
        if path.suffix.lower() in forbidden_ext:
            errors.append(f"forbidden upload extension: {path.name}")
        if any(fragment.lower() in path.name.lower() for fragment in forbidden_text):
            errors.append(f"forbidden fabrication/assembly layer: {path.name}")
    return errors


def outline_errors(board, spec):
    edges = [item for item in board.GetDrawings() if item.GetLayer() == pcbnew.Edge_Cuts]
    errors = []
    if len(edges) != 4 or any(not isinstance(item, pcbnew.PCB_SHAPE) for item in edges):
        return [f"outline must be one four-segment rectangle, found {len(edges)} items"]
    endpoints = []
    xs, ys = [], []
    for item in edges:
        start, end = item.GetStart(), item.GetEnd()
        a, z = (start.x, start.y), (end.x, end.y)
        endpoints += [a, z]
        xs += [mm(start.x), mm(end.x)]
        ys += [mm(start.y), mm(end.y)]
    degree = Counter(endpoints)
    if len(degree) != 4 or set(degree.values()) != {2}:
        errors.append("Edge.Cuts is not one closed loop")
    width, height = max(xs) - min(xs), max(ys) - min(ys)
    if abs(width - spec["width_mm"]) > 0.01 or abs(height - spec["height_mm"]) > 0.01:
        errors.append(f"outline {width:.3f}x{height:.3f} mm differs from profile")
    return errors


def annular_ring(pad):
    size, drill = pad.GetSize(), pad.GetDrillSize()
    return min((mm(size.x) - mm(drill.x)) / 2.0,
               (mm(size.y) - mm(drill.y)) / 2.0)


def board_errors(board, card, profile):
    spec = profile["boards"][card]
    geom = profile["geometry"]
    errors = []
    if board.GetCopperLayerCount() != spec["copper_layers"]:
        errors.append(f"{board.GetCopperLayerCount()} copper layers, expected {spec['copper_layers']}")
    thickness = mm(board.GetDesignSettings().GetBoardThickness())
    if abs(thickness - profile["order_options"]["board_thickness_mm"]) > 0.01:
        errors.append(f"board thickness {thickness:.3f} mm differs from profile")
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu, pcbnew.F_Mask, pcbnew.B_Mask,
                  pcbnew.F_SilkS, pcbnew.B_SilkS, pcbnew.Edge_Cuts):
        if not board.IsLayerEnabled(layer):
            errors.append(f"required layer {board.GetLayerName(layer)} is disabled")
    errors += outline_errors(board, spec)

    if spec["copper_layers"] == 4:
        for layer_name, netname in spec["inner_layer_nets"].items():
            layer = board.GetLayerID(layer_name)
            if not board.IsLayerEnabled(layer):
                errors.append(f"required inner layer {layer_name} is disabled")
            zones = [zone for zone in board.Zones()
                     if zone.GetLayer() == layer and zone.GetNetname() == netname]
            if not zones:
                errors.append(f"{layer_name} lacks its required {netname} plane")

    ordinary_min = geom["design_minimum_track_mm"]
    vendor_min = geom["vendor_minimum_track_mm_1oz"]
    allowed_thin = set(geom["video_allowed_0_15mm_track_nets"] if card == "video" else [])
    for item in board.Tracks():
        if isinstance(item, pcbnew.PCB_VIA):
            diameter = mm(item.GetWidth(pcbnew.F_Cu))
            drill = mm(item.GetDrillValue())
            if drill + 1e-6 < geom["via_minimum_drill_mm"]:
                errors.append(f"via drill {drill:.3f} mm below profile")
            if diameter + 1e-6 < geom["via_minimum_diameter_mm"]:
                errors.append(f"via diameter {diameter:.3f} mm below profile")
            if (diameter - drill) / 2.0 + 1e-6 < geom["via_minimum_annular_ring_mm"]:
                errors.append(f"via annular ring {(diameter-drill)/2:.3f} mm below profile")
            continue
        width = mm(item.GetWidth())
        if width + 1e-6 < vendor_min:
            errors.append(f"{item.GetNetname()} track {width:.3f} mm below vendor minimum")
        elif width + 1e-6 < ordinary_min:
            if item.GetNetname() not in allowed_thin or width + 1e-6 < 0.15:
                errors.append(f"unauthorized thin track {item.GetNetname()} {width:.3f} mm")

    default_clearance = mm(board.GetDesignSettings().GetSmallestClearanceValue())
    if default_clearance + 1e-6 < geom["design_default_clearance_mm"]:
        errors.append(f"default clearance {default_clearance:.3f} mm below design policy")
    local_allowed = geom["allowed_local_clearance_mm"]
    for fp in board.GetFootprints():
        key = f"{card}:{fp.GetReference()}"
        values = []
        try:
            value = fp.GetLocalClearance()
            values.append(mm(value) if value is not None else 0.0)
        except Exception:
            pass
        for pad in fp.Pads():
            value = pad.GetLocalClearance()
            values.append(mm(value) if value is not None else 0.0)
        for value in values:
            if not value:
                continue
            if value + 1e-6 < geom["vendor_minimum_clearance_mm_1oz"]:
                errors.append(f"{fp.GetReference()} local clearance {value:.3f} mm below vendor minimum")
            if key not in local_allowed or abs(value - local_allowed[key]) > 1e-6:
                errors.append(f"unapproved local clearance {value:.3f} mm at {fp.GetReference()}")

    pth_recommended = (geom["two_layer_pth_recommended_ring_mm"]
                       if spec["copper_layers"] == 2 else
                       geom["four_layer_pth_recommended_ring_mm"])
    pth_absolute = (geom["two_layer_pth_absolute_ring_mm"]
                    if spec["copper_layers"] == 2 else
                    geom["four_layer_pth_absolute_ring_mm"])
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if not pad.HasHole():
                continue
            drill = pad.GetDrillSize()
            dx, dy = mm(drill.x), mm(drill.y)
            if pad.GetAttribute() == pcbnew.PAD_ATTRIB_PTH:
                ring = annular_ring(pad)
                required = pth_recommended
                if card == "video" and fp.GetReference() == "J_VGA" and pad.GetNumber().isdigit():
                    required = geom["video_exact_vga_signal_ring_mm"]
                elif card == "backplane" and fp.GetReference() == "U_RST":
                    required = geom["backplane_exact_to92_ring_mm"]
                if ring + 1e-6 < max(required, pth_absolute):
                    errors.append(f"{fp.GetReference()}.{pad.GetNumber()} PTH ring {ring:.3f} mm "
                                  f"below {max(required, pth_absolute):.3f} mm")
                if abs(dx - dy) > 1e-6:
                    width, length = min(dx, dy), max(dx, dy)
                    if width + 1e-6 < geom["minimum_plated_slot_width_mm"]:
                        errors.append(f"{fp.GetReference()}.{pad.GetNumber()} plated slot {width:.3f} mm wide")
                    if length + 1e-6 < geom["minimum_plated_slot_length_to_width"] * width:
                        errors.append(f"{fp.GetReference()}.{pad.GetNumber()} plated slot aspect is too short")
            elif abs(dx - dy) > 1e-6 and min(dx, dy) + 1e-6 < geom["minimum_nonplated_slot_width_mm"]:
                errors.append(f"{fp.GetReference()}.{pad.GetNumber()} non-plated slot below profile")

    silk_items = list(board.GetDrawings())
    for fp in board.GetFootprints():
        silk_items += list(fp.GraphicalItems())
    for item in silk_items:
        if item.GetLayer() not in (pcbnew.F_SilkS, pcbnew.B_SilkS):
            continue
        if isinstance(item, pcbnew.PCB_TEXT):
            if not item.IsVisible():
                continue
            if mm(item.GetTextHeight()) + 1e-6 < geom["silkscreen_minimum_text_height_mm"]:
                errors.append(f"silk text {item.GetText()!r} is only {mm(item.GetTextHeight()):.3f} mm high")
            if mm(item.GetTextThickness()) + 1e-6 < geom["silkscreen_minimum_stroke_mm"]:
                errors.append(f"silk text {item.GetText()!r} stroke is below profile")
        else:
            try:
                width = mm(item.GetWidth())
            except Exception:
                continue
            if width and width + 1e-6 < geom["silkscreen_minimum_stroke_mm"]:
                errors.append(f"silk graphic stroke {width:.3f} mm below profile")
    return errors


def drc_errors(card):
    cli = os.environ.get("KICAD_CLI", "")
    if not cli:
        return []
    pcb = FAB / f"{card}.kicad_pcb"
    with tempfile.NamedTemporaryFile(suffix=".json") as report:
        proc = subprocess.run([cli, "pcb", "drc", "--format", "json", "--output",
                               report.name, str(pcb)], capture_output=True, text=True)
        try:
            data = json.loads(Path(report.name).read_text())
        except (json.JSONDecodeError, OSError):
            return [f"DRC did not produce readable JSON: {proc.stderr.strip()}"]
    violations = len(data.get("violations", []))
    unconnected = len(data.get("unconnected_items", []))
    return [] if not (violations or unconnected) else [f"DRC {violations} violations/{unconnected} unconnected"]


def package_errors(card, package_root, profile):
    archive = package_root / f"{card}.zip"
    if not archive.is_file():
        return [f"missing archive {archive}"]
    try:
        with zipfile.ZipFile(archive) as zf:
            errors = archive_errors(card, zf.namelist(), profile)
            corrupt = zf.testzip()
            if corrupt:
                errors.append(f"CRC failure in {corrupt}")
            return errors
    except zipfile.BadZipFile:
        return ["invalid ZIP archive"]


def self_test(profile):
    failures = []
    video_path = FAB / "video.kicad_pcb"

    narrow = pcbnew.LoadBoard(str(video_path))
    next(item for item in narrow.Tracks() if not isinstance(item, pcbnew.PCB_VIA)).SetWidth(pcbnew.FromMM(0.08))
    if not board_errors(narrow, "video", profile):
        failures.append("0.08-mm track mutation accepted")

    bad_via = pcbnew.LoadBoard(str(video_path))
    next(item for item in bad_via.Tracks() if isinstance(item, pcbnew.PCB_VIA)).SetWidth(pcbnew.FromMM(0.40))
    if not board_errors(bad_via, "video", profile):
        failures.append("0.40/0.30-mm via mutation accepted")

    bad_ring = pcbnew.LoadBoard(str(video_path))
    vga = next(fp for fp in bad_ring.GetFootprints() if fp.GetReference() == "J_VGA")
    pad = vga.FindPadByNumber("1")
    size = pad.GetSize()
    pad.SetSize(pcbnew.VECTOR2I(size.x - pcbnew.FromMM(0.1), size.y - pcbnew.FromMM(0.1)))
    if not board_errors(bad_ring, "video", profile):
        failures.append("undersize VGA annular ring mutation accepted")

    open_edge = pcbnew.LoadBoard(str(video_path))
    open_edge.Remove(next(item for item in open_edge.GetDrawings()
                          if item.GetLayer() == pcbnew.Edge_Cuts))
    if not board_errors(open_edge, "video", profile):
        failures.append("open outline mutation accepted")

    bad_silk = pcbnew.LoadBoard(str(video_path))
    label = next(item for item in bad_silk.GetDrawings()
                 if isinstance(item, pcbnew.PCB_TEXT) and item.GetLayer() == pcbnew.F_SilkS)
    label.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(0.5), pcbnew.FromMM(0.5)))
    if not board_errors(bad_silk, "video", profile):
        failures.append("0.5-mm silk text mutation accepted")

    good = {f"video/{name}" for name in expected_filenames("video", profile["boards"]["video"], profile)}
    if archive_errors("video", sorted(good), profile):
        failures.append("valid synthetic Video archive rejected")
    if not archive_errors("video", sorted(good | {"video/video.step"}), profile):
        failures.append("STEP-containing archive accepted")
    missing_inner = {name for name in good if "In2_Cu" not in name}
    if not archive_errors("video", sorted(missing_inner), profile):
        failures.append("archive missing an inner plane accepted")

    if failures:
        print("R5.J1 negative controls FAILED:")
        for failure in failures:
            print(f"    {failure}")
        return False
    print("R5.J1 negative controls OK: narrow track/via/ring, open outline, small silk, "
          "STEP member and missing inner plane all rejected")
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--package-root", type=Path)
    args = parser.parse_args()
    profile = json.loads(PROFILE_PATH.read_text())
    all_errors = []
    for card in profile["boards"]:
        path = FAB / f"{card}.kicad_pcb"
        if not path.is_file():
            all_errors.append(f"{card}: missing routed source {path}")
            continue
        errors = board_errors(pcbnew.LoadBoard(str(path)), card, profile)
        errors += drc_errors(card)
        if args.package_root:
            errors += package_errors(card, args.package_root, profile)
        all_errors += [f"{card}: {error}" for error in errors]
    if all_errors:
        print(f"R5.J1 JLCPCB profile: {len(all_errors)} violation(s) -> FAIL")
        for error in all_errors:
            print(f"    {error}")
        return 1
    print("R5.J1 JLCPCB profile OK: five outlines/stacks, tracks/clearance, drills/slots, "
          "annular rings, masks/silk and upload membership")
    if args.self_test and not self_test(profile):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
