#!/usr/bin/env python3
"""Apply validated local package coordinates to measurement observations.

Review state is deliberately preserved.  A local fit proves pad identity in a
photo, not where its copper terminates.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENDPOINTS = ROOT / "ref/photos/juku-pcb-2/endpoints.csv"
REPORT = ROOT / "docs/photo-registration/local-packages/report.json"
FIELDS = ("endpoint_id", "image", "x_px", "y_px", "refdes", "pin",
          "candidate_net", "confidence", "review_state", "reviewer", "note")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--side", choices=("component", "solder", "both"), default="both",
                        help="apply one validated side or require both (default: both)")
    parser.add_argument("refdes", nargs="+", help="references whose validated fits should be applied")
    args = parser.parse_args(); requested = set(args.refdes)
    sides = ("component", "solder") if args.side == "both" else (args.side,)
    report = json.loads(REPORT.read_text())
    fits = {(item["refdes"], item["side"]): item for item in report["fits"]
            if item["refdes"] in requested}
    missing = [ref for ref in requested
               if not all((ref, side) in fits for side in sides)]
    if missing:
        raise SystemExit(f"missing two-sided validated fits for {', '.join(sorted(missing))}")
    with ENDPOINTS.open(newline="") as source:
        rows = list(csv.DictReader(source))
    changed = 0
    for row in rows:
        if row["refdes"] not in requested or not row["endpoint_id"].startswith("seed-"):
            continue
        side = "component" if row["endpoint_id"].startswith("seed-component-") else "solder"
        if side not in sides:
            continue
        fit = fits[(row["refdes"], side)]
        if row["image"] != fit["image"]:
            if row["review_state"] != "candidate":
                raise SystemExit(f"{row['endpoint_id']}: fit image differs from reviewed observation image")
            # Newly seeded board-level candidates may select a different
            # overlapping tile. A validated package-local fit is the stronger
            # pad-identity record, so move only unreviewed candidates onto its
            # source image before applying the projected coordinate.
            row["image"] = fit["image"]
        point = fit["projected_pins"].get(row["pin"])
        if point is None:
            raise SystemExit(f"{row['endpoint_id']}: pin absent from local fit")
        row["x_px"], row["y_px"] = f"{point[0]:.3f}", f"{point[1]:.3f}"
        row["confidence"] = "local-package-fit"
        suffix = f"local {side} package fit establishes pad identity only; no electrical path accepted"
        if suffix not in row["note"]:
            row["note"] = (row["note"].rstrip("; ") + "; " + suffix).lstrip("; ")
        changed += 1
    expected = sum(len(item["projected_pins"]) for key, item in fits.items() if key[1] in sides)
    # Only unresolved pins have endpoint rows, so require two rows per distinct
    # unresolved pin rather than every projected package pad.
    unresolved = {(row["refdes"], row["pin"]) for row in rows if row["refdes"] in requested}
    expected_changed = len(sides) * len(unresolved)
    if changed != expected_changed:
        raise SystemExit(f"expected {expected_changed} unresolved observations, changed {changed}; fits expose {expected} pads")
    with ENDPOINTS.open("w", newline="") as destination:
        writer = csv.DictWriter(destination, FIELDS); writer.writeheader(); writer.writerows(rows)
    print(f"applied {args.side} local fits to {changed} measurement observations")


if __name__ == "__main__":
    main()
