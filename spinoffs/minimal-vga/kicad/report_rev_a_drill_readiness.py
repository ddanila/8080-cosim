#!/usr/bin/env python3
import collections
import math
import re
import sys
from pathlib import Path

import pcbnew


EXPECTED_MOUNTING_HOLES = 4
EXPECTED_MOUNTING_DIAMETER_MM = 3.2
DRILL_TOLERANCE_MM = 0.001


def fmt_mm(value):
    return f"{value:.3f} mm"


def round_drill(value):
    return round(value + 0.0, 3)


def parse_excellon(path):
    tools = {}
    tool_functions = {}
    hits = collections.Counter()
    current_tool = None
    pending_function = None
    metric = False
    markers = {
        "M48": False,
        "METRIC": False,
        "FileFunction": False,
        "M30": False,
    }

    for line in path.read_text(errors="replace").splitlines():
        text = line.strip()
        if text == "M48":
            markers["M48"] = True
        if text == "METRIC":
            markers["METRIC"] = True
            metric = True
        if "TF.FileFunction" in text and "MixedPlating" in text:
            markers["FileFunction"] = True
        if text == "M30":
            markers["M30"] = True
        if "TA.AperFunction" in text:
            pending_function = text.split("TA.AperFunction,", 1)[1].lstrip("; ") if "TA.AperFunction," in text else text
            continue
        tool_match = re.match(r"T(\d+)C([0-9.]+)$", text)
        if tool_match:
            tool, diameter = tool_match.groups()
            tools[tool] = round_drill(float(diameter))
            if pending_function:
                tool_functions[tool] = pending_function
                pending_function = None
            continue
        select_match = re.match(r"T(\d+)$", text)
        if select_match:
            current_tool = select_match.group(1)
            continue
        if current_tool and re.match(r"X[-0-9.]+Y[-0-9.]+$", text):
            hits[current_tool] += 1
        if current_tool and re.match(r"X[-0-9.]+Y[-0-9.]+G85X[-0-9.]+Y[-0-9.]+$", text):
            hits[current_tool] += 1

    return {
        "tools": tools,
        "tool_functions": tool_functions,
        "hits": hits,
        "metric": metric,
        "markers": markers,
    }


def board_drills(board):
    drills = collections.Counter()
    examples = {}
    slot_pads = 0
    for fp in board.Footprints():
        for pad in fp.Pads():
            size = pad.GetDrillSize()
            x = pcbnew.ToMM(size.x)
            y = pcbnew.ToMM(size.y)
            if not x and not y:
                continue
            diameter = round_drill(min(x, y))
            drills[diameter] += 1
            examples.setdefault(diameter, f"{fp.GetReference()}.{pad.GetNumber()}")
            if abs(x - y) > DRILL_TOLERANCE_MM:
                slot_pads += 1
    for track in board.GetTracks():
        if track.GetClass() == "PCB_VIA":
            diameter = round_drill(pcbnew.ToMM(track.GetDrillValue()))
            drills[diameter] += 1
            examples.setdefault(diameter, "via")
    return drills, examples, slot_pads


def edge_cut_mounting_holes(board):
    holes = []
    for drawing in board.Drawings():
        if drawing.GetLayer() != pcbnew.Edge_Cuts:
            continue
        if getattr(drawing, "GetShape", lambda: None)() != pcbnew.SHAPE_T_CIRCLE:
            continue
        center = drawing.GetCenter()
        end = drawing.GetEnd()
        radius = math.hypot(pcbnew.ToMM(end.x - center.x), pcbnew.ToMM(end.y - center.y))
        diameter = round_drill(radius * 2.0)
        if diameter >= 1.0:
            holes.append((diameter, pcbnew.ToMM(center.x), pcbnew.ToMM(center.y)))
    return holes


