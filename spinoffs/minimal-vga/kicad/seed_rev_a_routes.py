#!/usr/bin/env python3
import argparse
import os

import pcbnew


TRACK_WIDTH_MM = 0.2
VIA_DIAMETER_MM = 0.6
VIA_DRILL_MM = 0.3

LAYER_BY_NAME = {
    "F.Cu": pcbnew.F_Cu,
    "In1.Cu": pcbnew.In1_Cu,
    "In2.Cu": pcbnew.In2_Cu,
    "B.Cu": pcbnew.B_Cu,
}

SEED_ROUTES = {
    # Tie the two USB-C SMD ground contacts (A12/B12) to the adjacent plated
    # shell tabs; the shell tabs then connect to the In1.Cu GND plane. J3 is
    # rotated 90 deg CW at the left board edge (200x200 layout), so these follow
    # its pads: A12=(7.97,38.31) B12=(7.97,32.81), shell tabs at x=7.79
    # (y 39.88 / 31.24).
    "GND": {
        "vias": [],
        "tracks": [
            ("F.Cu", 7.97, 38.31, 7.79, 39.88),
            ("F.Cu", 7.97, 32.81, 7.79, 31.24),
        ],
    },
    # RE3_D0 taps the РЕ3 pager D0 out to the DECODE-DBG header J95.5. The router
    # routes U4->R36 (its pull-up) but repeatedly leaves the R36->J95 hop through
    # the congested bottom unfinished; seed it down the clear left margin and in
    # to J95.5 from below (clear of the other J95 pins). Follows R36.2=(10.16,
    # 143.51) and J95.5=(24.13,187.96).
    "RE3_D0": {
        "vias": [],
        "tracks": [
            ("B.Cu", 10.16, 143.51, 6.0, 143.51),
            ("B.Cu", 6.0, 143.51, 6.0, 183.0),
            ("B.Cu", 6.0, 183.0, 24.13, 183.0),
            ("B.Cu", 24.13, 183.0, 24.13, 187.96),
        ],
    },
    # NOTE: the previous per-net signal seeds (CLK, MEM_*, KBD_*, VIDEO_*,
    # RESET_N, ...) were hand-tuned for the old 285mm placement and are invalid
    # for the compact 200x200 re-layout. They were removed; the router routes
    # those nets fresh. Re-add targeted seeds only for nets that fail to route.
}


def mm(value):
    return pcbnew.FromMM(value)


def vector(x, y):
    return pcbnew.VECTOR2I(mm(x), mm(y))


def add_track(board, net, layer_name, x1, y1, x2, y2):
    track = pcbnew.PCB_TRACK(board)
    track.SetNet(net)
    track.SetLayer(LAYER_BY_NAME[layer_name])
    track.SetStart(vector(x1, y1))
    track.SetEnd(vector(x2, y2))
    track.SetWidth(mm(TRACK_WIDTH_MM))
    board.Add(track)


def add_via(board, net, x, y):
    via = pcbnew.PCB_VIA(board)
    via.SetNet(net)
    via.SetPosition(vector(x, y))
    via.SetWidth(mm(VIA_DIAMETER_MM))
    via.SetDrill(mm(VIA_DRILL_MM))
    via.SetViaType(pcbnew.VIATYPE_THROUGH)
    board.Add(via)


def main():
    parser = argparse.ArgumentParser(description="Add deterministic Rev A seed routes before FreeRouting.")
    parser.add_argument("board")
    args = parser.parse_args()

    board = pcbnew.LoadBoard(args.board)
    selected = {
        name for name in os.environ.get("SEED_NETS", "").split(",") if name
    }
    if selected:
        unknown = selected - SEED_ROUTES.keys()
        if unknown:
            raise SystemExit(f"unknown seed route(s): {', '.join(sorted(unknown))}")
    added_tracks = 0
    added_vias = 0
    for net_name, route in SEED_ROUTES.items():
        if selected and net_name not in selected:
            continue
        net = board.FindNet(net_name)
        if net is None:
            raise SystemExit(f"missing net for seed route: {net_name}")
        for x, y in route["vias"]:
            add_via(board, net, x, y)
            added_vias += 1
        for layer_name, x1, y1, x2, y2 in route["tracks"]:
            add_track(board, net, layer_name, x1, y1, x2, y2)
            added_tracks += 1

    pcbnew.SaveBoard(args.board, board)
    print(f"seeded Rev A routes: {added_tracks} tracks, {added_vias} vias")


if __name__ == "__main__":
    main()
