#!/usr/bin/python3
"""Overlay unresolved KiCad pads on the rectified owner photographs."""
from __future__ import annotations

import csv
import html
import subprocess
from collections import defaultdict
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "kicad/juku.kicad_pcb"
ENDPOINTS = ROOT / "docs/main-board-unresolved-endpoints.csv"
PHOTO_DIR = ROOT / "docs/photo-registration"
SCALE = 5.0
WIDTH, HEIGHT = 1550, 1330


def main() -> None:
    board = pcbnew.LoadBoard(str(BOARD))
    wanted = defaultdict(set)
    with ENDPOINTS.open(newline="") as source:
        for row in csv.DictReader(source):
            wanted[row["ref"]].add(row["pin"])

    elements = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" '
        f'viewBox="0 0 {WIDTH} {HEIGHT}">',
    ]
    pad_count = 0
    for footprint in board.GetFootprints():
        reference = footprint.GetReference()
        if reference not in wanted:
            continue
        position = footprint.GetPosition()
        x, y = pcbnew.ToMM(position.x) * SCALE, pcbnew.ToMM(position.y) * SCALE
        elements.append(f'<text x="{x + 5:.2f}" y="{y - 5:.2f}" fill="white" stroke="black" '
                        f'stroke-width="0.8" font-family="monospace" font-size="12" '
                        f'font-weight="bold">{html.escape(reference)}</text>')
        for pad in footprint.Pads():
            number = pad.GetNumber()
            if number not in wanted[reference]:
                continue
            position = pad.GetPosition()
            px, py = pcbnew.ToMM(position.x) * SCALE, pcbnew.ToMM(position.y) * SCALE
            elements.append(f'<circle cx="{px:.2f}" cy="{py:.2f}" r="5" fill="none" '
                            f'stroke="#ff1744" stroke-width="2"/>')
            elements.append(f'<text x="{px + 5:.2f}" y="{py - 5:.2f}" fill="#ffeb3b" '
                            f'stroke="black" stroke-width="0.4" font-family="monospace" '
                            f'font-size="8" font-weight="bold">{html.escape(number)}</text>')
            pad_count += 1
    elements.append("</svg>")
    overlay = PHOTO_DIR / "unresolved-endpoint-overlay.svg"
    overlay.write_text("\n".join(elements) + "\n")

    overlay_png = PHOTO_DIR / "unresolved-endpoint-overlay.png"
    subprocess.run(["magick", "-background", "none", str(overlay), str(overlay_png)], check=True)
    for side in ("component_grid", "solder_grid"):
        source = PHOTO_DIR / f"{side}-rectified.jpg"
        destination = PHOTO_DIR / f"{side}-unresolved-overlay.jpg"
        subprocess.run(["magick", str(source), str(overlay_png), "-compose", "over",
                        "-composite", str(destination)], check=True)
        print(f"wrote {destination.relative_to(ROOT)}")
    print(f"wrote {overlay.relative_to(ROOT)} ({pad_count} unresolved pads)")


if __name__ == "__main__":
    main()
