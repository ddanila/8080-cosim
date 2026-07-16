#!/usr/bin/env python3
import sys
from collections import Counter, defaultdict
from pathlib import Path

import pcbnew


SIGNAL_MIN_WIDTH_MM = 0.15
VIA_MIN_DRILL_MM = 0.25
POWER_REVIEW_WIDTH_MM = 0.50
POWER_NETS = ("VCC", "GND", "VCC_RAW")
POWER_PLANES = {
    "GND": "In1.Cu",
    "VCC": "In2.Cu",
}


def mm(value):
    return pcbnew.ToMM(value)


def layer_name(board, layer):
    return board.GetLayerName(layer)


def track_length_mm(track):
    try:
        return mm(track.GetLength())
    except Exception:
        start = track.GetStart()
        end = track.GetEnd()
        return ((mm(start.x - end.x) ** 2) + (mm(start.y - end.y) ** 2)) ** 0.5


def fmt_mm(value):
    return f"{value:.2f} mm"


def classify_tracks(board):
    segments = []
    vias = []
    for item in board.GetTracks():
        if item.Type() == pcbnew.PCB_TRACE_T:
            segments.append(item)
        elif item.Type() == pcbnew.PCB_VIA_T:
            vias.append(item)
    return segments, vias


def via_width_mm(via):
    for layer in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu):
        try:
            width = via.GetWidth(layer)
            if width:
                return mm(width)
        except TypeError:
            continue
    return 0.0


def counter_table(counter, columns):
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for key, value in counter:
        lines.append(f"| {key} | {value} |")
    return lines


