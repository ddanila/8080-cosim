#!/usr/bin/env python3
# Power-trace widening, geometric edition (replaces the parked widen_power.py DRC-cycle approach).
# For every track segment on a power net, find the nearest FOREIGN copper (other-net track
# segments and pads) and widen the segment to the largest width that keeps >= MIN_CLEAR of air,
# clamped to [0.25, 1.0] mm. Same-net copper is ignored (touching is fine). Vias are left alone
# (annular budget). kicad-cli DRC afterwards is the authoritative gate -- this script only
# proposes widths that the geometry allows, so DRC should stay clean; if it doesn't, restore the
# board from git.
#
# Run with KiCad's python when available:
#   <kicad-python3> kicad/widen_power_v2.py <board.kicad_pcb>
#
# KiCad 10.99/nightly no longer ships the legacy SWIG `pcbnew` module. In that case this
# script falls back to a conservative KiCad-file pass that preserves the s-expression text
# and rewrites only widened `(width ...)` fields on routed power segments.
import sys, math, re
from pathlib import Path

try:
    import pcbnew
except ModuleNotFoundError:
    pcbnew = None

BOARD = sys.argv[1]
POWER = {'GND', 'P5V', 'P12V', 'M12V', 'M5V_DERIVED'}
MIN_CLEAR_MM = 0.26     # a hair over the 0.25 rule for numeric safety
W_MAX_MM = 1.0
W_MIN_MM = 0.20         # freerouting's native routed width
GAIN_MIN_MM = 0.10      # don't bother widening by less than this


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


