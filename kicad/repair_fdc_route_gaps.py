#!/usr/bin/python3
"""A* route the three deterministic legacy gaps left by the FDC-power route."""

import heapq
import math
import sys

import pcbnew


if len(sys.argv) != 3:
    raise SystemExit(f"usage: {sys.argv[0]} INPUT.kicad_pcb OUTPUT.kicad_pcb")

STEP = 0.5
WIDTH = 0.20
CLEARANCE = 0.45
MAX_X, MAX_Y = round(310 / STEP), round(266 / STEP)
board = pcbnew.LoadBoard(sys.argv[1])


def mm(point):
    return pcbnew.ToMM(point.x), pcbnew.ToMM(point.y)


def cell(point):
    x, y = mm(point)
    return round(x / STEP), round(y / STEP)


def point_segment_distance(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def mark_circle(blocked, x, y, radius):
    ix0, ix1 = max(0, math.floor((x - radius) / STEP)), min(MAX_X, math.ceil((x + radius) / STEP))
    iy0, iy1 = max(0, math.floor((y - radius) / STEP)), min(MAX_Y, math.ceil((y + radius) / STEP))
    for ix in range(ix0, ix1 + 1):
        for iy in range(iy0, iy1 + 1):
            if math.hypot(ix * STEP - x, iy * STEP - y) <= radius:
                blocked.add((ix, iy))


def obstacle_map(netname, layer):
    blocked = set()
    edge = math.ceil(0.40 / STEP)
    for ix in range(MAX_X + 1):
        for iy in range(edge):
            blocked.add((ix, iy)); blocked.add((ix, MAX_Y - iy))
    for iy in range(MAX_Y + 1):
        for ix in range(edge):
            blocked.add((ix, iy)); blocked.add((MAX_X - ix, iy))

    for pad in board.GetPads():
        if pad.GetNetname() == netname:
            continue
        x, y = mm(pad.GetPosition())
        size = pad.GetSize()
        radius = pcbnew.ToMM(max(size.x, size.y)) / 2 + CLEARANCE + WIDTH / 2
        mark_circle(blocked, x, y, radius)

    for item in board.GetTracks():
        if item.GetNetname() == netname:
            continue
        if isinstance(item, pcbnew.PCB_VIA):
            x, y = mm(item.GetPosition())
            mark_circle(blocked, x, y, pcbnew.ToMM(item.GetWidth(layer)) / 2 + CLEARANCE + WIDTH / 2)
            continue
        if item.GetLayer() != layer:
            continue
        ax, ay = mm(item.GetStart()); bx, by = mm(item.GetEnd())
        radius = pcbnew.ToMM(item.GetWidth()) / 2 + CLEARANCE + WIDTH / 2
        ix0, ix1 = max(0, math.floor((min(ax, bx) - radius) / STEP)), min(MAX_X, math.ceil((max(ax, bx) + radius) / STEP))
        iy0, iy1 = max(0, math.floor((min(ay, by) - radius) / STEP)), min(MAX_Y, math.ceil((max(ay, by) + radius) / STEP))
        for ix in range(ix0, ix1 + 1):
            for iy in range(iy0, iy1 + 1):
                if point_segment_distance(ix * STEP, iy * STEP, ax, ay, bx, by) <= radius:
                    blocked.add((ix, iy))
    return blocked


MOVES = [(1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0),
         (1, 1, 1.414), (1, -1, 1.414), (-1, 1, 1.414), (-1, -1, 1.414)]


def find_path(start_point, end_point, blocked):
    start, goal = cell(start_point), cell(end_point)
    for center in (start, goal):
        for dx in range(-3, 4):
            for dy in range(-3, 4):
                blocked.discard((center[0] + dx, center[1] + dy))
    queue = [(0.0, 0.0, start)]
    previous = {start: None}
    cost = {start: 0.0}
    while queue:
        _, current_cost, current = heapq.heappop(queue)
        if current == goal:
            break
        if current_cost != cost[current]:
            continue
        for dx, dy, move_cost in MOVES:
            nxt = current[0] + dx, current[1] + dy
            if not (0 <= nxt[0] <= MAX_X and 0 <= nxt[1] <= MAX_Y) or nxt in blocked:
                continue
            candidate = current_cost + move_cost
            if candidate < cost.get(nxt, float("inf")):
                cost[nxt] = candidate
                previous[nxt] = current
                heuristic = math.hypot(goal[0] - nxt[0], goal[1] - nxt[1])
                heapq.heappush(queue, (candidate + heuristic, candidate, nxt))
    if goal not in previous:
        return None
    path = []
    current = goal
    while current is not None:
        path.append(current); current = previous[current]
    path.reverse()
    simplified = [path[0]]
    direction = None
    for index in range(1, len(path)):
        new_direction = (path[index][0] - path[index - 1][0], path[index][1] - path[index - 1][1])
        if direction is not None and new_direction != direction:
            simplified.append(path[index - 1])
        direction = new_direction
    simplified.append(path[-1])
    return simplified


def add_route(netname, start, end, layers=(pcbnew.F_Cu, pcbnew.B_Cu), endpoint_vias=False):
    best = None
    for layer in layers:
        path = find_path(start, end, obstacle_map(netname, layer))
        if path is not None:
            length = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(path, path[1:]))
            if best is None or length < best[0]:
                best = length, layer, path
    if best is None:
        raise SystemExit(f"no A* route for {netname}")
    _, layer, path = best
    points = [start] + [pcbnew.VECTOR2I_MM(ix * STEP, iy * STEP) for ix, iy in path[1:-1]] + [end]
    net = board.FindNet(netname)
    if endpoint_vias:
        for position in (start, end):
            via = pcbnew.PCB_VIA(board); via.SetPosition(position)
            via.SetWidth(pcbnew.FromMM(0.6)); via.SetDrill(pcbnew.FromMM(0.3))
            via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); via.SetNet(net); board.Add(via)
    for a, b in zip(points, points[1:]):
        track = pcbnew.PCB_TRACK(board)
        track.SetStart(a); track.SetEnd(b); track.SetLayer(layer)
        track.SetWidth(pcbnew.FromMM(WIDTH)); track.SetNet(net); board.Add(track)
    print(f"{netname}: {pcbnew.LayerName(layer)} {len(points) - 1} segments")


