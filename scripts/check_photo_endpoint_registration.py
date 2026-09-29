#!/usr/bin/env python3
"""Reject endpoint seed coordinates that contradict promoted package anchors."""

import csv
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRATION = ROOT / "ref/photos/juku-pcb-2/local-package-registration.json"
ENDPOINTS = ROOT / "ref/photos/juku-pcb-2/endpoints.csv"
MAX_ANCHOR_ERROR_PX = 10.0
MAX_GRID_ERROR_PX = 3.0
MAX_CROSS_PACKAGE_COLLISION_PX = 10.0


def promoted_grid(ref: str, side: str, pin: int) -> tuple[float, float] | None:
    """Complete D40/D11/D13 package rows from promoted corner anchors."""
    if (ref, side) == ("D40", "component"):
        if 1 <= pin <= 8:
            return 2756 - (pin - 1) * 395 / 7, 1956
        if 9 <= pin <= 16:
            return 2361 + (pin - 9) * 395 / 7, 2126
    if (ref, side) == ("D11", "solder"):
        if 1 <= pin <= 14:
            return 2705, 1610 + (pin - 1) * 601 / 13
        if 15 <= pin <= 28:
            return 2425, 2211 - (pin - 15) * 601 / 13
    if (ref, side) == ("D13", "solder"):
        if 1 <= pin <= 7:
            return 2682 + (pin - 1) * 369 / 6, 825
        if 8 <= pin <= 14:
            return 3051 - (pin - 8) * 369 / 6, 1009
    return None


def main() -> int:
    packages = json.loads(REGISTRATION.read_text(encoding="utf-8"))["packages"]
    with ENDPOINTS.open(newline="", encoding="utf-8") as handle:
        endpoints = list(csv.DictReader(handle))
    by_key = {
        (row["refdes"], row["endpoint_id"].split("-")[1], row["pin"], row["image"]): row
        for row in endpoints
        if row["endpoint_id"].startswith(("seed-component-", "seed-solder-"))
    }
    checked = 0
    failures = []
    by_image = {}
    for package in packages:
        for anchor in package.get("anchors", []):
            by_image.setdefault(package["image"], []).append(
                (package["refdes"], anchor["pin"], anchor["image_px"])
            )
    for image, anchors in by_image.items():
        for index, (refdes, pin, point) in enumerate(anchors):
            for other_refdes, other_pin, other_point in anchors[index + 1:]:
                if refdes == other_refdes:
                    continue
                if math.dist(point, other_point) < MAX_CROSS_PACKAGE_COLLISION_PX:
                    failures.append(
                        f"{Path(image).name}: {refdes}.{pin} and "
                        f"{other_refdes}.{other_pin} share a contact location"
                    )
    for package in packages:
        side = package.get("side")
        if side not in {"component", "solder"}:
            continue
        for anchor in package.get("anchors", []):
            key = (package["refdes"], side, anchor["pin"], package["image"])
            row = by_key.get(key)
            if row is None:
                continue
            checked += 1
            error = math.hypot(
                float(row["x_px"]) - anchor["image_px"][0],
                float(row["y_px"]) - anchor["image_px"][1],
            )
            if error > MAX_ANCHOR_ERROR_PX:
                failures.append(f"{row['endpoint_id']}: {error:.1f} px")
    grid_checked = 0
    for row in endpoints:
        endpoint_id = row["endpoint_id"]
        if not endpoint_id.startswith(("seed-component-", "seed-solder-")):
            continue
        side = endpoint_id.split("-")[1]
        if not row["pin"].isdigit():
            continue
        expected = promoted_grid(row["refdes"], side, int(row["pin"]))
        if expected is None:
            continue
        grid_checked += 1
        error = math.hypot(float(row["x_px"]) - expected[0], float(row["y_px"]) - expected[1])
        if error > MAX_GRID_ERROR_PX:
            failures.append(f"{endpoint_id}: {error:.1f} px from promoted package row")
    print(f"Photo endpoint/package checks: {checked} anchors, {grid_checked} grid pins; mismatches: {len(failures)}")
    for failure in failures:
        print(failure)
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
