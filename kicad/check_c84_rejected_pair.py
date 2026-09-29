#!/usr/bin/python3
"""Guard why the former C84 two-hole candidate cannot be a bypass pair."""

import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "ref/photos/juku-pcb-2/c84-region-review.json"
FITS = ROOT / "docs/photo-registration/local-packages/report.json"
BOARD = ROOT / "kicad/juku.board.json"


def main() -> None:
    review = json.loads(REVIEW.read_text())
    fits = {(f["refdes"], f["side"]): f for f in json.loads(FITS.read_text())["fits"]}
    d54 = fits["D54", "component"]
    if d54["image"] != review["owner_component_july"]["image"]:
        raise SystemExit("C84 REVIEW: D54 component photo changed")
    candidate = review["rejected_candidate_pair"]
    other = review["other_rejected_pair"]
    if np.linalg.norm(np.array(d54["projected_pins"]["4"])
                      - np.array(other["d54_pin4_component_px"])) > 0.05:
        raise SystemExit("C84 REVIEW: D54.4 fit drifted")
    if np.linalg.norm(np.array(d54["projected_pins"]["10"])
                      - np.array(candidate["d54_pin10_component_px"])) > 0.05:
        raise SystemExit("C84 REVIEW: D54.10 fit drifted")
    if np.linalg.norm(np.array(candidate["visible_trace_contact_px_approx"])
                      - np.array(candidate["d54_pin10_component_px"])) > 20:
        raise SystemExit("C84 REVIEW: trace contact no longer near D54.10")
    board = json.loads(BOARD.read_text())
    d54_chip = next(chip for chip in board["chips"] if chip["ref"] == "D54")
    if d54_chip["pins"]["4"] != "D4" or d54_chip["pins"]["10"] != "OUT0":
        raise SystemExit("C84 REVIEW: D54 signal-pin identities changed")
    print("C84 REVIEW: both obvious pairs rejected by D54.4/D4 and D54.10/OUT0 traces")


if __name__ == "__main__":
    main()