def build_report(board_path):
    board = pcbnew.LoadBoard(str(board_path))
    segments, vias = classify_tracks(board)
    zones = list(board.Zones())
    failures = []
    reviews = []

    widths = [mm(track.GetWidth()) for track in segments]
    min_width = min(widths) if widths else 0.0
    if not segments:
        failures.append("No routed track segments found.")
    if widths and min_width < SIGNAL_MIN_WIDTH_MM:
        failures.append(
            f"Minimum track width {fmt_mm(min_width)} is below the hard floor {fmt_mm(SIGNAL_MIN_WIDTH_MM)}."
        )

    via_drills = [mm(via.GetDrillValue()) for via in vias]
    min_via_drill = min(via_drills) if via_drills else 0.0
    if vias and min_via_drill < VIA_MIN_DRILL_MM:
        failures.append(
            f"Minimum via drill {fmt_mm(min_via_drill)} is below the hard floor {fmt_mm(VIA_MIN_DRILL_MM)}."
        )

    by_layer = Counter(layer_name(board, track.GetLayer()) for track in segments)
    by_width = Counter(f"{mm(track.GetWidth()):.2f} mm" for track in segments)
    via_sizes = Counter(
        f"{via_width_mm(via):.2f} / {mm(via.GetDrillValue()):.2f} mm"
        for via in vias
    )

    net_stats = defaultdict(lambda: {"segments": 0, "length": 0.0, "vias": 0, "widths": set()})
    for track in segments:
        net = track.GetNetname() or "<no net>"
        net_stats[net]["segments"] += 1
        net_stats[net]["length"] += track_length_mm(track)
        net_stats[net]["widths"].add(mm(track.GetWidth()))
    for via in vias:
        net = via.GetNetname() or "<no net>"
        net_stats[net]["vias"] += 1

    filled_planes = {}
    for zone in zones:
        layer = zone.GetLayer()
        if zone.IsFilled() and zone.HasFilledPolysForLayer(layer):
            filled_planes[zone.GetNetname()] = layer_name(board, layer)

    for net in POWER_NETS:
        stats = net_stats.get(net)
        plane_layer = filled_planes.get(net)
        expected_plane = POWER_PLANES.get(net)
        if expected_plane and plane_layer != expected_plane:
            failures.append(
                f"Power net {net} lacks its filled {expected_plane} plane."
            )
        if (not stats or stats["segments"] == 0) and not plane_layer:
            failures.append(f"Power net {net} has neither routed tracks nor a filled plane.")
            continue
        if stats and stats["segments"] and not plane_layer:
            power_min = min(stats["widths"])
        else:
            power_min = None
        if power_min is not None and power_min < POWER_REVIEW_WIDTH_MM:
            reviews.append(
                f"{net}: minimum routed width is {fmt_mm(power_min)}, below the review target {fmt_mm(POWER_REVIEW_WIDTH_MM)}."
            )

    if not zones:
        reviews.append("No copper zones are present; the current Rev A baseline routes power explicitly.")
    else:
        zone_nets = sorted({zone.GetNetname() for zone in zones})
        reviews.append("Confirm filled-plane island and return-path behavior for: " + ", ".join(zone_nets))

    status = "NOT READY" if failures else "REVIEW REQUIRED" if reviews else "READY"
    lines = [
        "# Rev A routing geometry readiness",
        "",
        f"Board: `{board_path}`",
        f"Status: **{status}**",
        "",
        "This report summarizes autorouted copper geometry that KiCad DRC does not",
        "interpret as a design-quality review. It catches hard geometry regressions",
        "and records power/return-path items that still need human sign-off.",
        "",
        "## Summary",
        "",
        f"- Routed track segments: {len(segments)}",
        f"- Vias: {len(vias)}",
        f"- Copper zones: {len(zones)}",
        f"- Minimum track width: {fmt_mm(min_width) if widths else '-'}",
        f"- Minimum via drill: {fmt_mm(min_via_drill) if vias else '-'}",
        f"- Hard geometry failures: {len(failures)}",
        f"- Human routing reviews still required: {len(reviews)}",
        "",
        "## Track Widths",
        "",
    ]
    lines.extend(counter_table(sorted(by_width.items()), ["Width", "Segments"]))
    lines.extend(["", "## Layers", ""])
    lines.extend(counter_table(sorted(by_layer.items()), ["Layer", "Segments"]))
    lines.extend(["", "## Via Sizes", ""])
    lines.extend(counter_table(sorted(via_sizes.items()), ["Diameter / drill", "Vias"]))

    lines.extend(
        [
            "",
            "## Power Nets",
            "",
            "| Net | Segments | Vias | Length | Widths | Filled plane |",
            "| --- | ---: | ---: | ---: | --- | --- |",
        ]
    )
    for net in POWER_NETS:
        stats = net_stats.get(net, {"segments": 0, "length": 0.0, "vias": 0, "widths": set()})
        widths_text = ", ".join(fmt_mm(value) for value in sorted(stats["widths"])) or "-"
        plane_text = filled_planes.get(net, "-")
        lines.append(
            f"| {net} | {stats['segments']} | {stats['vias']} | {stats['length']:.1f} mm | {widths_text} | {plane_text} |"
        )

    top_nets = sorted(net_stats.items(), key=lambda item: item[1]["length"], reverse=True)[:12]
    lines.extend(
        [
            "",
            "## Longest Routed Nets",
            "",
            "| Net | Segments | Vias | Length | Widths |",
            "| --- | ---: | ---: | ---: | --- |",
        ]
    )
    for net, stats in top_nets:
        widths_text = ", ".join(fmt_mm(value) for value in sorted(stats["widths"])) or "-"
        lines.append(
            f"| {net} | {stats['segments']} | {stats['vias']} | {stats['length']:.1f} mm | {widths_text} |"
        )

    if failures:
        lines.extend(["", "## Failures", ""])
        lines.extend(f"- {failure}" for failure in failures)
    if reviews:
        lines.extend(["", "## Required Human Reviews", ""])
        lines.extend(f"- {review}" for review in reviews)

    lines.append("")
    return "\n".join(lines), status


def main():
    board_path = Path(sys.argv[1] if len(sys.argv) > 1 else "spinoffs/minimal-vga/kicad/rev-a-physical.kicad_pcb")
    out_dir = Path(sys.argv[2] if len(sys.argv) > 2 else "fab/minimal-vga")
    report, status = build_report(board_path)
    path = out_dir / "routing-geometry-readiness.md"
    path.write_text(report)
    print(report)
    print(f"Wrote {path}")
    return 0 if status in {"READY", "REVIEW REQUIRED"} else 3


if __name__ == "__main__":
    raise SystemExit(main())
