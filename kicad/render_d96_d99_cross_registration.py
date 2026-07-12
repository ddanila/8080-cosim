#!/usr/bin/env python3
"""Project the validated D96 package into the overlapping D99 owner photo."""
from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "ref/photos/juku-pcb-2/PXL_20260710_200402344.jpg"
TARGET = "ref/photos/juku-pcb-2/PXL_20260710_200418174.jpg"
OUTPUT = ROOT / "docs/photo-registration/d96-d99-cross-registration.jpg"
SOLDER = "ref/photos/juku-pcb-2/PXL_20260710_200522685.jpg"


def project(matrix: np.ndarray, point: tuple[float, float]) -> tuple[float, float]:
    value = matrix @ np.array([point[0], point[1], 1.0])
    return float(value[0] / value[2]), float(value[1] / value[2])


def main() -> None:
    panorama = json.loads((ROOT / "docs/photo-registration/panorama-registration.json").read_text())
    images = panorama["groups"]["component_grid"]["images"]
    source_h = np.array(images[SOURCE]["original_to_panorama_homography"]).reshape(3, 3)
    target_h = np.array(images[TARGET]["original_to_panorama_homography"]).reshape(3, 3)
    source_to_target = np.linalg.inv(target_h) @ source_h

    report = json.loads((ROOT / "docs/photo-registration/local-packages/report.json").read_text())
    fit = next(item for item in report["fits"]
               if item["refdes"] == "D96" and item["side"] == "component")
    pins = {pin: project(source_to_target, tuple(point))
            for pin, point in fit["projected_pins"].items()}

    # Stable regression anchors from the composed registration. The overlay is
    # the human-review artifact: all contacts must sit on the same physical
    # КМ555ТМ2 leads, not merely on two convenient nearby traces.
    anchors = {"1": (3095.5, 535.0), "7": (3088.7, 853.2),
               "8": (3249.6, 852.4), "14": (3256.8, 534.1)}
    errors = {pin: float(np.hypot(pins[pin][0] - expected[0],
                                  pins[pin][1] - expected[1]))
              for pin, expected in anchors.items()}
    if max(errors.values()) > 0.15:
        raise SystemExit(f"D96 cross-photo registration drift: {errors}")

    image = Image.open(ROOT / TARGET).convert("RGB")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    for pin, (x, y) in pins.items():
        radius = 17
        draw.ellipse((x-radius, y-radius, x+radius, y+radius), outline="cyan", width=7)
        draw.text((x+20, y-10), f"D96.{pin}", fill="yellow", stroke_width=2,
                  stroke_fill="black", font=font)

    with (ROOT / "ref/photos/juku-pcb-2/endpoints.csv").open(newline="") as stream:
        endpoints = list(csv.DictReader(stream))
    for pin, colour in (("2", "magenta"), ("3", "lime")):
        row = next(item for item in endpoints
                   if item["endpoint_id"] == f"seed-component-D99-{pin}")
        x, y = float(row["x_px"]), float(row["y_px"])
        draw.ellipse((x-20, y-20, x+20, y+20), outline=colour, width=8)
        draw.text((x+23, y-10), f"D99.{pin}", fill=colour, stroke_width=2,
                  stroke_fill="black", font=font)

    component_landings = {"D96.8 landing": (3292.0, 951.0),
                          "D99.2 landing": (3162.0, 951.0),
                          "D99.3 GND path": (3106.0, 951.0)}
    landing_colours = {"D96.8 landing": "cyan", "D99.2 landing": "magenta",
                       "D99.3 GND path": "lime"}
    for label, (x, y) in component_landings.items():
        colour = landing_colours[label]
        draw.ellipse((x-16, y-16, x+16, y+16), outline=colour, width=7)
        draw.text((x+19, y-10), label, fill=colour, stroke_width=2,
                  stroke_fill="black", font=font)

    component_crop = image.crop((2800, 400, 3450, 1150))

    d99_component = next(item for item in report["fits"]
                         if item["refdes"] == "D99" and item["side"] == "component")
    d99_solder = next(item for item in report["fits"]
                      if item["refdes"] == "D99" and item["side"] == "solder")
    rows, values = [], []
    for pin in sorted(d99_component["projected_pins"], key=int):
        x, y = d99_component["projected_pins"][pin]
        u, v = d99_solder["projected_pins"][pin]
        rows.extend(([x, y, 1, 0, 0, 0], [0, 0, 0, x, y, 1]))
        values.extend((u, v))
    affine = np.linalg.lstsq(np.array(rows), np.array(values), rcond=None)[0]
    residuals = []
    for pin in d99_component["projected_pins"]:
        x, y = d99_component["projected_pins"][pin]
        observed = np.array(d99_solder["projected_pins"][pin])
        predicted = np.array([[x, y, 1, 0, 0, 0],
                              [0, 0, 0, x, y, 1]]) @ affine
        residuals.append(float(np.linalg.norm(predicted - observed)))
    if max(residuals) > 0.001:
        raise SystemExit(f"D99 cross-side affine drift: {max(residuals):.6f} px")

    # Manually reviewed centres of the three circular component endpoints. The
    # D99-local affine avoids the much looser board-wide cross-side transform.
    landings = component_landings
    solder_image = Image.open(ROOT / SOLDER).convert("RGB")
    solder_draw = ImageDraw.Draw(solder_image)
    colours = landing_colours
    for label, (x, y) in landings.items():
        u, v = np.array([[x, y, 1, 0, 0, 0],
                         [0, 0, 0, x, y, 1]]) @ affine
        colour = colours[label]
        solder_draw.ellipse((u-16, v-16, u+16, v+16), outline=colour, width=7)
        solder_draw.text((u+19, v-10), label, fill=colour, stroke_width=2,
                         stroke_fill="black", font=font)
    solder_crop = solder_image.crop((700, 850, 1250, 1150)).resize((650, 355))
    combined = Image.new("RGB", (650, 1105), "black")
    combined.paste(component_crop, (0, 0))
    combined.paste(solder_crop, (0, 750))
    combined.save(OUTPUT, quality=92)
    print(f"D96 cross-photo registration PASS: max anchor error {max(errors.values()):.3f} px")
    print(f"D99 local cross-side affine PASS: max residual {max(residuals):.6f} px")
    print(f"wrote {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
