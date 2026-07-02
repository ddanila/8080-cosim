#!/usr/bin/env python3
# Overlay our board render onto a board photo (v1: solder side).
# The render is mirrored (back view) and affine-warped onto the photo via 3 corner anchors.
# Usage: python3 kicad/overlay_photo.py <render.png> <photo.jpg> <out.png> \
#            --photo-corners TLx,TLy TRx,TRy BLx,BLy   (board corners in photo pixels)
import sys
from PIL import Image, ImageOps, ImageEnhance

render_p, photo_p, out_p = sys.argv[1], sys.argv[2], sys.argv[3]
idx = sys.argv.index('--photo-corners')
c = [tuple(map(float, a.split(','))) for a in sys.argv[idx+1:idx+4]]  # TL, TR, BL in photo px

photo = Image.open(photo_p).convert('RGB')
render = Image.open(render_p).convert('RGBA')
render = ImageOps.mirror(render)                     # back view = mirrored board coords
W, H = render.size

# affine: render (0,0)->TL, (W,0)->TR, (0,H)->BL ; PIL wants the INVERSE map (out->in)
(tlx,tly),(trx,try_),(blx,bly) = c
# forward: x' = a*x + b*y + tx ; y' = d*x + e*y + ty
a = (trx-tlx)/W; b = (blx-tlx)/H; tx = tlx
d = (try_-tly)/W; e = (bly-tly)/H; ty = tly
det = a*e - b*d
ia, ib, itx = e/det, -b/det, (b*ty - e*tx)/det
id_, ie, ity = -d/det, a/det, (d*tx - a*ty)/det
warped = render.transform(photo.size, Image.AFFINE, (ia, ib, itx, id_, ie, ity),
                          resample=Image.BILINEAR)
# tint the render magenta and blend
px = warped.load()
tinted = Image.new('RGBA', warped.size, (0,0,0,0))
tp = tinted.load()
for y in range(0, warped.size[1], 1):
    for x in range(0, warped.size[0], 1):
        r,g,bb,al = px[x,y]
        if al > 10 and (r+g+bb) < 700:               # copper artwork (not white bg)
            tp[x,y] = (255, 0, 255, 140)
out = photo.copy()
out.paste(tinted, (0,0), tinted)
out.save(out_p)
print('overlay ->', out_p)
