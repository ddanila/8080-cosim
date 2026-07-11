#!/usr/bin/env python3
"""Validate and render auditable package-local photo registration fits.

A fit identifies where package pads fall in one original photograph.  It does
not follow copper and must never be treated as electrical connectivity evidence.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import pcbnew
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "kicad/juku.kicad_pcb"
RECORDS = ROOT / "ref/photos/juku-pcb-2/local-package-registration.json"
OUTPUT = ROOT / "docs/photo-registration/local-packages"
REPORT = OUTPUT / "report.json"


def fit_similarity(points: list[tuple[complex, complex]], reflected: bool = False) -> tuple[complex, complex]:
    """Return image = offset + scale_rotation * package_local."""
    if len(points) < 2:
        raise ValueError("similarity fit needs at least two anchors")
    if reflected:
        points = [(z.conjugate(), w) for z, w in points]
    zbar = sum(z for z, _ in points) / len(points)
    wbar = sum(w for _, w in points) / len(points)
    denominator = sum(abs(z - zbar) ** 2 for z, _ in points)
    if denominator < 1e-9:
        raise ValueError("degenerate local anchors")
    factor = sum((z - zbar).conjugate() * (w - wbar) for z, w in points) / denominator
    return wbar - factor * zbar, factor


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-check-error-px", type=float, default=8.0)
    args = parser.parse_args()
    document = json.loads(RECORDS.read_text())
    if document.get("schema_version") != 1:
        raise SystemExit("unsupported local registration schema")
    board = pcbnew.LoadBoard(str(BOARD)); OUTPUT.mkdir(parents=True, exist_ok=True)
    results, errors = [], []
    for record in document["packages"]:
        refdes, side = record["refdes"], record["side"]
        footprint = board.FindFootprintByReference(refdes)
        if footprint is None:
            errors.append(f"{refdes}: footprint absent"); continue
        centre = footprint.GetPosition()
        local = {}
        for pad in footprint.Pads():
            position = pad.GetPosition()
            local[pad.GetNumber()] = complex(pcbnew.ToMM(position.x-centre.x),
                                             pcbnew.ToMM(position.y-centre.y))
        anchors = record.get("anchors", [])
        unknown = [item["pin"] for item in anchors if item["pin"] not in local]
        if unknown:
            errors.append(f"{refdes}/{side}: unknown anchor pins {unknown}"); continue
        fit = [(local[item["pin"]], complex(*map(float, item["image_px"])))
               for item in anchors if item["use"] == "fit"]
        model = record.get("model")
        if model not in ("similarity", "similarity_reflected"):
            errors.append(f"{refdes}/{side}: unsupported model {model}"); continue
        reflected = model == "similarity_reflected"
        try:
            offset, factor = fit_similarity(fit, reflected)
        except ValueError as exc:
            errors.append(f"{refdes}/{side}: {exc}"); continue
        checks = []
        for item in anchors:
            coordinate = local[item["pin"]].conjugate() if reflected else local[item["pin"]]
            predicted = offset + factor * coordinate
            observed = complex(*map(float, item["image_px"]))
            error = abs(predicted-observed)
            checks.append({"pin": item["pin"], "use": item["use"],
                           "error_px": round(error, 3)})
            if item["use"] == "check" and error > args.max_check_error_px:
                errors.append(f"{refdes}/{side} pin {item['pin']}: check error {error:.1f}px")
        image = Image.open(ROOT / record["image"]).convert("RGB")
        draw = ImageDraw.Draw(image); font = ImageFont.load_default()
        projected = {}
        for pin, point in local.items():
            coordinate = point.conjugate() if reflected else point
            value = offset + factor * coordinate; x, y = value.real, value.imag
            projected[pin] = [round(x, 3), round(y, 3)]
            colour = "#00e5ff" if any(a["pin"] == pin for a in anchors) else "#ff1744"
            draw.ellipse((x-9, y-9, x+9, y+9), outline=colour, width=3)
            draw.text((x+11, y-10), f"{refdes}.{pin}", fill=colour, font=font,
                      stroke_width=2, stroke_fill="black")
        destination = OUTPUT / f"{refdes}-{side}.jpg"
        image.save(destination, quality=94, subsampling=0)
        results.append({"refdes": refdes, "side": side, "image": record["image"],
                        "overlay": destination.relative_to(ROOT).as_posix(),
                        "model": model, "scale_px_per_mm": round(abs(factor), 6),
                        "rotation_deg": round(math.degrees(math.atan2(factor.imag, factor.real)), 6),
                        "checks": checks, "projected_pins": projected,
                        "electrical_evidence": False})
    REPORT.write_text(json.dumps({"schema_version": 1, "fits": results}, indent=2) + "\n")
    if errors:
        raise SystemExit("local package registration FAIL\n- " + "\n- ".join(errors))
    print(f"local package registration PASS: {len(results)} fits; wrote {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
