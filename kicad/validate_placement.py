#!/usr/bin/env python3
# Placement validation: project every placed footprint from the generated .kicad_pcb back
# onto the assembly drawing via the verified frame, so the result can be visually checked --
# each crosshair + refdes should land on the matching chip in the drawing. This catches frame
# errors (wrong px/mm, origin, or a chip read at the wrong spot) at a glance.
#
# Frame (emaplaat.pdf @ 200 dpi -> 9554x6976):  board top-left = (1740, 990) px, px/mm = 14.52
#   orig_px = (1740 + mm_x*14.52, 990 + mm_y*14.52)
#
# Run (KiCad python): $KICAD/.../python3 kicad/validate_placement.py <ema2-1.png> <out.png>
import sys, subprocess, pcbnew

TLx, TLy, PXMM = 1740.0, 990.0, 14.52
MAGICK = "/opt/homebrew/bin/magick"
GOST = "/Users/danila.sukharev/fun/8080-cosim/fonts/gost.ttf"

def main():
    drawing, out = sys.argv[1], sys.argv[2]
    board = pcbnew.LoadBoard("kicad/juku.kicad_pcb")
    pts = []
    for fp in board.GetFootprints():
        p = fp.GetBoundingBox(False, False).GetCenter()   # body CENTRE (anchor is a corner)
        ox = TLx + pcbnew.ToMM(p.x) * PXMM
        oy = TLy + pcbnew.ToMM(p.y) * PXMM
        pts.append((fp.GetReference(), ox, oy,
                    pcbnew.ToMM(p.x), pcbnew.ToMM(p.y)))
    # board outline projected (mm 0..BW, 0..BH) — read BW/BH from the edge-cuts bbox
    bb = board.GetBoardEdgesBoundingBox()
    bx0 = TLx + pcbnew.ToMM(bb.GetLeft())*PXMM;  by0 = TLy + pcbnew.ToMM(bb.GetTop())*PXMM
    bx1 = TLx + pcbnew.ToMM(bb.GetRight())*PXMM; by1 = TLy + pcbnew.ToMM(bb.GetBottom())*PXMM

    # --- text report: each chip's mm + %-position, bounds + overlap checks (a pass/fail test) ---
    BL, BT = pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetTop())
    BR, BBm = pcbnew.ToMM(bb.GetRight()), pcbnew.ToMM(bb.GetBottom())
    fps = list(board.GetFootprints()); oob = []
    print(f"{'ref':5} {'type':11} {'mm(x,y)':>12} {'%(x,y)':>11}  in")
    for fp in sorted(fps, key=lambda f: f.GetReference()):
        p = fp.GetBoundingBox(False, False).GetCenter(); mx, my = pcbnew.ToMM(p.x), pcbnew.ToMM(p.y)
        px, py = (mx-BL)/(BR-BL)*100, (my-BT)/(BBm-BT)*100
        inb = BL <= mx <= BR and BT <= my <= BBm
        if not inb: oob.append(fp.GetReference())
        print(f"{fp.GetReference():5} {fp.GetValue()[:11]:11} ({mx:4.0f},{my:4.0f}) ({px:4.0f}%,{py:4.0f}%)  {'ok' if inb else 'OUT'}")
    ov = []
    for i in range(len(fps)):
        for j in range(i+1, len(fps)):
            if fps[i].GetBoundingBox(False, False).Intersects(fps[j].GetBoundingBox(False, False)):
                ov.append((fps[i].GetReference(), fps[j].GetReference()))
    print(f"\nboard {BR-BL:.0f}x{BBm-BT:.0f} mm ; {len(fps)} chips ; out-of-bounds={oob or 'none'} ; overlaps={len(ov)}")
    if ov: print("  overlapping pairs:", ov[:12])
    print("VALIDATION:", "PASS" if not oob and not ov else "FAIL")

    cross = []
    for ref, ox, oy, mx, my in pts:
        cross.append(f"line {ox-28},{oy} {ox+28},{oy} line {ox},{oy-28} {ox},{oy+28}")
    cmd = [MAGICK, drawing,
           "-stroke", "blue", "-strokewidth", "4", "-fill", "none",
           "-draw", f"rectangle {bx0},{by0} {bx1},{by1}",        # projected board outline
           "-stroke", "red", "-strokewidth", "3",
           "-draw", " ".join(cross),
           "-stroke", "none", "-fill", "red", "-font", GOST, "-pointsize", "40"]
    for ref, ox, oy, mx, my in pts:
        cmd += ["-draw", f"text {ox+10},{oy-10} '{ref}'"]
    cmd += ["-resize", "3800x", out]
    subprocess.run(cmd, check=True)
    print(f"validated {len(pts)} chips; board outline proj = "
          f"({pcbnew.ToMM(bb.GetLeft()):.0f},{pcbnew.ToMM(bb.GetTop()):.0f}) .. "
          f"({pcbnew.ToMM(bb.GetRight()):.0f},{pcbnew.ToMM(bb.GetBottom()):.0f}) mm -> {out}")

if __name__ == "__main__":
    main()
