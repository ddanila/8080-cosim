#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FAB_DIR = ROOT / "fab" / "gerbers"
DEFAULT_REPORT = ROOT / "docs" / "replica-package-geometry-readiness.md"

EXPECTED_EDGE_WIDTH_MM = 310.0
EXPECTED_EDGE_HEIGHT_MM = 266.0
EXPECTED_JOB_SIZE_X_MM = 310.15
EXPECTED_JOB_SIZE_Y_MM = 266.15
EXPECTED_THICKNESS_MM = 1.6
EXPECTED_LAYER_NUMBER = 2
EXPECTED_DRILL_TOOLS = {
    "1": 0.300,
    "2": 0.750,
    "3": 0.800,
    "4": 1.000,
    "5": 1.300,
}
EXPECTED_DRILL_HITS = {
    "1": 315,
    "2": 12,
    "3": 2299,
    "4": 30,
    "5": 5,
}
TOLERANCE_MM = 0.001


def repo_relative(path):
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def table_row(values):
    return "| " + " | ".join(str(value).replace("|", "/") if value not in (None, "") else "-" for value in values) + " |"


def near(actual, expected, tolerance=TOLERANCE_MM):
    return abs(actual - expected) <= tolerance


def gerber_coords(path):
    coords = []
    for match in re.finditer(r"X(-?\d+)Y(-?\d+)D0[12]\*", path.read_text(errors="replace")):
        coords.append((int(match.group(1)) / 1_000_000, int(match.group(2)) / 1_000_000))
    return coords


def edge_bbox(path):
    coords = gerber_coords(path)
    if not coords:
        return None
    xs = [coord[0] for coord in coords]
    ys = [coord[1] for coord in coords]
    return min(xs), min(ys), max(xs), max(ys)


def parse_drill(path):
    tools = {}
    hits = {}
    current_tool = None
    text = path.read_text(errors="replace")
    for line in text.splitlines():
        tool_match = re.fullmatch(r"T(\d+)C([0-9.]+)", line)
        if tool_match:
            tools[tool_match.group(1)] = float(tool_match.group(2))
            continue
        select_match = re.fullmatch(r"T(\d+)", line)
        if select_match:
            current_tool = select_match.group(1)
            continue
        if re.fullmatch(r"X-?[0-9.]+Y-?[0-9.]+", line):
            hits[current_tool] = hits.get(current_tool, 0) + 1
    return text, tools, hits


