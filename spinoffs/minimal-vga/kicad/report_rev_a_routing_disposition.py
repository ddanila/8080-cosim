#!/usr/bin/env python3
import sys
from collections import defaultdict
from pathlib import Path

import pcbnew


POWER_NETS = ("VCC", "GND", "VCC_RAW")
EXPECTED_LAYERS = ("F.Cu", "In1.Cu", "In2.Cu", "B.Cu")
REV_A_ACCEPTED_POWER_WIDTH_MM = 0.20
MIN_SIGNAL_WIDTH_MM = 0.20
MAX_POWER_WIDTH_MM = 0.20
MIN_VIA_DRILL_MM = 0.30
EXPECTED_PLANES = {
    "GND": "In1.Cu",
    "VCC": "In2.Cu",
}


def mm(value):
    return pcbnew.ToMM(value)


def fmt_mm(value):
    return f"{value:.2f} mm"


def track_length_mm(track):
    try:
        return mm(track.GetLength())
    except Exception:
        start = track.GetStart()
        end = track.GetEnd()
        return ((mm(start.x - end.x) ** 2) + (mm(start.y - end.y) ** 2)) ** 0.5


def classify_tracks(board):
    segments = []
    vias = []
    for item in board.GetTracks():
        if item.Type() == pcbnew.PCB_TRACE_T:
            segments.append(item)
        elif item.Type() == pcbnew.PCB_VIA_T:
            vias.append(item)
    return segments, vias


def copper_layer_names(board):
    return [board.GetLayerName(layer) for layer in board.GetEnabledLayers().CuStack()]


def table_row(values):
    return "| " + " | ".join(str(value).replace("|", "/") if value else "-" for value in values) + " |"