def widen_with_pcbnew():
    MIN_CLEAR = pcbnew.FromMM(MIN_CLEAR_MM)
    W_MAX = pcbnew.FromMM(W_MAX_MM)
    W_MIN = pcbnew.FromMM(W_MIN_MM)
    GAIN_MIN = pcbnew.FromMM(GAIN_MIN_MM)

    b = pcbnew.LoadBoard(BOARD)
    if b is None:
        return False

    def seg_pts(t):
        s, e = t.GetStart(), t.GetEnd()
        return (s.x, s.y, e.x, e.y)

    # Collect obstacles per layer: (bbox, kind, geometry, half_width, netcode)
    tracks = [t for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK']
    vias = [t for t in b.GetTracks() if t.GetClass() == 'PCB_VIA']

    obstacles = {pcbnew.F_Cu: [], pcbnew.B_Cu: []}
    for t in tracks:
        lay = t.GetLayer()
        if lay in obstacles:
            obstacles[lay].append(('seg', seg_pts(t), t.GetWidth() / 2.0, t.GetNetCode(), t))
    for v in vias:
        for lay in (pcbnew.F_Cu, pcbnew.B_Cu):
            p = v.GetPosition()
            obstacles[lay].append(('pt', (p.x, p.y), v.GetWidth() / 2.0, v.GetNetCode(), v))
    for fp in b.GetFootprints():
        for pad in fp.Pads():
            p = pad.GetPosition()
            sz = pad.GetSize()
            half = max(sz.x, sz.y) / 2.0          # conservative circumscribed radius
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
        R = W_MAX / 2.0 + MIN_CLEAR + pcbnew.FromMM(1.6)   # search halo
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
    print(f"power tracks: {total}, widened: {widened} (pcbnew; clamp 0.20-1.0 mm, "
          f"clearance floor {pcbnew.ToMM(MIN_CLEAR):.2f} mm) -> {BOARD}")
    return True


def find_block_end(text, start):
    depth = 0
    for i in range(start, len(text)):
        if text[i] == '(':
            depth += 1
        elif text[i] == ')':
            depth -= 1
            if depth == 0:
                return i + 1
    raise ValueError(f"unclosed s-expression at byte {start}")


def iter_blocks(text, head):
    pos = 0
    needle = f"({head}"
    while True:
        start = text.find(needle, pos)
        if start < 0:
            return
        if start > 0 and text[start - 1] not in " \t\r\n(":
            pos = start + 1
            continue
        end = find_block_end(text, start)
        yield start, end, text[start:end]
        pos = end


def first_float(block, pattern):
    m = re.search(pattern, block)
    return float(m.group(1)) if m else None


def first_pair(block, pattern):
    m = re.search(pattern, block)
    return (float(m.group(1)), float(m.group(2))) if m else None


def first_str(block, pattern):
    m = re.search(pattern, block)
    return m.group(1) if m else None


def rotate_point(x, y, deg):
    if not deg:
        return x, y
    # KiCad PCB file angles are clockwise in board coordinates.
    r = math.radians(-deg)
    c, s = math.cos(r), math.sin(r)
    return x * c - y * s, x * s + y * c


def fmt_mm(v):
    return f"{v:.4f}".rstrip("0").rstrip(".")


def widen_text_fallback():
    path = Path(BOARD)
    text = path.read_text()
    tracks = []
    vias = []
    obstacles = {"F.Cu": [], "B.Cu": []}

    for start, end, block in iter_blocks(text, "segment"):
        p0 = first_pair(block, r'\(start\s+([-0-9.]+)\s+([-0-9.]+)\)')
        p1 = first_pair(block, r'\(end\s+([-0-9.]+)\s+([-0-9.]+)\)')
        width_m = re.search(r'\(width\s+([-0-9.]+)\)', block)
        layer = first_str(block, r'\(layer\s+"([^"]+)"\)')
        net = first_str(block, r'\(net\s+"([^"]+)"\)')
        if not p0 or not p1 or not width_m or layer not in obstacles:
            continue
        width = float(width_m.group(1))
        item = {
            "kind": "seg",
            "geom": (p0[0], p0[1], p1[0], p1[1]),
            "half": width / 2.0,
            "net": net,
            "layer": layer,
            "start": start,
            "end": end,
            "width": width,
            "width_span": (start + width_m.start(1), start + width_m.end(1)),
        }
        tracks.append(item)
        obstacles[layer].append(item)

    for _start, _end, block in iter_blocks(text, "via"):
        p = first_pair(block, r'\(at\s+([-0-9.]+)\s+([-0-9.]+)\)')
        size = first_float(block, r'\(size\s+([-0-9.]+)\)')
        net = first_str(block, r'\(net\s+"([^"]+)"\)')
        if not p or size is None:
            continue
        via = {"kind": "pt", "geom": p, "half": size / 2.0, "net": net}
        vias.append(via)
        for lay in obstacles:
            obstacles[lay].append(via)

    for _fp_start, _fp_end, fp in iter_blocks(text, "footprint"):
        at = re.search(r'\(at\s+([-0-9.]+)\s+([-0-9.]+)(?:\s+([-0-9.]+))?\)', fp)
        if not at:
            continue
        fx, fy = float(at.group(1)), float(at.group(2))
        rot = float(at.group(3) or 0.0)
        for _pad_start, _pad_end, pad in iter_blocks(fp, "pad"):
            pat = first_pair(pad, r'\(at\s+([-0-9.]+)\s+([-0-9.]+)(?:\s+[-0-9.]+)?\)')
            size = first_pair(pad, r'\(size\s+([-0-9.]+)\s+([-0-9.]+)\)')
            net = first_str(pad, r'\(net\s+"([^"]+)"\)')
            layers_m = re.search(r'\(layers\s+([^)]+)\)', pad)
            if not pat or not size or not layers_m:
                continue
            dx, dy = rotate_point(pat[0], pat[1], rot)
            px, py = fx + dx, fy + dy
            half = math.hypot(size[0], size[1]) / 2.0
            layers = layers_m.group(1)
            pad_ob = {"kind": "pt", "geom": (px, py), "half": half, "net": net}
            for lay in obstacles:
                if '"*.Cu"' in layers or f'"{lay}"' in layers:
                    obstacles[lay].append(pad_ob)

    widened = 0
    total = 0
    replacements = []
    for t in tracks:
        if t["net"] not in POWER:
            continue
        total += 1
        layer_obs = obstacles[t["layer"]]
        a = t["geom"]
        bx1, by1 = min(a[0], a[2]), min(a[1], a[3])
        bx2, by2 = max(a[0], a[2]), max(a[1], a[3])
        R = W_MAX_MM / 2.0 + MIN_CLEAR_MM + 1.6
        best_air = None
        for ob in layer_obs:
            if ob is t or ob["net"] == t["net"]:
                continue
            g = ob["geom"]
            half = ob["half"]
            if ob["kind"] == "seg" and ob["net"] in POWER:
                half = max(half, W_MAX_MM / 2.0)
            if ob["kind"] == "seg":
                ox1, oy1 = min(g[0], g[2]), min(g[1], g[3])
                ox2, oy2 = max(g[0], g[2]), max(g[1], g[3])
            else:
                ox1, oy1 = g[0] - half, g[1] - half
                ox2, oy2 = g[0] + half, g[1] + half
            if ox1 > bx2 + R or ox2 < bx1 - R or oy1 > by2 + R or oy2 < by1 - R:
                continue
            if ob["kind"] == "seg":
                d = seg_seg_dist(a, g) - half
            else:
                d = seg_seg_dist(a, (g[0], g[1], g[0], g[1])) - half
            if best_air is None or d < best_air:
                best_air = d
        if best_air is None:
            allowed = W_MAX_MM
        else:
            allowed = 2 * (best_air - MIN_CLEAR_MM)
        new_w = max(W_MIN_MM, min(W_MAX_MM, allowed))
        if new_w >= t["width"] + GAIN_MIN_MM:
            replacements.append((*t["width_span"], fmt_mm(new_w)))
            widened += 1

    for a, b, repl in sorted(replacements, reverse=True):
        text = text[:a] + repl + text[b:]
    path.write_text(text)
    print(f"power tracks: {total}, widened: {widened} (text fallback; clamp 0.20-1.0 mm, "
          f"clearance floor {MIN_CLEAR_MM:.2f} mm) -> {BOARD}")
    return True


if pcbnew is not None and widen_with_pcbnew():
    pass
else:
    widen_text_fallback()
