#!/usr/bin/env python3
import math
import sys
from pathlib import Path

import pcbnew


MM_PER_IU = 1_000_000.0
EXPECTED_BOARD_MM = 285.0
EXPECTED_HOLE_CENTERS_MM = ((8.0, 8.0), (277.0, 8.0), (8.0, 277.0), (277.0, 277.0))
EXPECTED_HOLE_DIAMETER_MM = 3.2
HOLE_TOLERANCE_MM = 0.05
MIN_EDGE_WEB_MM = 5.0
MIN_FOOTPRINT_CLEARANCE_MM = 3.0
MIN_TRACK_CLEARANCE_MM = 1.0


def to_mm(value):
    return value / MM_PER_IU


def point_mm(point):
    return to_mm(point.x), to_mm(point.y)


def fmt_mm(value):
    return f"{value:.2f} mm"


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def point_to_segment_distance(point, start, end):
    px, py = point
    sx, sy = start
    ex, ey = end
    dx = ex - sx
    dy = ey - sy
    length_sq = dx * dx + dy * dy
    if length_sq == 0:
        return dist(point, start)
    t = max(0.0, min(1.0, ((px - sx) * dx + (py - sy) * dy) / length_sq))
    return dist(point, (sx + t * dx, sy + t * dy))


def point_to_box_distance(point, box):
    px, py = point
    left, top, right, bottom = box
    dx = max(left - px, 0.0, px - right)
    dy = max(top - py, 0.0, py - bottom)
    return math.hypot(dx, dy)


def edge_shapes(board):
    return [shape for shape in board.Drawings() if shape.GetLayer() == pcbnew.Edge_Cuts]


def edge_segments(board):
    segments = []
    for shape in edge_shapes(board):
        if getattr(shape, "GetShape", lambda: None)() == pcbnew.SHAPE_T_SEGMENT:
            segments.append((point_mm(shape.GetStart()), point_mm(shape.GetEnd())))
    return segments


def mounting_holes(board):
    holes = []
    for shape in edge_shapes(board):
        if getattr(shape, "GetShape", lambda: None)() != pcbnew.SHAPE_T_CIRCLE:
            continue
        center = point_mm(shape.GetCenter())
        end = point_mm(shape.GetEnd())
        radius = dist(center, end)
        if radius <= 10.0:
            holes.append({"center": center, "radius": radius, "diameter": radius * 2.0})
    return sorted(holes, key=lambda item: (item["center"][1], item["center"][0]))


def board_bounds(segments):
    xs = []
    ys = []
    for start, end in segments:
        xs.extend((start[0], end[0]))
        ys.extend((start[1], end[1]))
    if not xs or not ys:
        return None
    return min(xs), min(ys), max(xs), max(ys)


def outline_edge_web(hole, bounds):
    x, y = hole["center"]
    left, top, right, bottom = bounds
    return min(x - left, y - top, right - x, bottom - y) - hole["radius"]


def min_footprint_clearance(board, hole):
    closest = None
    center = hole["center"]
    for fp in board.Footprints():
        box = fp.GetBoundingBox(False, False)
        fp_box = (
            pcbnew.ToMM(box.GetLeft()),
            pcbnew.ToMM(box.GetTop()),
            pcbnew.ToMM(box.GetRight()),
            pcbnew.ToMM(box.GetBottom()),
        )
        clearance = point_to_box_distance(center, fp_box) - hole["radius"]
        item = (clearance, fp.GetReference())
        if closest is None or item < closest:
            closest = item
    return closest


def min_track_clearance(board, hole):
    closest = None
    center = hole["center"]
    for track in board.GetTracks():
        if track.GetClass() == "PCB_VIA":
            via_center = point_mm(track.GetStart())
            clearance = dist(center, via_center) - hole["radius"] - to_mm(track.GetFrontWidth()) / 2.0
            item = (clearance, track.GetNetname() or "-", "via")
        elif hasattr(track, "GetStart") and hasattr(track, "GetEnd"):
            start = point_mm(track.GetStart())
            end = point_mm(track.GetEnd())
            clearance = point_to_segment_distance(center, start, end) - hole["radius"] - to_mm(track.GetWidth()) / 2.0
            item = (clearance, track.GetNetname() or "-", board.GetLayerName(track.GetLayer()))
        else:
            continue
        if closest is None or item < closest:
            closest = item
    return closest


def expected_match(holes):
    rows = []
    failures = []
    unmatched = holes[:]
    for expected in EXPECTED_HOLE_CENTERS_MM:
        if not unmatched:
            failures.append(f"missing mounting hole at {expected}")
            rows.append((expected, None, None, None, "FAIL"))
            continue
        nearest = min(unmatched, key=lambda hole: dist(hole["center"], expected))
        unmatched.remove(nearest)
        center_error = dist(nearest["center"], expected)
        diameter_error = abs(nearest["diameter"] - EXPECTED_HOLE_DIAMETER_MM)
        status = "PASS" if center_error <= HOLE_TOLERANCE_MM and diameter_error <= HOLE_TOLERANCE_MM else "FAIL"
        if status != "PASS":
            failures.append(
                f"hole at {nearest['center']} does not match expected {expected}: "
                f"center error {fmt_mm(center_error)}, diameter error {fmt_mm(diameter_error)}"
            )
        rows.append((expected, nearest, center_error, diameter_error, status))
    for hole in unmatched:
        failures.append(f"unexpected extra mounting hole at {hole['center']}")
    return rows, failures


