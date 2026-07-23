#!/usr/bin/env python3
import os
import sys

import pcbnew

# Block outlines/labels are computed by the generator from the placed parts, so
# the checker verifies against the same source of truth instead of hardcoded
# coordinates (which went stale when the board was re-laid-out to 200x200).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_rev_a_pcb as gen
import fix_rev_a_refresh_counter as refresh_fix


MM_TOLERANCE = 0.05
EXPECTED_COPPER_LAYERS = ("F.Cu", "In1.Cu", "In2.Cu", "B.Cu")
# Component-to-edge keepout. Matches the generator's EDGE_CLEARANCE_MM. (The old
# 14 mm value was comfortable on the sparse 285 mm board; the 200 mm compact
# board uses the standard 5 mm THT edge clearance, with the corners kept clear of
# the mounting-hole standoffs by placement.)
MIN_EDGE_CLEARANCE_MM = 5
MIN_SILK_EDGE_CLEARANCE_MM = 1.0
EXPECTED_SILK_LABELS = (
    "VJUGA REV A",
    "Z80 + 4164 DRAM REFRESH TESTBED",
    "CLOCK + RESET",
    "DEFAULT STROKE SILK",
)
EXPECTED_ZONES = {
    "Rev A GND plane placeholder": ("In1.Cu", "GND"),
    "Rev A VCC plane placeholder": ("In2.Cu", "VCC"),
}
# Block titles/frames are verified against gen.SILK_BLOCK_LABELS (single source
# of truth), computed from the placed parts.
EXPECTED_CHIP_BLOCK_LABELS = {
    "CPU": "U1",
    "ROM": "U2",
    "ADDRESS DECODE": "U5",
    "DRAM CONTROL": "U24",
    "PARALLEL INTERFACE": "U30",
}
EXPECTED_SILK_VALUES = {
    "U5": "GAL22V10",
    "U24": "GAL22V10",
    "U30": "82C55",
}
# J3 is the board-edge USB-C connector; its labels are placed inboard (to the
# right of the body) so they clear the board edge, not below the footprint.
EXPECTED_DOWNSTAIRS_VALUE_REFS = {
    "C50",
    "D1",
    "D2",
    "D3",
    "D4",
    "D5",
    "D6",
    "D7",
    "J30",
    "J90",
    "J91",
    "J92",
    "J93",
    "U40",
    "U51",
}
CHIP_BLOCK_LABEL_GAP_MM = 2.0
SILK_BLOCK_LABEL_PADDING_MM = 2.0
ALLOWED_SMD_REFS = {"J3"}
ADDRMUX_ENABLE_ENDPOINTS = (("U20", "15"), ("U21", "15"))
ADDRMUX_ENABLE_SEGMENTS_MM = {
    ((64.7700, 90.1700), (70.4870, 90.1700)),
    ((70.4870, 90.1700), (71.5982, 91.2812)),
    ((71.5982, 91.2812), (78.8988, 91.2812)),
    ((78.8988, 91.2812), (80.0100, 90.1700)),
}


def fail(message):
    raise SystemExit(f"Rev A PCB check: FAIL: {message}")


def silk_text_items(board):
    for drawing in board.Drawings():
        text = pcbnew.Cast_to_PCB_TEXT(drawing)
        if text and text.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS):
            yield "board", text.GetText(), text
    for fp in board.Footprints():
        for text in (fp.Reference(), fp.Value()):
            if (
                text
                and text.IsVisible()
                and text.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS)
            ):
                yield fp.GetReference(), text.GetText(), text


def segment_points(shape):
    return (
        round(pcbnew.ToMM(shape.GetStart().x), 2),
        round(pcbnew.ToMM(shape.GetStart().y), 2),
        round(pcbnew.ToMM(shape.GetEnd().x), 2),
        round(pcbnew.ToMM(shape.GetEnd().y), 2),
    )


