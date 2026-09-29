#!/usr/bin/python3
"""Compare photographed D54-to-edge spacing with the routed board."""

import json
import math
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "ref/photos/juku-pcb-2/timer-bottom-edge-registration.json"
BOARD = ROOT / "kicad/juku.kicad_pcb"
OUTPUT = ROOT / "docs/photo-registration/timer-bottom-edge-placement.json"
LOCAL_FITS = ROOT / "docs/photo-registration/local-packages/report.json"


def main() -> None:
    evidence = json.loads(EVIDENCE.read_text())
    board = pcbnew.LoadBoard(str(BOARD))
    footprint = next(f for f in board.GetFootprints() if f.GetReference() == "D54")
    pin1 = footprint.FindPadByNumber("1")
    if pin1 is None:
        raise SystemExit("D54 pin 1 missing")
    pin_y_mm = pin1.GetPosition().y / 1e6
    pin_x_mm = pin1.GetPosition().x / 1e6
    bottom_y_mm = evidence["board_bottom_y_mm"]
    model_distance_mm = bottom_y_mm - pin_y_mm
    local_fits = json.loads(LOCAL_FITS.read_text())["fits"]
    results = []
    for item in evidence["observations"]:
        matching_fits = [f for f in local_fits if f["refdes"] == "D54" and f["side"] == item["side"]]
        if len(matching_fits) != 1 or matching_fits[0]["image"] != item["image"]:
            raise SystemExit(f"{item['side']}: D54 local fit missing or source image changed")
        for pin, key in (("1", "pin1_image_px"), ("24", "opposite_row_pin24_image_px")):
            projected = matching_fits[0]["projected_pins"][pin]
            observed = item[key]
            if max(abs(projected[i] - observed[i]) for i in (0, 1)) > 2.0:
                raise SystemExit(f"{item['side']}: D54.{pin} disagrees with local fit")
        x, pin_y = item["pin1_image_px"]
        opposite_x, opposite_y = item["opposite_row_pin24_image_px"]
        edge_x, edge_y = item["bottom_edge_image_px"]
        if abs(x - opposite_x) > 1 or abs(x - edge_x) > 1:
            raise SystemExit(f"{item['side']}: observations are not at the same x")
        row_px = abs(pin_y - opposite_y)
        if row_px < 100 or edge_y <= pin_y:
            raise SystemExit(f"{item['side']}: invalid row or edge geometry")
        distance_mm = (edge_y - pin_y) * evidence["row_spacing_mm"] / row_px
        results.append({
            "side": item["side"],
            "image": item["image"],
            "row_spacing_px": row_px,
            "edge_distance_px": edge_y - pin_y,
            "photo_distance_mm": round(distance_mm, 3),
            "photo_pin_y_mm": round(bottom_y_mm - distance_mm, 3),
            "routed_pin_y_mm": round(pin_y_mm, 3),
            "photo_minus_routed_pin_y_mm": round(bottom_y_mm - distance_mm - pin_y_mm, 3),
        })
    spread = abs(results[0]["photo_distance_mm"] - results[1]["photo_distance_mm"])
    if spread > 2.0:
        raise SystemExit(f"photo faces disagree by {spread:.3f} mm")
    conflict = min(abs(r["photo_distance_mm"] - model_distance_mm) for r in results)
    if conflict < 10.0:
        raise SystemExit("expected >10 mm timer placement conflict is no longer present; review evidence")
    ppi = next(f for f in board.GetFootprints() if f.GetReference() == "D26")
    ppi_lower_row_mm = max(p.GetPosition().y / 1e6 for p in ppi.Pads())
    ppi_results = []
    for item in evidence["adjacent_ppi_observations"]:
        matching_fits = [f for f in local_fits if f["refdes"] == "D26" and f["side"] == item["side"]]
        if len(matching_fits) != 1 or matching_fits[0]["image"] != item["image"]:
            raise SystemExit(f"D26 {item['side']}: local fit missing or source image changed")
        for pin, key in (("40", "lower_row_pin40_image_px"), ("1", "opposite_row_pin1_image_px")):
            projected = matching_fits[0]["projected_pins"][pin]
            observed = item[key]
            if max(abs(projected[i] - observed[i]) for i in (0, 1)) > 2.0:
                raise SystemExit(f"D26 {item['side']}: physical pin {pin} disagrees with local fit")
        pin_x, lower_y = item["lower_row_pin40_image_px"]
        opposite_x, upper_y = item["opposite_row_pin1_image_px"]
        edge_x, edge_y = item["bottom_edge_image_px"]
        if max(abs(pin_x - opposite_x), abs(pin_x - edge_x)) > 1:
            raise SystemExit(f"D26 {item['side']}: observations are not at the same x")
        distance_mm = (edge_y - lower_y) * evidence["row_spacing_mm"] / abs(lower_y - upper_y)
        photo_y_mm = bottom_y_mm - distance_mm
        ppi_results.append({
            "side": item["side"],
            "photo_distance_mm": round(distance_mm, 3),
            "photo_lower_row_y_mm": round(photo_y_mm, 3),
            "routed_lower_row_y_mm": round(ppi_lower_row_mm, 3),
            "photo_minus_routed_y_mm": round(photo_y_mm - ppi_lower_row_mm, 3),
        })
    if any(abs(r["photo_lower_row_y_mm"] - d54["photo_pin_y_mm"]) > 1.0
           for r, d54 in zip(ppi_results, results)):
        raise SystemExit("D26 and D54 lower photo rows no longer agree")
    timer_column = []
    per_face = {}
    for side in ("component", "solder"):
        anchor_y_mm = next(r["photo_pin_y_mm"] for r in results if r["side"] == side)
        previous_y_mm = anchor_y_mm
        previous_pin_y_px = None
        previous_scale = None
        per_face[side] = {}
        for ref in ("D54", "D55", "D57"):
            matches = [f for f in local_fits if f["refdes"] == ref and f["side"] == side]
            if len(matches) != 1:
                raise SystemExit(f"{ref} {side}: local package fit missing")
            fit = matches[0]
            pin_y_px = fit["projected_pins"]["1"][1]
            opposite_y_px = fit["projected_pins"]["24"][1]
            scale = abs(pin_y_px - opposite_y_px) / evidence["row_spacing_mm"]
            if previous_pin_y_px is not None:
                previous_y_mm -= (previous_pin_y_px - pin_y_px) / ((previous_scale + scale) / 2)
            per_face[side][ref] = round(previous_y_mm, 3)
            previous_pin_y_px = pin_y_px
            previous_scale = scale
    for ref in ("D54", "D55", "D57"):
        face_y = {side: per_face[side][ref] for side in per_face}
        disagreement = abs(face_y["component"] - face_y["solder"])
        if disagreement > 2.0:
            raise SystemExit(f"{ref}: component/solder relative y estimates disagree")
        timer_footprint = next(f for f in board.GetFootprints() if f.GetReference() == ref)
        routed_y = timer_footprint.FindPadByNumber("1").GetPosition().y / 1e6
        timer_column.append({
            "refdes": ref,
            "photo_pin1_y_mm_by_side": face_y,
            "side_disagreement_mm": round(disagreement, 3),
            "routed_pin1_y_mm": round(routed_y, 3),
            "photo_mean_minus_routed_y_mm": round(sum(face_y.values()) / 2 - routed_y, 3),
        })
    timer_horizontal = []
    for observation in evidence["timer_right_edge_observations"]:
        ref = observation["refdes"]
        face_x = {}
        for side, edge_key in (("component", "component_edge_at_pin12_px"),
                               ("solder", "solder_reflected_edge_at_pin12_px")):
            fit = next(f for f in local_fits if f["refdes"] == ref and f["side"] == side)
            pin1 = fit["projected_pins"]["1"]
            pin12 = fit["projected_pins"]["12"]
            edge_x, edge_y = observation[edge_key]
            if abs(edge_y - pin12[1]) > 5.0:
                raise SystemExit(f"{ref} {side}: edge row differs from pin-12 row")
            scale = abs(pin12[0] - pin1[0]) / (11 * 2.54)
            gap_px = edge_x - pin12[0] if side == "component" else pin12[0] - edge_x
            face_x[side] = round(310.0 - gap_px / scale, 3)
        disagreement = abs(face_x["component"] - face_x["solder"])
        if disagreement > 3.0:
            raise SystemExit(f"{ref}: component/solder edge x estimates disagree")
        footprint_ref = next(f for f in board.GetFootprints() if f.GetReference() == ref)
        routed_x = footprint_ref.FindPadByNumber("12").GetPosition().x / 1e6
        timer_horizontal.append({
            "refdes": ref,
            "photo_pin12_x_mm_by_side": face_x,
            "side_disagreement_mm": round(disagreement, 3),
            "routed_pin12_x_mm": round(routed_x, 3),
            "photo_mean_minus_routed_x_mm": round(sum(face_x.values()) / 2 - routed_x, 3),
        })
    edge_holes = [
        (shape.GetPosition().x / 1e6, shape.GetPosition().y / 1e6)
        for shape in board.GetDrawings()
        if shape.GetLayer() == pcbnew.Edge_Cuts
        and shape.GetShape() == pcbnew.SHAPE_T_CIRCLE
    ]
    holes = []
    aperture_widths = [h["component_aperture_diameter_px_approx"]
                       for h in evidence["lower_mounting_holes"]]
    aperture_ratio = max(aperture_widths) / min(aperture_widths)
    if aperture_ratio > 1.15:
        raise SystemExit("photographed lower-hole aperture sizes differ; review observations")
    for hole in evidence["lower_mounting_holes"]:
        target = hole.get("routed_center_mm", hole.get("edge_derived_center_mm_approx"))
        nearest = min(math.dist(target, center) for center in edge_holes)
        observed_status = "present" if nearest <= 2.0 else "absent"
        expected_status = "present" if "routed_center_mm" in hole else hole["routed_status"]
        if observed_status != expected_status:
            raise SystemExit(f"{hole['identity']}: routed hole status changed; review evidence")
        holes.append({
            "identity": hole["identity"],
            "photo_candidate_center_mm": target,
            "nearest_routed_hole_mm": round(nearest, 3),
            "routed_status": observed_status,
            "component_aperture_diameter_px_approx": hole["component_aperture_diameter_px_approx"],
        })
    component = next(item for item in evidence["observations"] if item["side"] == "component")
    component_fit = next(f for f in local_fits if f["refdes"] == "D54" and f["side"] == "component")
    known_hole = next(h for h in evidence["lower_mounting_holes"] if "routed_center_mm" in h)
    hole_x_px, hole_y_px = known_hole["component_image_px"]
    hole_x_mm, hole_y_mm = known_hole["routed_center_mm"]
    photo_pin_x_px, photo_pin_y_px = component["pin1_image_px"]
    right_edge_x_px, right_edge_y_px = component["right_edge_at_pin1_image_px"]
    if abs(right_edge_y_px - photo_pin_y_px) > 1:
        raise SystemExit("right edge and D54 pin 1 are not on the same photo row")
    right_edge_x_mm = 310.0
    pin12_x_px = component_fit["projected_pins"]["12"][0]
    x_hole_edge_mm = hole_x_mm + (photo_pin_x_px - hole_x_px) * (
        right_edge_x_mm - hole_x_mm) / (right_edge_x_px - hole_x_px)
    x_pitch_edge_mm = right_edge_x_mm - (right_edge_x_px - photo_pin_x_px) * (
        11 * 2.54) / (pin12_x_px - photo_pin_x_px)
    y_hole_row_mm = hole_y_mm + (photo_pin_y_px - hole_y_px) * (
        evidence["row_spacing_mm"] / abs(photo_pin_y_px - component["opposite_row_pin24_image_px"][1]))
    y_bottom_row_mm = next(r["photo_pin_y_mm"] for r in results if r["side"] == "component")
    candidate = {
        "methods": {
            "x_known_hole_to_right_edge_mm": round(x_hole_edge_mm, 3),
            "x_pin_pitch_to_right_edge_mm": round(x_pitch_edge_mm, 3),
            "y_known_hole_and_row_pitch_mm": round(y_hole_row_mm, 3),
            "y_bottom_edge_and_row_pitch_mm": round(y_bottom_row_mm, 3),
        },
        "method_spread_mm": {
            "x": round(abs(x_hole_edge_mm - x_pitch_edge_mm), 3),
            "y": round(abs(y_hole_row_mm - y_bottom_row_mm), 3),
        },
        "routed_pin1_mm": [round(pin_x_mm, 3), round(pin_y_mm, 3)],
        "status": "candidate range only; perspective and landmark uncertainty remain",
    }
    report = {
        "schema_version": 1,
        "evidence": str(EVIDENCE.relative_to(ROOT)),
        "board": str(BOARD.relative_to(ROOT)),
        "status": "PLACEMENT HOLD",
        "routed_pin1_to_bottom_edge_mm": round(model_distance_mm, 3),
        "face_disagreement_mm": round(spread, 3),
        "observations": results,
        "adjacent_d26_lower_row": ppi_results,
        "timer_column_relative_placement": timer_column,
        "timer_column_right_edge_placement": timer_horizontal,
        "mounting_holes": holes,
        "lower_hole_aperture_width_ratio": round(aperture_ratio, 3),
        "lower_hole_drill_inference": "similar photo apertures suggest the existing nominal 3.5 mm drill; unmeasured",
        "d54_pin1_mechanical_candidate": candidate,
        "limitation": "Local row-scale approximation; final footprint coordinates need a full mechanical fit.",
    }
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(f"timer bottom-edge placement HOLD: {model_distance_mm:.3f} mm routed vs "
          + "/".join(f"{r['photo_distance_mm']:.3f}" for r in results) + " mm photographed")


if __name__ == "__main__":
    main()
