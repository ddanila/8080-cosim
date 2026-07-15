#!/usr/bin/env python3
"""Render the proved D94.6 front-copper handoff and cross-side uncertainty."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
COMPONENT = "ref/photos/juku-pcb-2/PXL_20260710_202708344.jpg"
SOLDER = "ref/photos/juku-pcb-2/PXL_20260710_200506061.jpg"
OUTPUT = ROOT / "docs/photo-registration/d94-d5-layer-handoff.jpg"
D94_PIN6 = np.array([2477.0, 1835.143])
HANDOFF = np.array([2266.0, 1828.0])


def cross_side_affine(report: dict, refdes: str) -> np.ndarray:
    component_side = "component-alt" if refdes == "D94" else "component"
    component = next(item for item in report["fits"]
                     if item["refdes"] == refdes and item["side"] == component_side)
    solder = next(item for item in report["fits"]
                  if item["refdes"] == refdes and item["side"] == "solder")
    rows, values = [], []
    for pin in sorted(component["projected_pins"], key=int):
        x, y = component["projected_pins"][pin]
        u, v = solder["projected_pins"][pin]
        rows.extend(([x, y, 1, 0, 0, 0], [0, 0, 0, x, y, 1]))
        values.extend((u, v))
    return np.linalg.lstsq(np.array(rows), np.array(values), rcond=None)[0]


def project(affine: np.ndarray, point: np.ndarray) -> np.ndarray:
    x, y = point
    return np.array([[x, y, 1, 0, 0, 0],
                     [0, 0, 0, x, y, 1]]) @ affine


def main() -> None:
    report = json.loads(
        (ROOT / "docs/photo-registration/local-packages/report.json").read_text()
    )
    d94_fit = next(item for item in report["fits"]
                   if item["refdes"] == "D94" and item["side"] == "component-alt")
    if np.linalg.norm(np.array(d94_fit["projected_pins"]["6"]) - D94_PIN6) > 0.001:
        raise SystemExit("D94.6 exposed-socket projection drifted")

    projections = {
        "D93-local projection": project(cross_side_affine(report, "D93"), HANDOFF),
        "D94-local projection": project(cross_side_affine(report, "D94"), HANDOFF),
    }
    disagreement = float(np.linalg.norm(
        projections["D93-local projection"] - projections["D94-local projection"]
    ))
    if not 53.5 <= disagreement <= 54.5:
        raise SystemExit(f"D94.6 cross-side uncertainty drifted: {disagreement:.3f} px")

    font = ImageFont.load_default()
    component = Image.open(ROOT / COMPONENT).convert("RGB")
    draw = ImageDraw.Draw(component)
    draw.line((tuple(D94_PIN6), tuple(HANDOFF)), fill="cyan", width=8)
    for label, point, colour in (
        ("D94.6", D94_PIN6, "cyan"),
        ("proved layer handoff", HANDOFF, "red"),
    ):
        x, y = point
        draw.ellipse((x-20, y-20, x+20, y+20), outline=colour, width=8)
        draw.text((x+24, y-12), label, fill=colour, stroke_width=2,
                  stroke_fill="black", font=font)
    component_crop = component.crop((2100, 1550, 2750, 2100)).resize((1300, 1100))

    solder = Image.open(ROOT / SOLDER).convert("RGB")
    draw = ImageDraw.Draw(solder)
    for (label, point), colour in zip(projections.items(), ("magenta", "lime")):
        x, y = point
        draw.ellipse((x-22, y-22, x+22, y+22), outline=colour, width=8)
        draw.text((x+27, y-12), label, fill=colour, stroke_width=2,
                  stroke_fill="black", font=font)
    draw.text((1650, 1550), f"projection spread {disagreement:.1f} px: no solder route promoted",
              fill="yellow", stroke_width=2, stroke_fill="black", font=font)
    solder_crop = solder.crop((1500, 1200, 2150, 1750)).resize((1300, 1100))

    result = Image.new("RGB", (1300, 2200), "black")
    result.paste(component_crop, (0, 0))
    result.paste(solder_crop, (0, 1100))
    result.save(OUTPUT, quality=92)
    print(
        f"D94 D5 layer handoff PASS: D94.6 reaches "
        f"({HANDOFF[0]:.0f},{HANDOFF[1]:.0f}) px; "
        f"cross-side projections disagree by {disagreement:.1f} px"
    )
    print(f"wrote {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
