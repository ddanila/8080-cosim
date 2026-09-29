#!/usr/bin/python3
"""Guard the D35.13 cross-face search projection and its uncertainty witness."""

import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "ref/photos/juku-pcb-2/d35-pin13-photo-review.json"
FITS = ROOT / "docs/photo-registration/local-packages/report.json"


def main() -> None:
    review = json.loads(REVIEW.read_text())
    fits = {(f["refdes"], f["side"]): f for f in json.loads(FITS.read_text())["fits"]}
    component = fits["D57", "component"]
    solder = fits["D57", "solder"]
    evidence = review["solder_projection"]
    if component["image"] != review["overlap_component_image"] or solder["image"] != evidence["image"]:
        raise SystemExit("D35.13 REVIEW: D57 photo source changed")
    pins = ("1", "12", "24")
    source = np.array([[*component["projected_pins"][p], 1] for p in pins])
    target = np.array([solder["projected_pins"][p] for p in pins])
    transform = np.linalg.solve(source, target)
    projected = np.array([*review["d35_pin13_overlap_component_px_approx"], 1]) @ transform
    if np.linalg.norm(projected - evidence["projected_pin13_px_approx"]) > 0.5:
        raise SystemExit("D35.13 REVIEW: projected solder search point drifted")
    c55 = np.mean(np.array(list(fits["D55", "component"]["projected_pins"].values())), axis=0)
    s55 = np.mean(np.array(list(fits["D55", "solder"]["projected_pins"].values())), axis=0)
    error = np.linalg.norm(np.array([*c55, 1]) @ transform - s55)
    if abs(error - evidence["D55_package_center_heldout_error_px"]) > 0.1:
        raise SystemExit("D35.13 REVIEW: D55 held-out uncertainty changed")
    print("D35.13 REVIEW: solder search point guarded; copper continuity HOLD")


if __name__ == "__main__":
    main()
