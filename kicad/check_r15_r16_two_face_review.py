#!/usr/bin/python3
"""Guard the former R15/R16 photo fit, now identified as R10/R9."""

import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "ref/photos/juku-pcb-2/r15-r16-two-face-review.json"
FITS = ROOT / "docs/photo-registration/local-packages/report.json"


def main() -> None:
    review = json.loads(REVIEW.read_text())
    if not review["status"].startswith("RETRACTED R15/R16 attribution"):
        raise SystemExit("R9/R10 REVIEW: factory identity retraction missing")
    fits = {(f["refdes"], f["side"]): f for f in json.loads(FITS.read_text())["fits"]}
    source = []
    target = []
    for ref in ("D95", "D99", "D101", "D97", "D102"):
        c = fits[ref, "component"]
        s = fits[ref, "solder"]
        if c["image"] != review["component_image"] or s["image"] != review["solder_image"]:
            raise SystemExit(f"R15/R16 REVIEW: {ref} photo source changed")
        source.append([*np.mean(np.array(list(c["projected_pins"].values())), axis=0), 1])
        target.append(np.mean(np.array(list(s["projected_pins"].values())), axis=0))
    source = np.array(source)
    target = np.array(target)
    transform = np.linalg.lstsq(source, target, rcond=None)[0]
    recorded = review["cross_face_registration"]
    rms = np.sqrt(np.mean(np.sum((source @ transform - target) ** 2, axis=1)))
    if abs(rms - recorded["package_center_rms_px"]) > 0.05:
        raise SystemExit("R15/R16 REVIEW: registration residual drifted")
    for name, observed in review["component_joint_px_approx"].items():
        projected = np.array([*observed, 1]) @ transform
        if np.linalg.norm(projected - recorded[f"{name}_projected_px"]) > 0.2:
            raise SystemExit(f"R15/R16 REVIEW: {name} projection drifted")
    reverse = np.linalg.lstsq(np.column_stack((target, np.ones(len(target)))), source[:, :2], rcond=None)[0]
    east = review["east_annulus_front_projection"]
    projected_front = np.array([*review["common_conductor_east_annulus_solder_px_approx"], 1]) @ reverse
    if np.linalg.norm(projected_front - east["component_px_approx"]) > 0.2:
        raise SystemExit("R15/R16 REVIEW: east annulus front projection drifted")
    reverse_rms = np.sqrt(np.mean(np.sum((np.column_stack((target, np.ones(len(target))))
                                   @ reverse - source[:, :2]) ** 2, axis=1)))
    if abs(reverse_rms - east["package_center_rms_px"]) > 0.05:
        raise SystemExit("R15/R16 REVIEW: reverse registration residual drifted")
    joints = review["four_joint_candidate_match"]
    order = ("left_upper", "right_upper", "left_lower", "right_lower")
    local_source = np.array([[*review["component_joint_px_approx"][key], 1] for key in order])
    local_target = np.array([joints[f"{key}_solder_px_approx"] for key in order])
    local_fit = np.linalg.lstsq(local_source, local_target, rcond=None)[0]
    local_rms = np.sqrt(np.mean(np.sum((local_source @ local_fit - local_target) ** 2, axis=1)))
    if abs(local_rms - joints["local_affine_four_joint_rms_px"]) > 0.05:
        raise SystemExit("R15/R16 REVIEW: four-joint local fit drifted")
    print("R9/R10 REVIEW: left-pair solder search guarded; R15/R16 attribution retracted")


if __name__ == "__main__":
    main()
