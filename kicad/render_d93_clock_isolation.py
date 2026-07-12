#!/usr/bin/env python3
"""Render raw-tile evidence that D93.24 and D99.13 do not share solder copper."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
CASES = (
    ("D93.24 CLK", "ref/photos/juku-pcb-2/PXL_20260710_200506061.jpg",
     1554.344, 2232.422, (1050, 1900, 2050, 2500)),
    ("D99.13 Q", "ref/photos/juku-pcb-2/PXL_20260710_200522685.jpg",
     1125.571, 736.857, (700, 480, 1500, 1080)),
)
OUTPUT = ROOT / "docs/photo-registration/d93-clock-solder-isolation.jpg"


def main() -> None:
    panels = []
    font = ImageFont.load_default()
    for label, path, x, y, box in CASES:
        image = Image.open(ROOT / path).convert("RGB")
        draw = ImageDraw.Draw(image)
        draw.ellipse((x-20, y-20, x+20, y+20), outline="red", width=8)
        draw.text((x+25, y-12), label, fill="yellow", stroke_width=2,
                  stroke_fill="black", font=font)
        panels.append(image.crop(box).resize((1000, 600)))
    result = Image.new("RGB", (1000, 1200), "black")
    for index, panel in enumerate(panels):
        result.paste(panel, (0, index * 600))
    result.save(OUTPUT, quality=92)
    print(f"wrote {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
