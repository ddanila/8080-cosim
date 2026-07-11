#!/usr/bin/env python3
"""Snap uniquely matched solder candidates to nearby plated-hole centres."""
import csv, math
from pathlib import Path
import cv2

ROOT = Path(__file__).resolve().parents[1]
ENDPOINTS = ROOT / "ref/photos/juku-pcb-2/endpoints.csv"
FIELDS = ("endpoint_id", "image", "x_px", "y_px", "refdes", "pin", "candidate_net",
          "confidence", "review_state", "reviewer", "note")

rows = list(csv.DictReader(ENDPOINTS.open(newline=""))); images = {}; snapped = 0
for row in rows:
    if not row["endpoint_id"].startswith("seed-solder-") or row["review_state"] != "candidate": continue
    image = images.setdefault(row["image"], cv2.imread(str(ROOT / row["image"])))
    x, y = float(row["x_px"]), float(row["y_px"]); radius = 65
    x0, y0 = max(0, int(x-radius)), max(0, int(y-radius))
    x1, y1 = min(image.shape[1], int(x+radius)), min(image.shape[0], int(y+radius))
    gray = cv2.medianBlur(cv2.cvtColor(image[y0:y1, x0:x1], cv2.COLOR_BGR2GRAY), 5)
    circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, 1, 12, param1=80,
                               param2=18, minRadius=5, maxRadius=18)
    if circles is None: continue
    candidates = sorted((math.hypot(x0+c[0]-x, y0+c[1]-y), x0+c[0], y0+c[1])
                        for c in circles[0])
    nearest = candidates[0]; separation = candidates[1][0]-nearest[0] if len(candidates)>1 else 99
    if nearest[0] >= 30 or separation <= 10: continue
    old = f"({x:.3f},{y:.3f})"
    row["x_px"], row["y_px"] = f"{nearest[1]:.3f}", f"{nearest[2]:.3f}"
    row["confidence"] = "registration+unique-hole-snap"
    row["note"] += (f"; projected {old}, snapped {nearest[0]:.1f}px to unique circular-hole "
                    f"candidate (next separation {separation:.1f}px); copper path not reviewed")
    snapped += 1
with ENDPOINTS.open("w", newline="") as destination:
    writer = csv.DictWriter(destination, FIELDS); writer.writeheader(); writer.writerows(rows)
print(f"snapped {snapped} solder candidates to unique nearby hole centres")
