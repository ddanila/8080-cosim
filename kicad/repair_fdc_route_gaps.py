#!/usr/bin/python3
"""A* route deterministic legacy gaps left by the FDC-power route."""

import heapq
import math
import sys

import pcbnew


if len(sys.argv) not in (3, 4, 8, 9, 10):
    raise SystemExit(f"usage: {sys.argv[0]} INPUT.kicad_pcb OUTPUT.kicad_pcb [d26-mode|controls|video-counters|d103|gap NET X1,Y1 X2,Y2 MODE [SEARCH_MARGIN_MM [GRID_STEP_MM]]]")

STEP = float(sys.argv[9]) if len(sys.argv) == 10 else 0.5
if STEP <= 0:
    raise SystemExit("grid step must be positive")
WIDTH = 0.20
CLEARANCE = 0.45
SEARCH_MARGIN = None
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


def mark_circle(blocked, x, y, radius, bounds=(0, MAX_X, 0, MAX_Y)):
    ix0, ix1 = max(bounds[0], math.floor((x - radius) / STEP)), min(bounds[1], math.ceil((x + radius) / STEP))
    iy0, iy1 = max(bounds[2], math.floor((y - radius) / STEP)), min(bounds[3], math.ceil((y + radius) / STEP))
    for ix in range(ix0, ix1 + 1):
        for iy in range(iy0, iy1 + 1):
            if math.hypot(ix * STEP - x, iy * STEP - y) <= radius:
                blocked.add((ix, iy))


def obstacle_map(netname, layer, bounds=(0, MAX_X, 0, MAX_Y)):
    blocked = set()
    edge = math.ceil(0.40 / STEP)
    for ix in range(bounds[0], bounds[1] + 1):
        for iy in range(edge):
            if bounds[2] <= iy <= bounds[3]: blocked.add((ix, iy))
            if bounds[2] <= MAX_Y - iy <= bounds[3]: blocked.add((ix, MAX_Y - iy))
    for iy in range(bounds[2], bounds[3] + 1):
        for ix in range(edge):
            if bounds[0] <= ix <= bounds[1]: blocked.add((ix, iy))
            if bounds[0] <= MAX_X - ix <= bounds[1]: blocked.add((MAX_X - ix, iy))

    for pad in board.GetPads():
        if pad.GetNetname() == netname:
            continue
        x, y = mm(pad.GetPosition())
        size = pad.GetSize()
        radius = pcbnew.ToMM(max(size.x, size.y)) / 2 + CLEARANCE + WIDTH / 2
        mark_circle(blocked, x, y, radius, bounds)

    for item in board.GetTracks():
        if item.GetNetname() == netname:
            continue
        if isinstance(item, pcbnew.PCB_VIA):
            x, y = mm(item.GetPosition())
            mark_circle(blocked, x, y, pcbnew.ToMM(item.GetWidth(layer)) / 2 + CLEARANCE + WIDTH / 2, bounds)
            continue
        if item.GetLayer() != layer:
            continue
        ax, ay = mm(item.GetStart()); bx, by = mm(item.GetEnd())
        radius = pcbnew.ToMM(item.GetWidth()) / 2 + CLEARANCE + WIDTH / 2
        ix0, ix1 = max(bounds[0], math.floor((min(ax, bx) - radius) / STEP)), min(bounds[1], math.ceil((max(ax, bx) + radius) / STEP))
        iy0, iy1 = max(bounds[2], math.floor((min(ay, by) - radius) / STEP)), min(bounds[3], math.ceil((max(ay, by) + radius) / STEP))
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
    start_cell, goal_cell = cell(start), cell(end)
    if SEARCH_MARGIN is None:
        search_bounds = (0, MAX_X, 0, MAX_Y)
    else:
        margin = math.ceil(SEARCH_MARGIN / STEP)
        search_bounds = (max(0, min(start_cell[0], goal_cell[0]) - margin),
                         min(MAX_X, max(start_cell[0], goal_cell[0]) + margin),
                         max(0, min(start_cell[1], goal_cell[1]) - margin),
                         min(MAX_Y, max(start_cell[1], goal_cell[1]) + margin))
    blocked = [obstacle_map(netname, pcbnew.F_Cu, search_bounds),
               obstacle_map(netname, pcbnew.B_Cu, search_bounds)]
    # Layer changes must stay 0.8 mm from existing drilled vias.  Build this
    # keep-out once; scanning every track for every expanded A* state made
    # dense residual routes spend most of their time in an invariant test.
    via_blocked = set()
    for item in board.GetTracks():
        if isinstance(item, pcbnew.PCB_VIA):
            x, y = mm(item.GetPosition())
            mark_circle(via_blocked, x, y, 0.799999, search_bounds)
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
        if (x, y) not in via_blocked and (x, y) not in blocked[1 - layer_index]:
            options.append((x, y, 1 - layer_index, 5.0))
        for nx, ny, nl, move_cost in options:
            if not (search_bounds[0] <= nx <= search_bounds[1]
                    and search_bounds[2] <= ny <= search_bounds[3]) or (nx, ny) in blocked[nl]:
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


