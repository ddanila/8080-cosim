#!/usr/bin/python3
"""Guard the withdrawn A9B candidate against D38 and D92 photo fits."""

import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "ref/photos/juku-pcb-2/a9b-corrected-trace-review.json"
A13_REVIEW = ROOT / "ref/photos/juku-pcb-2/a13a-c95-d50-candidate-review.json"
FITS = ROOT / "docs/photo-registration/local-packages/report.json"


def main() -> None:
    evidence = json.loads(EVIDENCE.read_text())
    fits = {(f["refdes"], f["side"]): f for f in json.loads(FITS.read_text())["fits"]}
    component = fits["D38", "component"]
    solder = fits["D38", "solder"]
    if component["image"] != evidence["component_image"] or solder["image"] != evidence["solder_image"]:
        raise SystemExit("A9B REVIEW: D38 photo source changed")
    source = np.array([[*component["projected_pins"][pin], 1] for pin in ("1", "7", "14")])
    target = np.array([solder["projected_pins"][pin] for pin in ("1", "7", "14")])
    transform = np.linalg.solve(source, target)
    observations = evidence["cross_face_projection"]
    for source_key, target_key in (
        ("component_candidate_annulus_px", "projected_candidate_annulus_solder_px"),
        ("component_candidate_joint_px", "projected_candidate_joint_solder_px"),
    ):
        projected = np.array([*evidence[source_key], 1]) @ transform
        recorded = np.array(observations[target_key])
        if np.linalg.norm(projected - recorded) > 0.05:
            raise SystemExit(f"A9B REVIEW: {target_key} drifted")
    pin12 = np.array(solder["projected_pins"]["12"])
    if np.linalg.norm(pin12 - observations["corrected_d38_pin12_solder_px"]) > 0.05:
        raise SystemExit("A9B REVIEW: corrected D38.12 moved")
    wider = evidence["independent_cross_package_check"]
    source_centers = []
    target_centers = []
    for ref in wider["package_centers"]:
        c = fits[ref, "component"]
        s = fits[ref, "solder"]
        source_centers.append([*np.mean(np.array(list(c["projected_pins"].values())), axis=0), 1])
        target_centers.append(np.mean(np.array(list(s["projected_pins"].values())), axis=0))
    broad_transform = np.linalg.lstsq(np.array(source_centers), np.array(target_centers), rcond=None)[0]
    for source_key, target_key in (
        ("component_candidate_annulus_px", "projected_candidate_annulus_solder_px"),
        ("component_candidate_joint_px", "projected_candidate_joint_solder_px"),
    ):
        projected = np.array([*evidence[source_key], 1]) @ broad_transform
        if np.linalg.norm(projected - wider[target_key]) > 0.05:
            raise SystemExit(f"A9B REVIEW: cross-package {target_key} drifted")
    distance = np.linalg.norm(np.array(wider["projected_candidate_annulus_solder_px"])
                              - np.array(observations["nearest_visible_open_annulus_solder_px_approx"]))
    if abs(distance - wider["open_annulus_distance_from_broad_projection_px_approx"]) > 0.5:
        raise SystemExit("A9B REVIEW: candidate annulus proximity drifted")
    roe = json.loads(A13_REVIEW.read_text())["d92_roe_trace_chase"]
    d92_front = fits["D92", "component"]["projected_pins"]
    d92_back = fits["D92", "solder"]["projected_pins"]
    d92_source = np.array([[*d92_front[pin], 1] for pin in ("1", "7", "8")])
    d92_target = np.array([d92_back[pin] for pin in ("1", "7", "8")])
    d92_transform = np.linalg.solve(d92_source, d92_target)
    d92_projected = np.array([*roe["component_annulus_px_approx"], 1]) @ d92_transform
    d92_recorded = np.array(roe["d92_local_projection_of_component_annulus_solder_px"])
    if np.linalg.norm(d92_projected - d92_recorded) > 0.15:
        raise SystemExit("A9B REVIEW: D92-local ROE annulus projection drifted")
    if np.linalg.norm(np.array(d92_back["1"]) - roe["registered_d92_1_solder_px"]) > 0.05:
        raise SystemExit("A9B REVIEW: registered D92.1 solder contact drifted")
    roe_distance = np.linalg.norm(d92_projected - roe["solder_open_annulus_px_approx"])
    if abs(roe_distance - roe["projection_to_open_annulus_distance_px_approx"]) > 0.2:
        raise SystemExit("A9B REVIEW: D92-local annulus proximity drifted")
    if "D92.1/ROE" not in evidence["decision"] or "D38.12" not in evidence["decision"]:
        raise SystemExit("A9B REVIEW: ROE retraction or SYNC hold was lost")
    print("A9B REVIEW: HOLD — former white-wire annulus favors A13B/D92.1/ROE; separate D38.12/SYNC spur has no proved wire")


if __name__ == "__main__":
    main()
