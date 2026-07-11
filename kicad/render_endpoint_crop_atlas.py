#!/usr/bin/python3
"""Render labeled original-photo crops for the endpoint review queue."""
from __future__ import annotations
import csv, math
from collections import defaultdict
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ENDPOINTS = ROOT / "ref/photos/juku-pcb-2/endpoints.csv"
UNRESOLVED = ROOT / "docs/main-board-unresolved-endpoints.csv"
OUTPUT = ROOT / "docs/photo-registration/crops"
CROP_W, CROP_H, LABEL_H, COLUMNS = 360, 280, 28, 4

def main():
    priorities = {(row["ref"], row["pin"]): row["priority"]
                  for row in csv.DictReader(UNRESOLVED.open(newline=""))}
    groups = defaultdict(list)
    for row in csv.DictReader(ENDPOINTS.open(newline="")):
        if not row["endpoint_id"].startswith("seed-"): continue
        side = "component" if "-component-" in row["endpoint_id"] else "solder"
        priority = priorities.get((row["refdes"], row["pin"]), "accepted")
        groups[(priority, side, row["refdes"])].append(row)
    OUTPUT.mkdir(parents=True, exist_ok=True); generated = 0
    font = ImageFont.load_default()
    for (priority, side, refdes), rows in sorted(groups.items()):
        rows.sort(key=lambda row: int(row["pin"]) if row["pin"].isdigit() else row["pin"])
        height = math.ceil(len(rows) / COLUMNS) * (CROP_H + LABEL_H)
        atlas = Image.new("RGB", (COLUMNS * CROP_W, height), "white")
        for index, row in enumerate(rows):
            source = Image.open(ROOT / row["image"]).convert("RGB")
            x, y = float(row["x_px"]), float(row["y_px"])
            crop = source.crop((round(x-CROP_W/2), round(y-CROP_H/2),
                                round(x+CROP_W/2), round(y+CROP_H/2)))
            draw = ImageDraw.Draw(crop)
            draw.ellipse((CROP_W/2-8, CROP_H/2-8, CROP_W/2+8, CROP_H/2+8),
                         outline="#ff1744", width=3)
            column, grid_row = index % COLUMNS, index // COLUMNS
            ox, oy = column*CROP_W, grid_row*(CROP_H+LABEL_H)
            atlas.paste(crop, (ox, oy+LABEL_H))
            label = f"{priority} {refdes}.{row['pin']}  {Path(row['image']).name}  ({x:.1f},{y:.1f})"
            ImageDraw.Draw(atlas).text((ox+4, oy+7), label, fill="black", font=font)
        destination = OUTPUT / f"{priority}-{side}-{refdes}.jpg"
        atlas.save(destination, quality=94, subsampling=0); generated += 1
    print(f"wrote {generated} endpoint crop atlases under {OUTPUT.relative_to(ROOT)}")

if __name__ == "__main__": main()