def build_report(board_path):
    board = pcbnew.LoadBoard(str(board_path))
    segments = edge_segments(board)
    bounds = board_bounds(segments)
    holes = mounting_holes(board)
    match_rows, failures = expected_match(holes)

    if bounds is None:
        failures.append("board outline segment bounds unavailable")
        bounds_text = "unavailable"
    else:
        left, top, right, bottom = bounds
        width = right - left
        height = bottom - top
        bounds_text = f"{fmt_mm(width)} x {fmt_mm(height)}"
        if abs(width - EXPECTED_BOARD_MM) > HOLE_TOLERANCE_MM or abs(height - EXPECTED_BOARD_MM) > HOLE_TOLERANCE_MM:
            failures.append(f"board outline is {bounds_text}; expected {EXPECTED_BOARD_MM:.2f} mm square")

    rows = []
    for expected, hole, _, _, status in match_rows:
        if not hole or not bounds:
            rows.append(
                {
                    "Expected center": f"({expected[0]:.2f}, {expected[1]:.2f})",
                    "Actual center": "missing",
                    "Diameter": "-",
                    "Edge web": "-",
                    "Nearest footprint": "-",
                    "Nearest track": "-",
                    "Status": status,
                }
            )
            continue

        edge_web = outline_edge_web(hole, bounds)
        fp_clearance = min_footprint_clearance(board, hole)
        track_clearance = min_track_clearance(board, hole)
        if edge_web < MIN_EDGE_WEB_MM:
            status = "FAIL"
            failures.append(f"hole {expected} edge web is {fmt_mm(edge_web)}, below {fmt_mm(MIN_EDGE_WEB_MM)}")
        if fp_clearance and fp_clearance[0] < MIN_FOOTPRINT_CLEARANCE_MM:
            status = "FAIL"
            failures.append(
                f"hole {expected} footprint clearance is {fmt_mm(fp_clearance[0])} to {fp_clearance[1]}, "
                f"below {fmt_mm(MIN_FOOTPRINT_CLEARANCE_MM)}"
            )
        if track_clearance and track_clearance[0] < MIN_TRACK_CLEARANCE_MM:
            status = "FAIL"
            failures.append(
                f"hole {expected} track clearance is {fmt_mm(track_clearance[0])} to "
                f"{track_clearance[1]} on {track_clearance[2]}, below {fmt_mm(MIN_TRACK_CLEARANCE_MM)}"
            )
        rows.append(
            {
                "Expected center": f"({expected[0]:.2f}, {expected[1]:.2f})",
                "Actual center": f"({hole['center'][0]:.2f}, {hole['center'][1]:.2f})",
                "Diameter": fmt_mm(hole["diameter"]),
                "Edge web": fmt_mm(edge_web),
                "Nearest footprint": f"{fp_clearance[1]} at {fmt_mm(fp_clearance[0])}" if fp_clearance else "-",
                "Nearest track": f"{track_clearance[1]} {track_clearance[2]} at {fmt_mm(track_clearance[0])}" if track_clearance else "-",
                "Status": status,
            }
        )

    status = "READY" if not failures else "NOT READY"
    lines = [
        "# Rev A mounting-hole readiness",
        "",
        f"Board: `{board_path}`",
        f"Status: **{status}**",
        "",
        "This report checks the generated mechanical mounting holes on `Edge.Cuts`.",
        "It proves the board has the intended corner holes and enough local",
        "clearance for Rev A fabrication review; enclosure/standoff selection is",
        "still a separate human/mechanical decision.",
        "",
        "## Summary",
        "",
        f"- Board outline: {bounds_text}",
        f"- Expected mounting holes: {len(EXPECTED_HOLE_CENTERS_MM)}",
        f"- Detected mounting holes: {len(holes)}",
        f"- Expected hole diameter: {fmt_mm(EXPECTED_HOLE_DIAMETER_MM)}",
        f"- Minimum edge web target: {fmt_mm(MIN_EDGE_WEB_MM)}",
        f"- Minimum footprint clearance target: {fmt_mm(MIN_FOOTPRINT_CLEARANCE_MM)}",
        f"- Minimum routed-track clearance target: {fmt_mm(MIN_TRACK_CLEARANCE_MM)}",
        f"- Mounting-hole failures: {len(failures)}",
        "",
        "## Holes",
        "",
        "| Expected center | Actual center | Diameter | Edge web | Nearest footprint | Nearest track | Status |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        safe = {key: str(value).replace("|", "/") for key, value in row.items()}
        lines.append(
            "| {Expected center} | {Actual center} | {Diameter} | {Edge web} | {Nearest footprint} | {Nearest track} | {Status} |".format(
                **safe
            )
        )
    if failures:
        lines.extend(["", "## Failures", ""])
        lines.extend(f"- {failure}" for failure in failures)
    lines.append("")
    return "\n".join(lines), not failures


def main():
    board_path = Path(sys.argv[1] if len(sys.argv) > 1 else "spinoffs/minimal-vga/kicad/rev-a-physical.kicad_pcb")
    out_dir = Path(sys.argv[2] if len(sys.argv) > 2 else "fab/minimal-vga")
    report, ready = build_report(board_path)
    report_path = out_dir / "mounting-hole-readiness.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report)
    print(report)
    print(f"Wrote {report_path}")
    return 0 if ready else 3


if __name__ == "__main__":
    raise SystemExit(main())