def add_multilayer_route(netname, start, end, start_layers=(0, 1), goal_layers=(0, 1)):
    blocked = [obstacle_map(netname, pcbnew.F_Cu), obstacle_map(netname, pcbnew.B_Cu)]
    start_cell, goal_cell = cell(start), cell(end)
    for layer_index in start_layers:
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                blocked[layer_index].discard((start_cell[0] + dx, start_cell[1] + dy))
    for layer_index in goal_layers:
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                blocked[layer_index].discard((goal_cell[0] + dx, goal_cell[1] + dy))
    queue = []
    previous, cost = {}, {}
    for layer_index in start_layers:
        state = (start_cell[0], start_cell[1], layer_index)
        previous[state] = None; cost[state] = 0.0
        heapq.heappush(queue, (0.0, 0.0, state))
    goal_state = None
    while queue:
        _, current_cost, current = heapq.heappop(queue)
        if current_cost != cost[current]:
            continue
        if current[:2] == goal_cell and current[2] in goal_layers:
            goal_state = current; break
        x, y, layer_index = current
        options = [(x + dx, y + dy, layer_index, move_cost) for dx, dy, move_cost in MOVES]
        if (x, y) not in blocked[1 - layer_index]:
            options.append((x, y, 1 - layer_index, 5.0))
        for nx, ny, nl, move_cost in options:
            if not (0 <= nx <= MAX_X and 0 <= ny <= MAX_Y) or (nx, ny) in blocked[nl]:
                continue
            nxt = (nx, ny, nl); candidate = current_cost + move_cost
            if candidate < cost.get(nxt, float("inf")):
                cost[nxt] = candidate; previous[nxt] = current
                heuristic = math.hypot(goal_cell[0] - nx, goal_cell[1] - ny)
                heapq.heappush(queue, (candidate + heuristic, candidate, nxt))
    if goal_state is None:
        raise SystemExit(f"no multilayer A* route for {netname}")
    path = []
    state = goal_state
    while state is not None:
        path.append(state); state = previous[state]
    path.reverse()
    compressed = [path[0]]
    direction = None
    for index in range(1, len(path)):
        prior, current = path[index - 1], path[index]
        new_direction = (current[0] - prior[0], current[1] - prior[1], current[2] - prior[2])
        if direction is not None and new_direction != direction:
            compressed.append(prior)
        direction = new_direction
    compressed.append(path[-1])
    path = compressed
    net = board.FindNet(netname)
    last_point, last_layer = start, path[0][2]
    segment_count = via_count = 0
    for index in range(1, len(path)):
        x, y, layer_index = path[index]
        point = end if index == len(path) - 1 else pcbnew.VECTOR2I_MM(x * STEP, y * STEP)
        if layer_index != last_layer:
            via = pcbnew.PCB_VIA(board); via.SetPosition(last_point)
            via.SetWidth(pcbnew.FromMM(0.6)); via.SetDrill(pcbnew.FromMM(0.3))
            via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); via.SetNet(net); board.Add(via)
            last_layer = layer_index; via_count += 1
        elif point != last_point:
            track = pcbnew.PCB_TRACK(board); track.SetStart(last_point); track.SetEnd(point)
            track.SetLayer(pcbnew.F_Cu if layer_index == 0 else pcbnew.B_Cu)
            track.SetWidth(pcbnew.FromMM(WIDTH)); track.SetNet(net); board.Add(track)
            last_point = point; segment_count += 1
    print(f"{netname}: multilayer {segment_count} segments + {via_count} vias")


add_multilayer_route("RF_TANK", pcbnew.VECTOR2I_MM(252.1, 103.2), pcbnew.VECTOR2I_MM(263.3222, 104.233), (1,), (1,))
add_route("VIDEO_OUT", board.FindFootprintByReference("X7").FindPadByNumber("1").GetPosition(), board.FindFootprintByReference("R65").FindPadByNumber("1").GetPosition())
add_multilayer_route("RESET", board.FindFootprintByReference("D26").FindPadByNumber("35").GetPosition(), board.FindFootprintByReference("D1").FindPadByNumber("12").GetPosition())

pcbnew.SaveBoard(sys.argv[2], board)
print(f"closed RESET, VIDEO_OUT, and RF_TANK reroute gaps -> {sys.argv[2]}")