def build_report(board_path, drill_path):
    board = pcbnew.LoadBoard(str(board_path))
    parsed = parse_excellon(Path(drill_path))
    board_counts, examples, slot_pads = board_drills(board)
    edge_holes = edge_cut_mounting_holes(board)
    drill_counts = collections.Counter()
    for tool, diameter in parsed["tools"].items():
        drill_counts[diameter] += parsed["hits"][tool]

    failures = []
    missing_markers = [name for name, present in parsed["markers"].items() if not present]
    if missing_markers:
        failures.append(f"missing Excellon markers: {', '.join(missing_markers)}")
    if not parsed["metric"]:
        failures.append("drill file is not metric")
    if drill_counts != board_counts:
        failures.append("Excellon drill counts do not match PCB pad/via drill counts")
    if len(edge_holes) != EXPECTED_MOUNTING_HOLES:
        failures.append(f"expected {EXPECTED_MOUNTING_HOLES} Edge.Cuts mounting holes, found {len(edge_holes)}")
    for diameter, x, y in edge_holes:
        if abs(diameter - EXPECTED_MOUNTING_DIAMETER_MM) > DRILL_TOLERANCE_MM:
            failures.append(f"mounting cutout at ({x:.2f}, {y:.2f}) is {fmt_mm(diameter)}, expected {fmt_mm(EXPECTED_MOUNTING_DIAMETER_MM)}")
        if diameter in drill_counts:
            failures.append(f"mounting cutout diameter {fmt_mm(diameter)} also appears as an Excellon drill tool; expected Edge.Cuts-only mounting holes")

    rows = []
    for diameter in sorted(set(board_counts) | set(drill_counts)):
        board_count = board_counts.get(diameter, 0)
        drill_count = drill_counts.get(diameter, 0)
        rows.append(
            {
                "Diameter": fmt_mm(diameter),
                "PCB count": board_count,
                "Excellon count": drill_count,
                "Example": examples.get(diameter, "-"),
                "Status": "PASS" if board_count == drill_count else "FAIL",
            }
        )

    tool_rows = []
    for tool in sorted(parsed["tools"], key=lambda value: int(value)):
        tool_rows.append(
            {
                "Tool": f"T{tool}",
                "Diameter": fmt_mm(parsed["tools"][tool]),
                "Hits": parsed["hits"][tool],
                "Function": parsed["tool_functions"].get(tool, "-"),
            }
        )

    status = "READY" if not failures else "NOT READY"
    lines = [
        "# Rev A drill readiness",
        "",
        f"Board: `{board_path}`",
        f"Drill file: `{drill_path}`",
        f"Status: **{status}**",
        "",
        "This report compares the exported Excellon drill file against the routed",
        "KiCad PCB's through-hole pads and vias. Rev A corner mounting holes are",
        "generated as circular `Edge.Cuts` cutouts, so they are checked here as",
        "mechanical cutouts rather than Excellon drill hits.",
        "",
        "## Summary",
        "",
        f"- Excellon tools: {len(parsed['tools'])}",
        f"- Excellon drill hits: {sum(parsed['hits'].values())}",
        f"- PCB pad/via drill features: {sum(board_counts.values())}",
        f"- Slotted/oval pad drills represented by minor drill size: {slot_pads}",
        f"- Edge.Cuts mounting cutouts: {len(edge_holes)}",
        f"- Expected mounting cutout diameter: {fmt_mm(EXPECTED_MOUNTING_DIAMETER_MM)}",
        f"- Drill readiness failures: {len(failures)}",
        "",
        "## Drill Size Match",
        "",
        "| Diameter | PCB count | Excellon count | Example | Status |",
        "| --- | ---: | ---: | --- | --- |",
    ]
    for row in rows:
        lines.append("| {Diameter} | {PCB count} | {Excellon count} | {Example} | {Status} |".format(**row))
    lines.extend(["", "## Excellon Tools", ""])
    lines.extend(["| Tool | Diameter | Hits | Function |", "| --- | ---: | ---: | --- |"])
    for row in tool_rows:
        safe = {key: str(value).replace("|", "/") for key, value in row.items()}
        lines.append("| {Tool} | {Diameter} | {Hits} | {Function} |".format(**safe))
    lines.extend(["", "## Edge.Cuts Mounting Cutouts", ""])
    lines.extend(["| Diameter | X | Y | Status |", "| ---: | ---: | ---: | --- |"])
    for diameter, x, y in sorted(edge_holes, key=lambda item: (item[2], item[1])):
        ok = abs(diameter - EXPECTED_MOUNTING_DIAMETER_MM) <= DRILL_TOLERANCE_MM
        lines.append(f"| {fmt_mm(diameter)} | {x:.2f} mm | {y:.2f} mm | {'PASS' if ok else 'FAIL'} |")
    if failures:
        lines.extend(["", "## Failures", ""])
        lines.extend(f"- {failure}" for failure in failures)
    lines.append("")
    return "\n".join(lines), not failures


def main():
    board_path = Path(sys.argv[1] if len(sys.argv) > 1 else "spinoffs/minimal-vga/kicad/rev-a-physical.kicad_pcb")
    drill_path = Path(sys.argv[2] if len(sys.argv) > 2 else "fab/minimal-vga/drill/rev-a-physical.drl")
    out_dir = Path(sys.argv[3] if len(sys.argv) > 3 else "fab/minimal-vga")
    report, ready = build_report(board_path, drill_path)
    report_path = out_dir / "drill-readiness.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report)
    print(report)
    print(f"Wrote {report_path}")
    return 0 if ready else 3


if __name__ == "__main__":
    raise SystemExit(main())