def pad(ref, pin):
    return board.FindFootprintByReference(ref).FindPadByNumber(pin).GetPosition()


if len(sys.argv) in (8, 9, 10) and sys.argv[3] == "gap":
    CLEARANCE = 0.45
    netname = sys.argv[4]
    x1, y1 = map(float, sys.argv[5].split(",")); x2, y2 = map(float, sys.argv[6].split(","))
    if sys.argv[7] == "M":
        SEARCH_MARGIN = float(sys.argv[8]) if len(sys.argv) >= 9 else 30.0
        add_multilayer_route(netname, pcbnew.VECTOR2I_MM(x1, y1), pcbnew.VECTOR2I_MM(x2, y2))
    else:
        layer = {"F": (pcbnew.F_Cu,), "B": (pcbnew.B_Cu,), "FB": (pcbnew.F_Cu, pcbnew.B_Cu)}[sys.argv[7]]
        add_route(netname, pcbnew.VECTOR2I_MM(x1, y1), pcbnew.VECTOR2I_MM(x2, y2), layer)
elif len(sys.argv) == 4 and sys.argv[3] == "d26-mode":
    add_multilayer_route("MEM_MODE0", pad("D6", "2"), pad("D26", "16"))
    add_multilayer_route("MEM_MODE1", pad("D6", "1"), pad("D26", "17"))
    add_multilayer_route("FDC_DDEN", pad("D26", "13"), pad("D93", "37"))
    add_multilayer_route("FDC_DDEN", pad("D93", "37"), pad("D6", "15"))
elif len(sys.argv) == 4 and sys.argv[3] == "controls":
    # Extra cell margin prevents diagonal grid chords from grazing the RESET
    # and data traces in the dense CPU/controller cluster.
    CLEARANCE = 0.70
    add_multilayer_route("GND", pad("D1", "13"), pcbnew.VECTOR2I_MM(38.5084, 149.2434), (0, 1), (0,))
    add_multilayer_route("GND", pad("D5", "22"), pad("D5", "14"))
    add_multilayer_route("GND", pad("D4", "9"), pad("D4", "10"))
    add_multilayer_route("GND", pad("D107", "9"), pad("D107", "10"))
    add_multilayer_route("P5V", pad("D4", "11"), pad("D107", "20"))
    add_multilayer_route("P5V", pad("D107", "11"), pad("D107", "20"))
elif len(sys.argv) == 4 and sys.argv[3] == "video-counters":
    add_multilayer_route("P5V", pad("D44", "4"), pcbnew.VECTOR2I_MM(84.515, 190.7772), (0, 1), (0,))
    add_multilayer_route("P5V", pad("D45", "4"), pcbnew.VECTOR2I_MM(96.0105, 226.3492), (0, 1), (1,))
    add_route("GND", pad("D44", "14"), pad("D44", "15"), (pcbnew.B_Cu,))
    add_route("GND", pad("D45", "14"), pad("D45", "15"), (pcbnew.B_Cu,))
elif len(sys.argv) == 4 and sys.argv[3] == "d103":
    CLEARANCE = 0.70
    add_multilayer_route("P5V", pad("D103", "1"), pad("D103", "16"))
    add_multilayer_route("P5V", pad("D103", "1"), pad("D103", "3"))
    add_multilayer_route("P5V", pad("D103", "3"), pad("D103", "4"))
    add_multilayer_route("P5V", pad("D103", "4"), pad("D103", "7"))
    add_multilayer_route("P5V", pad("D103", "7"), pad("D103", "10"))
    add_route("GND", pad("D103", "5"), pad("D103", "6"), (pcbnew.B_Cu,))
    add_multilayer_route("GND", pad("D103", "6"), pad("D103", "8"))
else:
    add_route("VIDEO_OUT", pad("X7", "1"), pad("R65", "1"))
    add_multilayer_route("RESET", pad("D26", "35"), pad("D1", "12"))

pcbnew.SaveBoard(sys.argv[2], board)
label = sys.argv[3] if len(sys.argv) in (4, 8, 9, 10) else "RESET and VIDEO_OUT"
print(f"closed {label} reroute gaps -> {sys.argv[2]}")
