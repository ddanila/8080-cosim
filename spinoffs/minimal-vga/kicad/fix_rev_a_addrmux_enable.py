#!/usr/bin/env python3
"""Move the routed U20/U21 74HCT157 enable island onto GND.

The existing four-segment trace between U20.15 and U21.15 is retained and
reclassified as GND. Both pads then connect to the filled In1.Cu GND plane.
"""

from __future__ import annotations

import sys

import pcbnew


RETIRED_NET = "ADDRMUX_OE_N"
TARGET_NET = "GND"
ENDPOINTS = (("U20", "15"), ("U21", "15"))
EXPECTED_TRACKS = 4


def pad(board: pcbnew.BOARD, ref: str, pin: str) -> pcbnew.PAD:
    footprint = board.FindFootprintByReference(ref)
    result = footprint.FindPadByNumber(pin) if footprint else None
    if result is None:
        raise SystemExit(f"missing PCB endpoint {ref}.{pin}")
    return result


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: fix_rev_a_addrmux_enable.py <rev-a.kicad_pcb>")
    path = sys.argv[1]
    board = pcbnew.LoadBoard(path)
    if board is None:
        raise SystemExit(f"could not load {path}")

    target = board.FindNet(TARGET_NET)
    if target is None:
        raise SystemExit(f"missing target net {TARGET_NET}")
    pads = [pad(board, *endpoint) for endpoint in ENDPOINTS]
    retired = board.FindNet(RETIRED_NET)
    retired_tracks = (
        [track for track in board.GetTracks() if track.GetNetname() == RETIRED_NET]
        if retired is not None
        else []
    )

    if all(item.GetNetname() == TARGET_NET for item in pads) and not retired_tracks:
        print("Rev A address-mux enable: already tied to GND")
        return 0
    if retired is None:
        raise SystemExit(f"missing expected source net {RETIRED_NET}")
    if any(item.GetNetname() != RETIRED_NET for item in pads):
        actual = ", ".join(
            f"{ref}.{pin}={item.GetNetname()}"
            for (ref, pin), item in zip(ENDPOINTS, pads)
        )
        raise SystemExit(f"unexpected mux-enable pad nets: {actual}")
    if len(retired_tracks) != EXPECTED_TRACKS:
        raise SystemExit(
            f"{RETIRED_NET}: expected {EXPECTED_TRACKS} routed segments, "
            f"found {len(retired_tracks)}"
        )

    for item in pads + retired_tracks:
        item.SetNet(target)
    board.BuildListOfNets()
    board.RemoveUnusedNets(None)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(path, board)

    check = pcbnew.LoadBoard(path)
    for ref, pin in ENDPOINTS:
        if pad(check, ref, pin).GetNetname() != TARGET_NET:
            raise SystemExit(f"saved PCB did not move {ref}.{pin} to {TARGET_NET}")
    if any(track.GetNetname() == RETIRED_NET for track in check.GetTracks()):
        raise SystemExit(f"saved PCB still contains {RETIRED_NET} copper")
    print(
        "Rev A address-mux enable: U20.15/U21.15 and "
        f"{EXPECTED_TRACKS} retained segments moved to GND"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
