#!/usr/bin/python3
"""Seed two-sided candidate photo landings for every unresolved KiCad pad."""
from __future__ import annotations
import csv, json
from pathlib import Path
import numpy as np
import pcbnew

ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "kicad/juku.kicad_pcb"
UNRESOLVED = ROOT / "docs/main-board-unresolved-endpoints.csv"
ENDPOINTS = ROOT / "ref/photos/juku-pcb-2/endpoints.csv"
MANIFEST = ROOT / "ref/photos/juku-pcb-2/registration.json"
PANORAMA = ROOT / "docs/photo-registration/panorama-registration.json"
BOARD_REG = ROOT / "docs/photo-registration/board-registration.json"
FIELDS = ("endpoint_id", "image", "x_px", "y_px", "refdes", "pin", "candidate_net",
          "confidence", "review_state", "reviewer", "note")

def project(matrix, point):
    value = matrix @ np.array([point[0], point[1], 1.0])
    return value[:2] / value[2]

def best_source(group_id, panorama_point, panorama, manifest):
    candidates = []
    for rel, record in panorama["groups"][group_id]["images"].items():
        inverse = np.linalg.inv(np.array(record["original_to_panorama_homography"]).reshape(3, 3))
        source = project(inverse, panorama_point)
        width, height = manifest["images"][rel]["width"], manifest["images"][rel]["height"]
        if 0 <= source[0] < width and 0 <= source[1] < height:
            margin = min(source[0], width-source[0], source[1], height-source[1])
            candidates.append((margin, rel, source))
    if not candidates:
        raise RuntimeError(f"no source covers {group_id} point {panorama_point}")
    return max(candidates, key=lambda item: item[0])[1:]

def main():
    board = pcbnew.LoadBoard(str(BOARD)); manifest = json.loads(MANIFEST.read_text())
    panorama = json.loads(PANORAMA.read_text()); board_reg = json.loads(BOARD_REG.read_text())
    unresolved = list(csv.DictReader(UNRESOLVED.open(newline="")))
    existing = list(csv.DictReader(ENDPOINTS.open(newline=""))) if ENDPOINTS.exists() else []
    preserved = [row for row in existing if not row["endpoint_id"].startswith("seed-")
                 or row["review_state"] != "candidate"]
    preserved_ids = {row["endpoint_id"] for row in preserved}; rows = list(preserved)
    for endpoint in unresolved:
        footprint = board.FindFootprintByReference(endpoint["ref"])
        pad = footprint.FindPadByNumber(endpoint["pin"]) if footprint else None
        if pad is None: raise RuntimeError(f"missing PCB pad {endpoint['ref']}.{endpoint['pin']}")
        position = pad.GetPosition(); board_point = np.array([pcbnew.ToMM(position.x), pcbnew.ToMM(position.y)])
        for group_id, side in (("component_grid", "component"), ("solder_grid", "solder")):
            endpoint_id = f"seed-{side}-{endpoint['ref']}-{endpoint['pin']}"
            if endpoint_id in preserved_ids: continue
            h = np.array(board_reg["groups"][group_id]["board_to_panorama_homography"]).reshape(3, 3)
            rel, source = best_source(group_id, project(h, board_point), panorama, manifest)
            rows.append({"endpoint_id": endpoint_id,
                "image": rel, "x_px": f"{source[0]:.3f}", "y_px": f"{source[1]:.3f}",
                "refdes": endpoint["ref"], "pin": endpoint["pin"],
                "candidate_net": pad.GetNetname(), "confidence": "registration-only",
                "review_state": "candidate", "reviewer": "",
                "note": f"Generated pad landing from board ({board_point[0]:.3f},{board_point[1]:.3f}) mm; copper path not reviewed"})
    with ENDPOINTS.open("w", newline="") as destination:
        writer = csv.DictWriter(destination, FIELDS); writer.writeheader(); writer.writerows(rows)
    print(f"wrote {ENDPOINTS.relative_to(ROOT)}: {len(rows)} rows for {len(unresolved)} unresolved pads")

if __name__ == "__main__": main()
