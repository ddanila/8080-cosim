#!/usr/bin/env python3
# Power-trace widening, geometric edition (replaces the parked widen_power.py DRC-cycle approach).
# For every track segment on a power net, find the nearest FOREIGN copper (other-net track
# segments and pads) and widen the segment to the largest width that keeps >= MIN_CLEAR of air,
# clamped to [0.25, 1.0] mm. Same-net copper is ignored (touching is fine). Vias are left alone
# (annular budget). kicad-cli DRC afterwards is the authoritative gate -- this script only
# proposes widths that the geometry allows, so DRC should stay clean; if it doesn't, restore the
# board from git.
#
# Run with KiCad's python:  <kicad-python3> kicad/widen_power_v2.py <board.kicad_pcb>
import sys, math, pcbnew

BOARD = sys.argv[1]
POWER = {'GND', 'P5V', 'P12V', 'M12V', 'M5V_DERIVED'}
MIN_CLEAR = pcbnew.FromMM(0.26)     # a hair over the 0.25 rule for numeric safety
W_MAX = pcbnew.FromMM(1.0)
W_MIN = pcbnew.FromMM(0.25)
GAIN_MIN = pcbnew.FromMM(0.10)      # don't bother widening by less than this

b = pcbnew.LoadBoard(BOARD)


def seg_pts(t):
    s, e = t.GetStart(), t.GetEnd()
    return (s.x, s.y, e.x, e.y)


def seg_seg_dist(a, c):
    """Min distance between two segments (x1,y1,x2,y2)."""
    def clamp(v, lo, hi):
        return lo if v < lo else hi if v > hi else v

    def pt_seg(px, py, x1, y1, x2, y2):
        dx, dy = x2 - x1, y2 - y1
        L2 = dx * dx + dy * dy
        if L2 == 0:
            return math.hypot(px - x1, py - y1)
        t = clamp(((px - x1) * dx + (py - y1) * dy) / L2, 0.0, 1.0)
        return math.hypot(px - (x1 + t * dx), py - (y1 + t * dy))

    ax1, ay1, ax2, ay2 = a
    cx1, cy1, cx2, cy2 = c

    def ccw(ax, ay, bx, by, cx, cy):
        return (cy - ay) * (bx - ax) - (by - ay) * (cx - ax)

    d1 = ccw(ax1, ay1, ax2, ay2, cx1, cy1)
    d2 = ccw(ax1, ay1, ax2, ay2, cx2, cy2)
    d3 = ccw(cx1, cy1, cx2, cy2, ax1, ay1)
    d4 = ccw(cx1, cy1, cx2, cy2, ax2, ay2)
    if ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)):
        return 0.0
    return min(pt_seg(ax1, ay1, *c), pt_seg(ax2, ay2, *c),
               pt_seg(cx1, cy1, *a), pt_seg(cx2, cy2, *a))


# Collect obstacles per layer: (bbox, kind, geometry, half_width, netcode)
tracks = [t for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK']
vias = [t for t in b.GetTracks() if t.GetClass() == 'PCB_VIA']

obstacles = {pcbnew.F_Cu: [], pcbnew.B_Cu: []}
for t in tracks:
    lay = t.GetLayer()
    if lay in obstacles:
        obstacles[lay].append(('seg', seg_pts(t), t.GetWidth() // 2, t.GetNetCode(), t))
for v in vias:
    for lay in (pcbnew.F_Cu, pcbnew.B_Cu):
        p = v.GetPosition()
        obstacles[lay].append(('pt', (p.x, p.y), v.GetWidth() // 2, v.GetNetCode(), v))
for fp in b.GetFootprints():
    for pad in fp.Pads():
        p = pad.GetPosition()
        sz = pad.GetSize()
        half = max(sz.x, sz.y) // 2          # conservative circumscribed radius
        for lay in (pcbnew.F_Cu, pcbnew.B_Cu):
            if pad.IsOnLayer(lay):
                obstacles[lay].append(('pt', (p.x, p.y), half, pad.GetNetCode(), pad))

power_codes = {b.GetNetsByName()[n].GetNetCode() for n in POWER if n in b.GetNetsByName()}

widened = 0
total = 0
for t in tracks:
    if t.GetNetCode() not in power_codes:
        continue
    total += 1
    lay = t.GetLayer()
    if lay not in obstacles:
        continue
    a = seg_pts(t)
    bx1, by1 = min(a[0], a[2]), min(a[1], a[3])
    bx2, by2 = max(a[0], a[2]), max(a[1], a[3])
    R = W_MAX // 2 + MIN_CLEAR + pcbnew.FromMM(1.6)   # search halo
    best_air = None
    for kind, g, half, net, obj in obstacles[lay]:
        if obj is t or net == t.GetNetCode():
            continue
        # bbox prefilter
        if kind == 'seg':
            ox1, oy1 = min(g[0], g[2]), min(g[1], g[3])
            ox2, oy2 = max(g[0], g[2]), max(g[1], g[3])
        else:
            ox1, oy1 = g[0] - half, g[1] - half
            ox2, oy2 = g[0] + half, g[1] + half
        if ox1 > bx2 + R or ox2 < bx1 - R or oy1 > by2 + R or oy2 < by1 - R:
            continue
        if kind == 'seg':
            d = seg_seg_dist(a, g) - half
        else:
            # point/pad: distance from segment to centre minus radius
            d = seg_seg_dist(a, (g[0], g[1], g[0], g[1])) - half
        if best_air is None or d < best_air:
            best_air = d
    # allowed total width: centreline distance minus clearance, doubled
    if best_air is None:
        allowed = W_MAX
    else:
        allowed = 2 * (best_air - MIN_CLEAR)
    new_w = max(W_MIN, min(W_MAX, int(allowed)))
    if new_w >= t.GetWidth() + GAIN_MIN:
        t.SetWidth(new_w)
        widened += 1

pcbnew.SaveBoard(BOARD, b)
print(f"power tracks: {total}, widened: {widened} (clamp 0.25-1.0 mm, clearance floor "
      f"{pcbnew.ToMM(MIN_CLEAR):.2f} mm) -> {BOARD}")
