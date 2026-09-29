#!/usr/bin/python3
"""Compare D27's photographed left-edge spacing with its routed array."""

import json
from pathlib import Path

import pcbnew
from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "ref/photos/juku-pcb-2/d27-left-edge-placement.json"
BOARD = ROOT / "kicad/juku.kicad_pcb"
OUTPUT = ROOT / "docs/photo-registration/d27-left-edge-placement.json"
ROW_OVERLAY = ROOT / "docs/photo-registration/d27-left-edge-row.jpg"
EDGE_OVERLAY = ROOT / "docs/photo-registration/d27-left-edge-edge.jpg"


def main() -> None:
    evidence = json.loads(EVIDENCE.read_text())
    left_x, left_y = evidence["physical_pin20_left_px"]
    right_x, right_y = evidence["physical_pin1_right_px"]
    edge_x, edge_y = evidence["left_board_edge_at_same_y_px"]
    if max(abs(left_y - right_y), abs(left_y - edge_y)) > 1 or edge_x >= left_x:
        raise SystemExit("invalid D27 same-row edge observations")
    px_per_mm = (right_x - left_x) / evidence["pin_span_mm"]
    if not 15 <= px_per_mm <= 30:
        raise SystemExit("unexpected D27 photo pin pitch")
    photo_left_x_mm = (left_x - edge_x) / px_per_mm
    photo_right_x_mm = (right_x - edge_x) / px_per_mm
    board = pcbnew.LoadBoard(str(BOARD))
    footprint = next(f for f in board.GetFootprints() if f.GetReference() == "D27")
    routed_xs = [p.GetPosition().x / 1e6 for p in footprint.Pads()]
    routed_left_x_mm = min(routed_xs)
    routed_right_x_mm = max(routed_xs)
    if abs(photo_left_x_mm - routed_left_x_mm) > 3:
        raise SystemExit("D27 horizontal residual exceeds 3 mm; review edge observation")
    image = Image.open(ROOT / evidence["image"]).convert("RGB")
    row_crop = (2730, 990, 3960, 1240)
    row = image.crop(row_crop)
    draw = ImageDraw.Draw(row)
    for index in range(20):
        x = left_x + (right_x - left_x) * index / 19 - row_crop[0]
        y = left_y - row_crop[1]
        draw.ellipse((x - 7, y - 7, x + 7, y + 7), outline="cyan", width=2)
    row.save(ROW_OVERLAY, quality=90)
    edge_crop = (100, 970, 240, 1250)
    edge = image.crop(edge_crop)
    draw = ImageDraw.Draw(edge)
    draw.line((edge_x - edge_crop[0], 0, edge_x - edge_crop[0], edge.height), fill="cyan", width=2)
    edge.save(EDGE_OVERLAY, quality=90)
    report = {
        "schema_version": 1,
        "evidence": str(EVIDENCE.relative_to(ROOT)),
        "board": str(BOARD.relative_to(ROOT)),
        "photo_px_per_mm": round(px_per_mm, 3),
        "photo_left_pin_x_mm": round(photo_left_x_mm, 3),
        "photo_right_pin_x_mm": round(photo_right_x_mm, 3),
        "routed_left_pad_x_mm": round(routed_left_x_mm, 3),
        "routed_right_pad_x_mm": round(routed_right_x_mm, 3),
        "left_pin_photo_minus_routed_x_mm": round(photo_left_x_mm - routed_left_x_mm, 3),
        "row_overlay": str(ROW_OVERLAY.relative_to(ROOT)),
        "edge_overlay": str(EDGE_OVERLAY.relative_to(ROOT)),
        "status": "no gross horizontal placement conflict; physical pin-net mapping held",
    }
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(f"D27 left-edge placement check: photo {photo_left_x_mm:.3f} mm vs "
          f"routed {routed_left_x_mm:.3f} mm left row end")


if __name__ == "__main__":
    main()
