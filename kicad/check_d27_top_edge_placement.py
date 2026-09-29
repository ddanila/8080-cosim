#!/usr/bin/python3
"""Compare D27's photographed top-edge distance with its routed row."""

import json
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "ref/photos/juku-pcb-2/d27-top-edge-placement.json"
LOCAL_FITS = ROOT / "docs/photo-registration/local-packages/report.json"
BOARD = ROOT / "kicad/juku.kicad_pcb"
OUTPUT = ROOT / "docs/photo-registration/d27-top-edge-placement.json"


def main() -> None:
    evidence = json.loads(EVIDENCE.read_text())
    fits = json.loads(LOCAL_FITS.read_text())["fits"]
    matches = [f for f in fits if f["refdes"] == "D27" and f["side"] == "component"]
    if len(matches) != 1 or matches[0]["image"] != evidence["image"]:
        raise SystemExit("D27 component local fit missing or source changed")
    projected = matches[0]["projected_pins"]
    for pin, key in (("1", "physical_pin1_upper_row_px"),
                     ("40", "physical_pin40_lower_row_px")):
        if max(abs(projected[pin][i] - evidence[key][i]) for i in (0, 1)) > 2.0:
            raise SystemExit(f"D27.{pin} observation differs from local fit")
    x_top, y_top = evidence["top_board_edge_at_same_x_px"]
    x1, y1 = evidence["physical_pin1_upper_row_px"]
    _, y40 = evidence["physical_pin40_lower_row_px"]
    if abs(x_top - x1) > 1 or y_top >= y1 or y40 <= y1:
        raise SystemExit("invalid top-edge or row geometry")
    px_per_mm = (y40 - y1) / evidence["row_spacing_mm"]
    photo_upper_y_mm = (y1 - y_top) / px_per_mm
    photo_lower_y_mm = (y40 - y_top) / px_per_mm
    board = pcbnew.LoadBoard(str(BOARD))
    footprint = next(f for f in board.GetFootprints() if f.GetReference() == "D27")
    ys = [p.GetPosition().y / 1e6 for p in footprint.Pads()]
    routed_upper_y_mm = min(ys)
    routed_lower_y_mm = max(ys)
    if abs(photo_upper_y_mm - routed_upper_y_mm) > 3:
        raise SystemExit("D27 vertical residual exceeds 3 mm; review top-edge observation")
    solder = evidence["independent_solder_face"]
    solder_matches = [f for f in fits if f["refdes"] == "D27" and f["side"] == "solder"]
    if len(solder_matches) != 1 or solder_matches[0]["image"] != solder["image"]:
        raise SystemExit("D27 solder local fit missing or source changed")
    solder_projected = solder_matches[0]["projected_pins"]
    for pin, key in (("1", "physical_pin1_upper_row_px"),
                     ("40", "physical_pin40_lower_row_px")):
        if max(abs(solder_projected[pin][i] - solder[key][i]) for i in (0, 1)) > 2.0:
            raise SystemExit(f"D27 solder .{pin} observation differs from local fit")
    sx, sy = solder["top_board_edge_at_same_x_px"]
    s1x, s1y = solder["physical_pin1_upper_row_px"]
    _, s40y = solder["physical_pin40_lower_row_px"]
    if abs(sx - s1x) > 1 or sy >= s1y or s40y <= s1y:
        raise SystemExit("invalid solder top-edge or row geometry")
    solder_px_per_mm = (s40y - s1y) / evidence["row_spacing_mm"]
    solder_upper_y_mm = (s1y - sy) / solder_px_per_mm
    if abs(solder_upper_y_mm - routed_upper_y_mm) > 3:
        raise SystemExit("D27 solder vertical residual exceeds 3 mm; review observation")
    report = {
        "schema_version": 1,
        "evidence": str(EVIDENCE.relative_to(ROOT)),
        "board": str(BOARD.relative_to(ROOT)),
        "photo_px_per_mm": round(px_per_mm, 3),
        "photo_upper_row_y_mm": round(photo_upper_y_mm, 3),
        "photo_lower_row_y_mm": round(photo_lower_y_mm, 3),
        "routed_upper_row_y_mm": round(routed_upper_y_mm, 3),
        "routed_lower_row_y_mm": round(routed_lower_y_mm, 3),
        "upper_row_photo_minus_routed_y_mm": round(photo_upper_y_mm - routed_upper_y_mm, 3),
        "solder_photo_px_per_mm": round(solder_px_per_mm, 3),
        "solder_photo_upper_row_y_mm": round(solder_upper_y_mm, 3),
        "solder_upper_row_photo_minus_routed_y_mm": round(solder_upper_y_mm - routed_upper_y_mm, 3),
        "cross_face_upper_row_difference_mm": round(solder_upper_y_mm - photo_upper_y_mm, 3),
        "status": "both faces show no gross vertical placement conflict; physical pin-net mapping held",
    }
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(f"D27 top-edge placement check: photo {photo_upper_y_mm:.3f} mm vs "
          f"routed {routed_upper_y_mm:.3f} mm upper row")


if __name__ == "__main__":
    main()
