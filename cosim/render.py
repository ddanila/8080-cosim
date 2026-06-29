#!/usr/bin/env python3
# Render a raw monochrome bitmap dump as a PNG so we can eyeball it.
# Usage: render.py <dump.bin> <out.png> [stride_bytes] [scale] [msb_first]
import sys
from PIL import Image

path   = sys.argv[1]
outpng = sys.argv[2]
stride = int(sys.argv[3]) if len(sys.argv) > 3 else 64   # bytes per scanline
scale  = int(sys.argv[4]) if len(sys.argv) > 4 else 2
msb    = (sys.argv[5] != "0") if len(sys.argv) > 5 else True

data = open(path, "rb").read()
rows = len(data) // stride
w, h = stride * 8, rows
img = Image.new("1", (w, h))
px = img.load()
for r in range(rows):
    for b in range(stride):
        byte = data[r * stride + b]
        for bit in range(8):
            v = (byte >> (7 - bit)) & 1 if msb else (byte >> bit) & 1
            px[b * 8 + bit, r] = 1 if v else 0   # 1=white pixel set
img = img.resize((w * scale, h * scale), Image.NEAREST)
img.save(outpng)
print(f"{outpng}: {w}x{h} (stride={stride}, msb={msb}) -> scaled x{scale}")
