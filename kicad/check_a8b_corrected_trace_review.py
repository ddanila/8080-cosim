#!/usr/bin/python3
"""Guard corrected D38 projection of the former A8B candidate."""

import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "ref/photos/juku-pcb-2/a8b-corrected-trace-review.json"
FITS = ROOT / "docs/photo-registration/local-packages/report.json"


def main() -> None:
    evidence = json.loads(EVIDENCE.read_text())
    fits = {(f["refdes"], f["side"]): f for f in json.loads(FITS.read_text())["fits"]}
    component = fits["D38", "component"]
    solder = fits["D38", "solder"]
    if component["image"] != evidence["component_image"] or solder["image"] != evidence["solder_image"]:
        raise SystemExit("A8B REVIEW: D38 photo source changed")
    source = np.array([[*component["projected_pins"][pin], 1] for pin in ("1", "7", "14")])
    target = np.array([solder["projected_pins"][pin] for pin in ("1", "7", "14")])
    transform = np.linalg.solve(source, target)
    observation = evidence["cross_face_projection"]
    projected = np.array([*evidence["component_candidate_white_joint_px"], 1]) @ transform
    pin8 = np.array(solder["projected_pins"]["8"])
    if np.linalg.norm(projected - observation["projected_candidate_solder_px"]) > 0.05:
        raise SystemExit("A8B REVIEW: candidate projection drifted")
    if np.linalg.norm(pin8 - observation["corrected_d38_pin8_solder_px"]) > 0.05:
        raise SystemExit("A8B REVIEW: D38.8 moved")
    if abs(np.linalg.norm(projected - pin8) - observation["candidate_to_pin8_solder_distance_px"]) > 0.05:
        raise SystemExit("A8B REVIEW: D38.8 separation drifted")
    wider = evidence["independent_cross_package_check"]
    package_source = []
    package_target = []
    for ref in wider["package_centers"]:
        c = fits[ref, "component"]
        s = fits[ref, "solder"]
        if c["image"] != evidence["component_image"] or s["image"] != evidence["solder_image"]:
            raise SystemExit(f"A8B REVIEW: {ref} photo source changed")
        center_c = np.mean(np.array(list(c["projected_pins"].values())), axis=0)
        center_s = np.mean(np.array(list(s["projected_pins"].values())), axis=0)
        package_source.append([*center_c, 1])
        package_target.append(center_s)
    package_source = np.array(package_source)
    package_target = np.array(package_target)
    broad_transform = np.linalg.lstsq(package_source, package_target, rcond=None)[0]
    broad_projected = np.array([*evidence["component_candidate_white_joint_px"], 1]) @ broad_transform
    rms = np.sqrt(np.mean(np.sum((package_source @ broad_transform - package_target) ** 2, axis=1)))
    if np.linalg.norm(broad_projected - wider["projected_candidate_solder_px"]) > 0.05:
        raise SystemExit("A8B REVIEW: cross-package projection drifted")
    if abs(rms - wider["anchor_rms_px"]) > 0.05:
        raise SystemExit("A8B REVIEW: cross-package residual drifted")
    if abs(np.linalg.norm(broad_projected - projected) - wider["difference_from_d38_local_projection_px"]) > 0.05:
        raise SystemExit("A8B REVIEW: cross-package disagreement drifted")
    print("A8B REVIEW: HOLD — extrapolated candidate has no established D38.8 path")


if __name__ == "__main__":
    main()
