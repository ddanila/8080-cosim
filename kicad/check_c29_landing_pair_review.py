#!/usr/bin/python3
"""Check C29 candidate geometry against current owner photo registrations."""

import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "ref/photos/juku-pcb-2/c29-landing-pair-review.json"
FITS = ROOT / "docs/photo-registration/local-packages/report.json"
FACTORY_MOD = ROOT / "ref/photos/dgsh5-109-009-sb/factory-modification-registration.json"


def main() -> None:
    review = json.loads(REVIEW.read_text())
    fits = {(f["refdes"], f["side"]): f for f in json.loads(FITS.read_text())["fits"]}
    source = []
    target = []
    for ref in ("D38", "D41", "D92", "D39"):
        component = fits[ref, "component"]
        solder = fits[ref, "solder"]
        if component["image"] != review["component_image"] or solder["image"] != review["solder_image"]:
            raise SystemExit(f"C29 REVIEW: {ref} photo source changed")
        source.append([*np.mean(np.array(list(component["projected_pins"].values())), axis=0), 1])
        target.append(np.mean(np.array(list(solder["projected_pins"].values())), axis=0))
    transform = np.linalg.lstsq(np.array(source), np.array(target), rcond=None)[0]
    evidence = review["projection"]
    for label, observed in (
        ("upper", review["component_candidate_px"]["upper_solder_filled_looking_site"]),
        ("middle", review["component_candidate_px"]["middle_solder_filled_looking_site"]),
        ("lower", review["component_candidate_px"]["lower_open_annulus"]),
        ("r35_lower_lead", evidence["r35_lower_lead_component_px_approx"]),
        ("r106_upper_lead", evidence["r106_upper_lead_component_px_approx"]),
    ):
        projected = np.array([*observed, 1]) @ transform
        if np.linalg.norm(projected - evidence[f"{label}_four_package_px"]) > 0.05:
            raise SystemExit(f"C29 REVIEW: {label} projection drifted")
    relative = evidence["middle_to_lower_relative_geometry"]
    predicted = np.array(evidence["lower_four_package_px"]) - np.array(evidence["middle_four_package_px"])
    visible = (np.array(evidence["nearby_solder_candidate_px_approx"]["lower_wide_rail_hole"])
               - np.array(evidence["nearby_solder_candidate_px_approx"]["middle_isolated_joint"]))
    if np.linalg.norm(predicted - relative["projected_solder_vector_px"]) > 0.05:
        raise SystemExit("C29 REVIEW: projected relative geometry drifted")
    if np.linalg.norm(visible - relative["visible_solder_vector_px_approx"]) > 0.05:
        raise SystemExit("C29 REVIEW: visible relative geometry drifted")
    if abs(np.linalg.norm(predicted - visible) - relative["vector_disagreement_px_approx"]) > 0.05:
        raise SystemExit("C29 REVIEW: vector agreement drifted")
    ground = review["wide_rail_chase"]["ground_anchor"]
    factory_ground = json.loads(FACTORY_MOD.read_text())["d56"]["trigger_ground_rail"]
    if factory_ground["source_net"] != ground["source_net"] or factory_ground["package_ground_pin"] != "8":
        raise SystemExit("C29 REVIEW: D56 ground anchor changed")
    matching = [item for item in factory_ground["solder_observations"]
                if item["image"] == review["solder_image"]]
    if len(matching) != 1 or np.linalg.norm(np.array(matching[0]["d56_8_px"])
                                            - np.array(ground["pin_solder_px"])) > 0.05:
        raise SystemExit("C29 REVIEW: D56.8 solder anchor changed")
    print("C29 REVIEW: upper post-R35 and middle GND routes supported; population HOLD")


if __name__ == "__main__":
    main()