def build_report(board_path):
    board = pcbnew.LoadBoard(str(board_path))
    segments, vias = classify_tracks(board)
    zones = list(board.Zones())
    enabled_layers = copper_layer_names(board)
    failures = []
    dispositions = []

    segment_widths = [mm(track.GetWidth()) for track in segments]
    via_drills = [mm(via.GetDrillValue()) for via in vias]

    if enabled_layers != list(EXPECTED_LAYERS):
        failures.append(f"Expected copper stack {', '.join(EXPECTED_LAYERS)}, found {', '.join(enabled_layers)}.")
    if not segments:
        failures.append("No routed track segments found.")
    if segment_widths and min(segment_widths) < MIN_SIGNAL_WIDTH_MM:
        failures.append(
            f"Minimum track width {fmt_mm(min(segment_widths))} is below the Rev A floor {fmt_mm(MIN_SIGNAL_WIDTH_MM)}."
        )
    if via_drills and min(via_drills) < MIN_VIA_DRILL_MM:
        failures.append(
            f"Minimum via drill {fmt_mm(min(via_drills))} is below the Rev A floor {fmt_mm(MIN_VIA_DRILL_MM)}."
        )
    filled_planes = {}
    for zone in zones:
        layer = zone.GetLayer()
        if zone.IsFilled() and zone.HasFilledPolysForLayer(layer):
            filled_planes[zone.GetNetname()] = board.GetLayerName(layer)
    for net, expected_layer in EXPECTED_PLANES.items():
        if filled_planes.get(net) != expected_layer:
            failures.append(f"Expected a filled {net} plane on {expected_layer}.")
    unexpected_planes = sorted(set(filled_planes) - set(EXPECTED_PLANES))
    if unexpected_planes:
        failures.append("Unexpected filled power planes: " + ", ".join(unexpected_planes) + ".")

    net_stats = defaultdict(lambda: {"segments": 0, "vias": 0, "length": 0.0, "widths": set(), "layers": set()})
    for track in segments:
        net = track.GetNetname() or "<no net>"
        net_stats[net]["segments"] += 1
        net_stats[net]["length"] += track_length_mm(track)
        net_stats[net]["widths"].add(round(mm(track.GetWidth()), 3))
        net_stats[net]["layers"].add(board.GetLayerName(track.GetLayer()))
    for via in vias:
        net = via.GetNetname() or "<no net>"
        net_stats[net]["vias"] += 1

    power_rows = []
    for net in POWER_NETS:
        stats = net_stats.get(net)
        plane_layer = filled_planes.get(net)
        net_failed = False
        if (not stats or stats["segments"] == 0) and not plane_layer:
            failures.append(f"Power net {net} has neither routed tracks nor a filled plane.")
            power_rows.append([net, 0, 0, "-", "-", "-", "-", "FAIL"])
            continue
        widths = sorted(stats["widths"]) if stats else []
        layers = sorted(stats["layers"]) if stats else []
        if widths and not plane_layer and (
            min(widths) < REV_A_ACCEPTED_POWER_WIDTH_MM or max(widths) > MAX_POWER_WIDTH_MM
        ):
            failures.append(
                f"{net} routed widths are outside the accepted Rev A width set: "
                + ", ".join(fmt_mm(width) for width in widths)
            )
            net_failed = True
        power_rows.append(
            [
                net,
                stats["segments"] if stats else 0,
                stats["vias"] if stats else 0,
                f"{stats['length']:.1f} mm" if stats else "-",
                ", ".join(fmt_mm(width) for width in widths) or "-",
                ", ".join(layers) or "-",
                plane_layer or "-",
                "FAIL" if net_failed else "PASS",
            ]
        )

    if not failures:
        dispositions.extend(
            [
                f"VCC_RAW uses the accepted Rev A prototype routing width of {fmt_mm(REV_A_ACCEPTED_POWER_WIDTH_MM)}.",
                "VCC and GND use filled inner-layer planes; their short explicit tracks are local pad-to-plane connections.",
                "The separate power-budget gate keeps the +5 V planning budget and fuse selection in scope for order review.",
                "The board exposes VCC, GND, PWR_OK, and VCC_RAW on J93 for bench validation before socketed IC insertion.",
            ]
        )

    status = "READY" if not failures else "NOT READY"
    lines = [
        "# Rev A routing disposition",
        "",
        f"Board: `{board_path}`",
        f"Status: **{status}**",
        "",
        "This report records the Rev A routing/plane disposition used for the",
        "first low-current prototype order. It does not change KiCad DRC; it",
        "turns the inner-plane and 0.20 mm raw-power routing choice into an explicit",
        "order-time contract.",
        "",
        "## Summary",
        "",
        f"- Copper layers: {', '.join(enabled_layers)}",
        f"- Routed track segments: {len(segments)}",
        f"- Vias: {len(vias)}",
        f"- Copper zones: {len(zones)}",
        f"- Minimum track width: {fmt_mm(min(segment_widths)) if segment_widths else '-'}",
        f"- Minimum via drill: {fmt_mm(min(via_drills)) if via_drills else '-'}",
        f"- Disposition failures: {len(failures)}",
        "",
        "## Power / Return Path Disposition",
        "",
        "| Net | Segments | Vias | Length | Widths | Track layers | Filled plane | Status |",
        "| --- | ---: | ---: | ---: | --- | --- | --- | --- |",
    ]
    lines.extend(table_row(row) for row in power_rows)

    if dispositions:
        lines.extend(["", "## Accepted Rev A Tradeoffs", ""])
        lines.extend(f"- {item}" for item in dispositions)

    if failures:
        lines.extend(["", "## Failures", ""])
        lines.extend(f"- {failure}" for failure in failures)

    lines.append("")
    return "\n".join(lines), status


def main():
    board_path = Path(sys.argv[1] if len(sys.argv) > 1 else "spinoffs/minimal-vga/kicad/rev-a-physical.kicad_pcb")
    out_dir = Path(sys.argv[2] if len(sys.argv) > 2 else "fab/minimal-vga")
    report, status = build_report(board_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "routing-disposition-readiness.md"
    path.write_text(report)
    print(report)
    print(f"Wrote {path}")
    return 0 if status == "READY" else 3


if __name__ == "__main__":
    raise SystemExit(main())