def build_report(fab_dir):
    failures = []
    job_path = fab_dir / "juku_routed-job.gbrjob"
    edge_path = fab_dir / "juku_routed-Edge_Cuts.gm1"
    drill_path = fab_dir / "juku_routed.drl"

    job = json.loads(job_path.read_text())
    specs = job.get("GeneralSpecs", {})
    size = specs.get("Size", {})
    files = job.get("FilesAttributes", [])
    stackup = job.get("MaterialStackup", [])

    job_size_x = float(size.get("X", -1))
    job_size_y = float(size.get("Y", -1))
    layer_number = int(specs.get("LayerNumber", -1))
    thickness = float(specs.get("BoardThickness", -1))
    copper_files = [file for file in files if file.get("FileFunction", "").startswith("Copper")]
    profile_files = [file for file in files if file.get("FileFunction", "") == "Profile"]
    copper_stack = [layer for layer in stackup if layer.get("Type") == "Copper"]

    if not near(job_size_x, EXPECTED_JOB_SIZE_X_MM) or not near(job_size_y, EXPECTED_JOB_SIZE_Y_MM):
        failures.append(f"Gerber job rendered size changed: {job_size_x:.3f} x {job_size_y:.3f} mm")
    if layer_number != EXPECTED_LAYER_NUMBER:
        failures.append(f"Gerber job layer count changed: {layer_number}")
    if not near(thickness, EXPECTED_THICKNESS_MM):
        failures.append(f"Gerber job board thickness changed: {thickness:.3f} mm")
    if len(copper_files) != EXPECTED_LAYER_NUMBER:
        failures.append(f"Expected {EXPECTED_LAYER_NUMBER} copper files, found {len(copper_files)}")
    if len(copper_stack) != EXPECTED_LAYER_NUMBER:
        failures.append(f"Expected {EXPECTED_LAYER_NUMBER} copper stackup layers, found {len(copper_stack)}")
    if len(profile_files) != 1:
        failures.append(f"Expected one profile file, found {len(profile_files)}")

    bbox = edge_bbox(edge_path)
    if bbox:
        min_x, min_y, max_x, max_y = bbox
        edge_width = max_x - min_x
        edge_height = max_y - min_y
        if not near(edge_width, EXPECTED_EDGE_WIDTH_MM) or not near(edge_height, EXPECTED_EDGE_HEIGHT_MM):
            failures.append(f"Edge.Cuts coordinate box changed: {edge_width:.3f} x {edge_height:.3f} mm")
    else:
        min_x = min_y = max_x = max_y = edge_width = edge_height = 0.0
        failures.append("No Edge.Cuts coordinates found")

    drill_text, drill_tools, drill_hits = parse_drill(drill_path)
    if "M48" not in drill_text or "METRIC" not in drill_text or "FMAT,2" not in drill_text:
        failures.append("Excellon drill header is missing M48/METRIC/FMAT,2 markers")
    if "TF.FileFunction,MixedPlating,1,2" not in drill_text:
        failures.append("Excellon drill file function is not MixedPlating,1,2")
    if drill_tools != EXPECTED_DRILL_TOOLS:
        failures.append(f"Drill tool set changed: {drill_tools}")
    if drill_hits != EXPECTED_DRILL_HITS:
        failures.append(f"Drill hit counts changed: {drill_hits}")

    status = "READY" if not failures else "NOT READY"
    lines = [
        "# Replica package geometry readiness",
        "",
        f"Fabrication package: `{repo_relative(fab_dir)}`",
        f"Status: **{status}**",
        "",
        "This report checks the vendor-visible geometry exported in the Gerber job,",
        "Edge.Cuts Gerber, and Excellon drill file. It turns the order-time",
        "preview dimensions and drill-file expectations into a reproducible local gate.",
        "",
        "## Board Geometry",
        "",
        "| Source | Measurement | Expected | Status |",
        "| --- | --- | --- | --- |",
        table_row(["Gerber job size", f"{job_size_x:.3f} x {job_size_y:.3f} mm", f"{EXPECTED_JOB_SIZE_X_MM:.3f} x {EXPECTED_JOB_SIZE_Y_MM:.3f} mm", "PASS" if near(job_size_x, EXPECTED_JOB_SIZE_X_MM) and near(job_size_y, EXPECTED_JOB_SIZE_Y_MM) else "FAIL"]),
        table_row(["Edge.Cuts coordinate box", f"{edge_width:.3f} x {edge_height:.3f} mm", f"{EXPECTED_EDGE_WIDTH_MM:.3f} x {EXPECTED_EDGE_HEIGHT_MM:.3f} mm", "PASS" if near(edge_width, EXPECTED_EDGE_WIDTH_MM) and near(edge_height, EXPECTED_EDGE_HEIGHT_MM) else "FAIL"]),
        table_row(["Edge.Cuts min/max", f"({min_x:.3f}, {min_y:.3f}) .. ({max_x:.3f}, {max_y:.3f})", "(0.000, -266.000) .. (310.000, 0.000)", "PASS" if bbox and near(min_x, 0.0) and near(min_y, -266.0) and near(max_x, 310.0) and near(max_y, 0.0) else "FAIL"]),
        table_row(["Layer count", layer_number, EXPECTED_LAYER_NUMBER, "PASS" if layer_number == EXPECTED_LAYER_NUMBER else "FAIL"]),
        table_row(["Board thickness", f"{thickness:.3f} mm", f"{EXPECTED_THICKNESS_MM:.3f} mm", "PASS" if near(thickness, EXPECTED_THICKNESS_MM) else "FAIL"]),
        table_row(["Copper files", len(copper_files), EXPECTED_LAYER_NUMBER, "PASS" if len(copper_files) == EXPECTED_LAYER_NUMBER else "FAIL"]),
        table_row(["Profile files", len(profile_files), 1, "PASS" if len(profile_files) == 1 else "FAIL"]),
        "",
        "## Drill File",
        "",
        "| Tool | Diameter mm | Hits | Expected hits | Status |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for tool in sorted(EXPECTED_DRILL_TOOLS, key=int):
        diameter = drill_tools.get(tool)
        hits = drill_hits.get(tool, 0)
        diameter_ok = diameter is not None and near(diameter, EXPECTED_DRILL_TOOLS[tool])
        hits_ok = hits == EXPECTED_DRILL_HITS[tool]
        lines.append(table_row([
            f"T{tool}",
            f"{diameter:.3f}" if diameter is not None else "-",
            hits,
            EXPECTED_DRILL_HITS[tool],
            "PASS" if diameter_ok and hits_ok else "FAIL",
        ]))

    lines.extend([
        "",
        "## Upload Implications",
        "",
        "- Vendor preview should show a 2-layer board.",
        "- Vendor preview should show the 310 mm x 266 mm Edge.Cuts coordinate box; a 310.15 mm x 266.15 mm rendered job size is the 0.15 mm profile aperture envelope.",
        "- Vendor preview should ingest one mixed-plating Excellon drill file with the five tool groups above.",
    ])

    if failures:
        lines.extend(["", "## Failures", ""])
        lines.extend(f"- {failure}" for failure in failures)

    lines.append("")
    return "\n".join(lines), not failures


def main():
    fab_dir = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT_FAB_DIR
    report_path = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else DEFAULT_REPORT
    report, ok = build_report(fab_dir)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report)
    print(report)
    print(f"Wrote {repo_relative(report_path)}")
    return 0 if ok else 3


if __name__ == "__main__":
    raise SystemExit(main())
