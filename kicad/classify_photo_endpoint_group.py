#!/usr/bin/env python3
"""Apply an explicit human review decision to seeded photo endpoints.

This does not infer connectivity.  It only records a supplied review state and
side-specific rationale for one reference (optionally a pin subset), preserving
the measured image coordinates and confidence metadata.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENDPOINTS = ROOT / "ref/photos/juku-pcb-2/endpoints.csv"
FIELDS = ("endpoint_id", "image", "x_px", "y_px", "refdes", "pin",
          "candidate_net", "confidence", "review_state", "reviewer", "note")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("refdes")
    parser.add_argument("state", choices=("candidate", "accepted", "rejected", "measurement"))
    parser.add_argument("--pins", help="comma-separated pin numbers; default: every seeded pin for refdes")
    parser.add_argument("--component-note", required=True)
    parser.add_argument("--solder-note", required=True)
    parser.add_argument("--reviewer", default="codex-photo-review")
    args = parser.parse_args()
    pins = set(args.pins.split(",")) if args.pins else None

    with ENDPOINTS.open(newline="") as source:
        rows = list(csv.DictReader(source))
    changed = 0
    for row in rows:
        if not row["endpoint_id"].startswith("seed-") or row["refdes"] != args.refdes:
            continue
        if pins is not None and row["pin"] not in pins:
            continue
        side = "component" if row["endpoint_id"].startswith("seed-component-") else "solder"
        row["review_state"] = args.state
        row["reviewer"] = args.reviewer
        row["note"] = args.component_note if side == "component" else args.solder_note
        changed += 1
    expected = 2 * (len(pins) if pins is not None else len({r["pin"] for r in rows
                  if r["endpoint_id"].startswith("seed-") and r["refdes"] == args.refdes}))
    if changed != expected:
        raise SystemExit(f"expected {expected} matching observations, changed {changed}")
    with ENDPOINTS.open("w", newline="") as destination:
        writer = csv.DictWriter(destination, FIELDS)
        writer.writeheader(); writer.writerows(rows)
    print(f"classified {changed} {args.refdes} observations as {args.state}")


if __name__ == "__main__":
    main()
