#!/usr/bin/env python3
# Repair pass for widen_power_v2: narrow power tracks near DRC violation coordinates back to
# 0.25 mm. Run: <kicad-python3> narrow_at_violations.py <board> <drc.rpt>
import sys, re, math, pcbnew
BOARD, RPT = sys.argv[1], sys.argv[2]
POWER = {'GND', 'P5V', 'P12V', 'M12V', 'M5V_DERIVED'}
b = pcbnew.LoadBoard(BOARD)
power_codes = {b.GetNetsByName()[n].GetNetCode() for n in POWER if n in b.GetNetsByName()}
txt = open(RPT).read()
coords = []
grab = False
for line in txt.splitlines():
    if re.search(r'\[(clearance|shorting_items|hole_clearance)\]', line):
        grab = True
        continue
    m = re.match(r'\s+@\((\d+\.\d+) mm, (\d+\.\d+) mm\)', line)
    if m and grab:
        coords.append((float(m.group(1)), float(m.group(2))))
    elif not m:
        grab = grab and line.strip().startswith(('Rule', 'Local'))
def pt_seg(px, py, x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    L2 = dx * dx + dy * dy
    if L2 == 0:
        return math.hypot(px - x1, py - y1)
    t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / L2))
    return math.hypot(px - (x1 + t * dx), py - (y1 + t * dy))
n = 0
for t in b.GetTracks():
    if t.GetClass() != 'PCB_TRACK' or t.GetNetCode() not in power_codes:
        continue
    if t.GetWidth() <= pcbnew.FromMM(0.21):
        continue
    s, e = t.GetStart(), t.GetEnd()
    x1, y1 = pcbnew.ToMM(s.x), pcbnew.ToMM(s.y)
    x2, y2 = pcbnew.ToMM(e.x), pcbnew.ToMM(e.y)
    for (cx, cy) in coords:
        if pt_seg(cx, cy, x1, y1, x2, y2) < 2.0:
            t.SetWidth(pcbnew.FromMM(0.2))   # back to freerouting's native width
            n += 1
            break
pcbnew.SaveBoard(BOARD, b)
print(f"narrowed {n} tracks near {len(coords)} violation points")
