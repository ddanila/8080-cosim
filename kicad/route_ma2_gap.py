#!/usr/bin/python3
"""Clearance-aware local router for the deterministic D84.13 MA2 gap."""

import heapq
import math
import sys

import pcbnew


if len(sys.argv) != 3:
    raise SystemExit(f"usage: {sys.argv[0]} INPUT.kicad_pcb OUTPUT.kicad_pcb")

board = pcbnew.LoadBoard(sys.argv[1])
pad = board.FindFootprintByReference("D84").FindPadByNumber("13")
assert pad.GetNetname() == "MA2"

STEP = 0.1
X0, X1, Y0, Y1 = 189.0, 203.5, 198.0, 219.0
CLEAR = 0.21
TRACE_W = 0.20
LAYERS = (pcbnew.F_Cu, pcbnew.B_Cu)
START = (202.215, 207.13)
GOAL = (190.915, 207.13)


def mm(point):
    return pcbnew.ToMM(point.x), pcbnew.ToMM(point.y)


def pt_seg(px, py, a, b):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


track_obs = {layer: [] for layer in LAYERS}
via_obs = []
for item in board.GetTracks():
    if item.GetNetname() == "MA2":
        continue
    if item.GetClass() == "PCB_VIA":
        x, y = mm(item.GetPosition())
        if X0 - 2 <= x <= X1 + 2 and Y0 - 2 <= y <= Y1 + 2:
            via_obs.append((x, y, pcbnew.ToMM(item.GetWidth(pcbnew.F_Cu)) / 2 + CLEAR + TRACE_W / 2))
    elif item.GetLayer() in LAYERS:
        a, b = mm(item.GetStart()), mm(item.GetEnd())
        if not (max(a[0], b[0]) < X0 - 2 or min(a[0], b[0]) > X1 + 2 or max(a[1], b[1]) < Y0 - 2 or min(a[1], b[1]) > Y1 + 2):
            track_obs[item.GetLayer()].append((a, b, pcbnew.ToMM(item.GetWidth()) / 2 + CLEAR + TRACE_W / 2))

pad_obs = []
for fp in board.GetFootprints():
    for other in fp.Pads():
        if other.GetNetname() == "MA2":
            continue
        x, y = mm(other.GetPosition())
        if not (X0 - 2 <= x <= X1 + 2 and Y0 - 2 <= y <= Y1 + 2):
            continue
        size = other.GetSize()
        radius = max(pcbnew.ToMM(size.x), pcbnew.ToMM(size.y)) / 2 + CLEAR + TRACE_W / 2
        pad_obs.append((x, y, radius))


def clear(ix, iy, layer):
    x, y = X0 + ix * STEP, Y0 + iy * STEP
    if not (X0 <= x <= X1 and Y0 <= y <= Y1):
        return False
    for ox, oy, radius in pad_obs:
        if math.hypot(x - ox, y - oy) < radius:
            return False
    for ox, oy, radius in via_obs:
        if math.hypot(x - ox, y - oy) < radius:
            return False
    for a, b, radius in track_obs[layer]:
        if pt_seg(x, y, a, b) < radius:
            return False
    return True


def grid(point):
    return round((point[0] - X0) / STEP), round((point[1] - Y0) / STEP)


start_xy, goal_xy = grid(START), grid(GOAL)
starts = [(start_xy[0], start_xy[1], layer) for layer in LAYERS]
goals = {(goal_xy[0], goal_xy[1], layer) for layer in LAYERS}
queue = []
cost = {}
prev = {}
for state in starts:
    cost[state] = 0.0
    heapq.heappush(queue, (0.0, state))

dirs = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
end = None
while queue:
    _score, state = heapq.heappop(queue)
    if state in goals:
        end = state
        break
    ix, iy, layer = state
    for dx, dy in dirs:
        nxt = (ix + dx, iy + dy, layer)
        if nxt not in goals and not clear(*nxt):
            continue
        step_cost = math.hypot(dx, dy)
        new = cost[state] + step_cost
        if new < cost.get(nxt, math.inf):
            cost[nxt], prev[nxt] = new, state
            heuristic = math.hypot(nxt[0] - goal_xy[0], nxt[1] - goal_xy[1])
            heapq.heappush(queue, (new + heuristic, nxt))
    other = pcbnew.B_Cu if layer == pcbnew.F_Cu else pcbnew.F_Cu
    nxt = (ix, iy, other)
    if clear(ix, iy, layer) and clear(ix, iy, other):
        new = cost[state] + 20.0
        if new < cost.get(nxt, math.inf):
            cost[nxt], prev[nxt] = new, state
            heapq.heappush(queue, (new + math.hypot(ix - goal_xy[0], iy - goal_xy[1]), nxt))

if end is None:
    raise SystemExit("no clearance-aware MA2 path found")

path = [end]
while path[-1] not in starts:
    path.append(prev[path[-1]])
path.reverse()

# Collapse collinear grid steps while preserving layer transitions.
points = [(START[0], START[1], path[0][2])]
for idx, state in enumerate(path[1:-1], 1):
    before, after = path[idx - 1], path[idx + 1]
    d1 = (state[0] - before[0], state[1] - before[1], state[2] - before[2])
    d2 = (after[0] - state[0], after[1] - state[1], after[2] - state[2])
    if d1 != d2 or before[2] != state[2] or state[2] != after[2]:
        points.append((X0 + state[0] * STEP, Y0 + state[1] * STEP, state[2]))
points.append((GOAL[0], GOAL[1], path[-1][2]))

for a, b in zip(points, points[1:]):
    if a[2] != b[2]:
        via = pcbnew.PCB_VIA(board)
        via.SetPosition(pcbnew.VECTOR2I_MM(a[0], a[1]))
        via.SetWidth(pcbnew.FromMM(0.6))
        via.SetDrill(pcbnew.FromMM(0.3))
        via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        via.SetNet(pad.GetNet())
        board.Add(via)
        continue
    track = pcbnew.PCB_TRACK(board)
    track.SetStart(pcbnew.VECTOR2I_MM(a[0], a[1]))
    track.SetEnd(pcbnew.VECTOR2I_MM(b[0], b[1]))
    track.SetLayer(a[2])
    track.SetWidth(pcbnew.FromMM(TRACE_W))
    track.SetNet(pad.GetNet())
    board.Add(track)

pcbnew.SaveBoard(sys.argv[2], board)
print(f"routed MA2 gap with {len(points) - 1} items -> {sys.argv[2]}")