def matching_silk_segment(board, expected):
    ex1, ey1, ex2, ey2 = expected
    for drawing in board.Drawings():
        shape = pcbnew.Cast_to_PCB_SHAPE(drawing)
        if not shape or shape.GetLayer() != pcbnew.F_SilkS:
            continue
        if shape.GetShape() != pcbnew.SHAPE_T_SEGMENT:
            continue
        x1, y1, x2, y2 = segment_points(shape)
        forward = (
            abs(x1 - ex1) <= MM_TOLERANCE
            and abs(y1 - ey1) <= MM_TOLERANCE
            and abs(x2 - ex2) <= MM_TOLERANCE
            and abs(y2 - ey2) <= MM_TOLERANCE
        )
        reverse = (
            abs(x1 - ex2) <= MM_TOLERANCE
            and abs(y1 - ey2) <= MM_TOLERANCE
            and abs(x2 - ex1) <= MM_TOLERANCE
            and abs(y2 - ey1) <= MM_TOLERANCE
        )
        if forward or reverse:
            return True
    return False


def missing_silk_outline_edges(board, name, bounds, title):
    left, top, right, bottom = bounds
    edges = {
        "right": (right, top, right, bottom),
        "bottom": (right, bottom, left, bottom),
        "left": (left, bottom, left, top),
    }
    # The top border is drawn as one full segment (untitled) or two stubs
    # flanking the inset title -- computed the same way the generator draws it.
    for i, seg in enumerate(gen.block_top_segments(bounds, title)):
        edges[f"top{i}"] = seg
    return [edge for edge, segment in edges.items() if not matching_silk_segment(board, segment)]


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "spinoffs/minimal-vga/kicad/rev-a-physical.kicad_pcb"
    board = pcbnew.LoadBoard(path)
    # Expected functional-block frames, computed from the placed parts exactly as
    # the generator draws them.
    block_outlines = gen.compute_block_outlines(
        {fp.GetReference(): fp for fp in board.Footprints()}
    )
    copper_count = board.GetCopperLayerCount()
    if copper_count != len(EXPECTED_COPPER_LAYERS):
        fail(f"expected {len(EXPECTED_COPPER_LAYERS)} copper layers, found {copper_count}")

    names = {board.GetLayerName(layer_id) for layer_id in range(pcbnew.PCB_LAYER_ID_COUNT)}
    missing = [layer for layer in EXPECTED_COPPER_LAYERS if layer not in names]
    if missing:
        fail(f"missing copper layers: {', '.join(missing)}")

    footprint_count = sum(1 for _ in board.Footprints())
    if footprint_count < 80:
        fail(f"expected physical Rev A footprints, found only {footprint_count}")
    track_count = sum(1 for _ in board.GetTracks())
    for ref, pin in ADDRMUX_ENABLE_ENDPOINTS:
        footprint = board.FindFootprintByReference(ref)
        endpoint = footprint.FindPadByNumber(pin) if footprint else None
        if endpoint is None:
            fail(f"missing address-mux enable endpoint {ref}.{pin}")
        if endpoint.GetNetname() != "GND":
            fail(
                f"{ref}.{pin} active-low address-mux enable is "
                f"{endpoint.GetNetname() or '<no net>'}, expected GND"
            )
    enable_segments = set()
    for track in board.GetTracks():
        if type(track).__name__ != "PCB_TRACK":
            continue
        start = (
            round(pcbnew.ToMM(track.GetStart().x), 4),
            round(pcbnew.ToMM(track.GetStart().y), 4),
        )
        end = (
            round(pcbnew.ToMM(track.GetEnd().x), 4),
            round(pcbnew.ToMM(track.GetEnd().y), 4),
        )
        segment = tuple(sorted((start, end)))
        if segment in ADDRMUX_ENABLE_SEGMENTS_MM:
            if track.GetNetname() != "GND":
                fail(
                    "retained address-mux enable segment "
                    f"{segment} is {track.GetNetname() or '<no net>'}, expected GND"
                )
            enable_segments.add(segment)
    missing_enable_segments = ADDRMUX_ENABLE_SEGMENTS_MM - enable_segments
    if missing_enable_segments:
        fail(
            "missing retained GND address-mux enable segment(s): "
            + ", ".join(str(segment) for segment in sorted(missing_enable_segments))
        )
    retired_mux_tracks = [
        track for track in board.GetTracks() if track.GetNetname() == "ADDRMUX_OE_N"
    ]
    if retired_mux_tracks:
        fail(
            f"retired ADDRMUX_OE_N still owns {len(retired_mux_tracks)} track(s)"
        )
    u22 = board.FindFootprintByReference("U22")
    if u22 is None:
        fail("missing refresh counter U22")
    for pin in ("2", "12"):
        endpoint = u22.FindPadByNumber(pin)
        if endpoint is None or endpoint.GetNetname() != "GND":
            actual = endpoint.GetNetname() if endpoint else "<missing>"
            fail(f"U22.{pin} active-high reset is {actual}, expected GND")
    cascade_clock = u22.FindPadByNumber("13")
    if (
        cascade_clock is None
        or cascade_clock.GetNetname() != refresh_fix.CASCADE_NET
    ):
        actual = cascade_clock.GetNetname() if cascade_clock else "<missing>"
        fail(
            f"U22.13 high-nibble clock is {actual}, "
            f"expected {refresh_fix.CASCADE_NET}"
        )
    retired_refresh_tracks = [
        track for track in board.GetTracks() if track.GetNetname() == "REFRESH_CLR"
    ]
    if retired_refresh_tracks:
        fail(
            f"retired REFRESH_CLR still owns {len(retired_refresh_tracks)} track(s)"
        )
    if (
        refresh_fix.present_cascade_tracks(board)
        != refresh_fix.expected_cascade_tracks()
        or refresh_fix.present_cascade_vias(board) != set(refresh_fix.CASCADE_VIAS)
        or refresh_fix.matching_cascade_track_count(board)
        != len(refresh_fix.CASCADE_TRACKS)
        or refresh_fix.matching_cascade_via_count(board)
        != len(refresh_fix.CASCADE_VIAS)
    ):
        fail("U22.6-to-U22.13 refresh-counter cascade copper is incomplete")
    inner_signal_tracks = [
        track
        for track in board.GetTracks()
        if type(track).__name__ == "PCB_TRACK"
        and board.GetLayerName(track.GetLayer()) in {"In1.Cu", "In2.Cu"}
    ]
    if inner_signal_tracks:
        fail(
            f"reserved GND/VCC plane layers carry {len(inner_signal_tracks)} signal tracks"
        )

    # Board-edge connectors (e.g. the USB-C power receptacle) are meant to sit at
    # the board edge, so they are exempt from the general edge-keepout rule.
    EDGE_CONNECTORS = {"J3"}
    # Measure clearance against the actual board outline (Edge.Cuts) rather than a
    # hardcoded width -- the board shrank from 285 mm to 200 mm, and a fixed
    # constant silently stops checking the right/bottom edges.
    edge_box = board.GetBoardEdgesBoundingBox()
    board_left = pcbnew.ToMM(edge_box.GetLeft())
    board_top = pcbnew.ToMM(edge_box.GetTop())
    board_right = pcbnew.ToMM(edge_box.GetRight())
    board_bottom = pcbnew.ToMM(edge_box.GetBottom())
    edge_violations = []
    for fp in board.Footprints():
        if fp.GetReference() in EDGE_CONNECTORS:
            continue
        box = fp.GetBoundingBox(False, False)
        left = pcbnew.ToMM(box.GetLeft())
        top = pcbnew.ToMM(box.GetTop())
        right = pcbnew.ToMM(box.GetRight())
        bottom = pcbnew.ToMM(box.GetBottom())
        margin = min(
            left - board_left,
            top - board_top,
            board_right - right,
            board_bottom - bottom,
        )
        if margin < MIN_EDGE_CLEARANCE_MM:
            edge_violations.append(f"{fp.GetReference()}={margin:.1f}mm")
    if edge_violations:
        fail(
            f"footprints too close to board edge "
            f"(<{MIN_EDGE_CLEARANCE_MM}mm): {', '.join(edge_violations)}"
        )

    duplicate_value_refs = []
    for fp in board.Footprints():
        if fp.GetReference() == fp.GetValue():
            duplicate_value_refs.append(fp.GetReference())
    if duplicate_value_refs:
        fail(f"footprint values duplicate refdes: {', '.join(sorted(duplicate_value_refs))}")

    unexpected_smd_refs = []
    for fp in board.Footprints():
        if fp.GetReference() in ALLOWED_SMD_REFS:
            continue
        if any(pad.GetAttribute() == pcbnew.PAD_ATTRIB_SMD for pad in fp.Pads()):
            unexpected_smd_refs.append(fp.GetReference())
    if unexpected_smd_refs:
        fail(
            "unexpected SMD pads on mostly-through-hole Rev A board: "
            + ", ".join(sorted(unexpected_smd_refs))
        )

    zones = {}
    for zone in board.Zones():
        layer = zone.GetLayer()
        zones[zone.GetZoneName()] = (
            board.GetLayerName(layer),
            zone.GetNetname(),
            zone.GetNumCorners(),
            zone.IsFilled(),
            zone.HasFilledPolysForLayer(layer),
        )
    for zone_name, (layer, net) in EXPECTED_ZONES.items():
        if zone_name not in zones:
            fail(f"missing zone: {zone_name}")
        actual_layer, actual_net, corner_count, is_filled, has_fill = zones[zone_name]
        if (actual_layer, actual_net) != (layer, net):
            fail(
                f"{zone_name} expected on {layer}/{net}, "
                f"found {actual_layer}/{actual_net}"
            )
        if corner_count < 4:
            fail(f"{zone_name} has incomplete outline ({corner_count} corners)")
        if not is_filled or not has_fill:
            fail(f"{zone_name} is not filled")

    for label in EXPECTED_SILK_LABELS:
        matches = [
            text
            for _, _, text in silk_text_items(board)
            if (
                text.GetText() == label
                and text.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS)
            )
        ]
        if not matches:
            fail(f"missing silkscreen label: {label}")
        for text in matches:
            if text.IsItalic():
                fail(f"silkscreen label is italic: {label}")
            if text.GetFontName():
                fail(
                    f"silkscreen label uses custom font '{text.GetFontName()}'; "
                    f"expected default footprint text style: {label}"
                )

    # Titles are printed ON each frame's top border, inset from the left corner;
    # a block in gen.SILK_BLOCK_LABEL_DROP is framed but untitled.
    block_label_violations = []
    for name, label in gen.SILK_BLOCK_LABELS.items():
        if name not in block_outlines:
            continue
        matches = [
            text
            for _, _, text in silk_text_items(board)
            if text.GetText() == label and text.GetLayer() == pcbnew.F_SilkS
        ]
        if name in gen.SILK_BLOCK_LABEL_DROP:
            if matches:
                block_label_violations.append(f"{label}:should-be-dropped")
            continue
        expected_pos = gen.silk_block_title_anchor(block_outlines[name])
        if not matches:
            block_label_violations.append(f"{label}:missing")
            continue
        for text in matches:
            x = pcbnew.ToMM(text.GetTextPos().x)
            y = pcbnew.ToMM(text.GetTextPos().y)
            if abs(x - expected_pos[0]) > MM_TOLERANCE or abs(y - expected_pos[1]) > MM_TOLERANCE:
                block_label_violations.append(
                    f"{label}=({x:.2f},{y:.2f}) expected=({expected_pos[0]:.2f},{expected_pos[1]:.2f})"
                )
    if block_label_violations:
        fail("silkscreen block titles are not on their frame's top border: " + "; ".join(block_label_violations))

    chip_label_violations = []
    for label, ref in EXPECTED_CHIP_BLOCK_LABELS.items():
        fp = board.FindFootprintByReference(ref)
        if fp is None:
            chip_label_violations.append(f"{label}:{ref}:missing-footprint")
            continue
        # Function name is a second line INSIDE the chip, below its value.
        expected_x, expected_y = gen.chip_function_anchor(fp)
        matches = [
            text
            for _, _, text in silk_text_items(board)
            if text.GetText() == label and text.GetLayer() == pcbnew.F_SilkS
        ]
        if not matches:
            chip_label_violations.append(f"{label}:missing")
            continue
        for text in matches:
            x = pcbnew.ToMM(text.GetTextPos().x)
            y = pcbnew.ToMM(text.GetTextPos().y)
            if abs(x - expected_x) > MM_TOLERANCE or abs(y - expected_y) > MM_TOLERANCE:
                chip_label_violations.append(
                    f"{label}=({x:.2f},{y:.2f}) expected=({expected_x:.2f},{expected_y:.2f})"
                )
    if chip_label_violations:
        fail("chip function labels are not centred inside the chip: " + "; ".join(chip_label_violations))

    silk_value_violations = []
    for ref, expected_value in EXPECTED_SILK_VALUES.items():
        fp = board.FindFootprintByReference(ref)
        if fp is None:
            silk_value_violations.append(f"{ref}:missing-footprint")
            continue
        if fp.Value().GetText() != expected_value:
            silk_value_violations.append(f"{ref}={fp.Value().GetText()} expected={expected_value}")
    if silk_value_violations:
        fail("named chip silkscreen values are not as expected: " + "; ".join(silk_value_violations))

    downstairs_violations = []
    for ref in EXPECTED_DOWNSTAIRS_VALUE_REFS:
        fp = board.FindFootprintByReference(ref)
        if fp is None:
            downstairs_violations.append(f"{ref}:missing-footprint")
            continue
        if not fp.Value().IsVisible():
            downstairs_violations.append(f"{ref}:value-hidden")
            continue
        fp_box = fp.GetBoundingBox(False, False)
        value_box = fp.Value().GetBoundingBox()
        gap = pcbnew.ToMM(value_box.GetTop()) - pcbnew.ToMM(fp_box.GetBottom())
        if gap < 0.2:
            downstairs_violations.append(f"{ref}:value-not-downstairs gap={gap:.2f}mm")
    if downstairs_violations:
        fail("connector/detail values are not below their footprints: " + "; ".join(downstairs_violations))

    silk_edge_violations = []
    for owner, text_value, text in silk_text_items(board):
        box = text.GetBoundingBox()
        left = pcbnew.ToMM(box.GetLeft())
        top = pcbnew.ToMM(box.GetTop())
        right = pcbnew.ToMM(box.GetRight())
        bottom = pcbnew.ToMM(box.GetBottom())
        margin = min(
            left - board_left,
            top - board_top,
            board_right - right,
            board_bottom - bottom,
        )
        if margin < MIN_SILK_EDGE_CLEARANCE_MM:
            silk_edge_violations.append(
                f"{owner}:{text_value}={margin:.2f}mm "
                f"box=({left:.2f},{top:.2f},{right:.2f},{bottom:.2f})"
            )
    if silk_edge_violations:
        fail(
            "silkscreen text too close to board edge "
            f"(<{MIN_SILK_EDGE_CLEARANCE_MM:.1f}mm): "
            + "; ".join(silk_edge_violations)
        )

    missing_outlines = []
    for name, bounds in block_outlines.items():
        title = None if name in gen.SILK_BLOCK_LABEL_DROP else gen.SILK_BLOCK_LABELS[name]
        missing_edges = missing_silk_outline_edges(board, name, bounds, title)
        if missing_edges:
            missing_outlines.append(f"{name}:{','.join(missing_edges)}")
    if missing_outlines:
        fail(f"missing silkscreen block outline edges: {'; '.join(missing_outlines)}")

    print(
        "Rev A PCB check: PASS "
        f"({copper_count} copper layers: {', '.join(EXPECTED_COPPER_LAYERS)}, "
        f"{footprint_count} footprints, {board.GetNetCount() - 1} named nets, "
        f"{track_count} tracks, {len(zones)} power zones)"
    )


if __name__ == "__main__":
    main()
