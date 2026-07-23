#!/usr/bin/env python3
"""Make U22 a functional cascaded 8-bit 74HCT393 refresh counter.

The former REFRESH_CLR trace is retained and reclassified as GND so both
active-high reset inputs stay inactive. A new F.Cu/B.Cu route connects
low-nibble Q3 (pin 6) to the high-nibble falling-edge clock (pin 13).
"""

from __future__ import annotations

import sys

import pcbnew


RETIRED_NET = "REFRESH_CLR"
GROUND_NET = "GND"
CASCADE_NET = "REFRESH_ROW3"
RESET_ENDPOINTS = (("U22", "2"), ("U22", "12"))
CASCADE_ENDPOINT = ("U22", "13")
EXPECTED_RETIRED_TRACKS = 3
TRACK_WIDTH_MM = 0.2
VIA_DIAMETER_MM = 0.6
VIA_DRILL_MM = 0.3
CASCADE_TRACKS = (
    ("F.Cu", (92.7807, 101.605), (93.2, 101.0)),
    ("B.Cu", (93.2, 101.0), (93.2, 95.9)),
    ("B.Cu", (93.2, 95.9), (93.4, 95.3)),
    ("B.Cu", (93.4, 95.3), (93.7, 94.8)),
    ("B.Cu", (93.7, 94.8), (94.0, 94.0)),
    ("B.Cu", (94.0, 94.0), (94.4, 93.2)),
    ("B.Cu", (94.4, 93.2), (94.4, 91.6)),
    ("F.Cu", (94.4, 91.6), (95.25, 91.445)),
)
CASCADE_VIAS = ((93.2, 101.0), (94.4, 91.6))


def vector(x_mm: float, y_mm: float) -> pcbnew.VECTOR2I:
    return pcbnew.VECTOR2I(pcbnew.FromMM(x_mm), pcbnew.FromMM(y_mm))


def pad(board: pcbnew.BOARD, ref: str, pin: str) -> pcbnew.PAD:
    footprint = board.FindFootprintByReference(ref)
    result = footprint.FindPadByNumber(pin) if footprint else None
    if result is None:
        raise SystemExit(f"missing PCB endpoint {ref}.{pin}")
    return result


def canonical_segment(track: pcbnew.PCB_TRACK) -> tuple[tuple[float, float], ...]:
    points = (
        (
            round(pcbnew.ToMM(track.GetStart().x), 3),
            round(pcbnew.ToMM(track.GetStart().y), 3),
        ),
        (
            round(pcbnew.ToMM(track.GetEnd().x), 3),
            round(pcbnew.ToMM(track.GetEnd().y), 3),
        ),
    )
    return tuple(sorted(points))


def canonical_points(
    start: tuple[float, float], end: tuple[float, float]
) -> tuple[tuple[float, float], ...]:
    return tuple(
        sorted(
            (
                (round(start[0], 3), round(start[1], 3)),
                (round(end[0], 3), round(end[1], 3)),
            )
        )
    )


def expected_cascade_tracks() -> set[tuple[str, tuple[tuple[float, float], ...]]]:
    return {
        (layer, canonical_points(start, end))
        for layer, start, end in CASCADE_TRACKS
    }


def present_cascade_tracks(
    board: pcbnew.BOARD,
) -> set[tuple[str, tuple[tuple[float, float], ...]]]:
    expected = expected_cascade_tracks()
    return {
        (board.GetLayerName(track.GetLayer()), canonical_segment(track))
        for track in board.GetTracks()
        if type(track).__name__ == "PCB_TRACK"
        and track.GetNetname() == CASCADE_NET
        and (board.GetLayerName(track.GetLayer()), canonical_segment(track)) in expected
    }


def present_cascade_vias(board: pcbnew.BOARD) -> set[tuple[float, float]]:
    expected = set(CASCADE_VIAS)
    return {
        (
            round(pcbnew.ToMM(via.GetPosition().x), 3),
            round(pcbnew.ToMM(via.GetPosition().y), 3),
        )
        for via in board.GetTracks()
        if type(via).__name__ == "PCB_VIA"
        and via.GetNetname() == CASCADE_NET
        and (
            round(pcbnew.ToMM(via.GetPosition().x), 3),
            round(pcbnew.ToMM(via.GetPosition().y), 3),
        )
        in expected
    }


def matching_cascade_track_count(board: pcbnew.BOARD) -> int:
    expected = expected_cascade_tracks()
    return sum(
        1
        for track in board.GetTracks()
        if type(track).__name__ == "PCB_TRACK"
        and track.GetNetname() == CASCADE_NET
        and (board.GetLayerName(track.GetLayer()), canonical_segment(track)) in expected
    )


def matching_cascade_via_count(board: pcbnew.BOARD) -> int:
    expected = set(CASCADE_VIAS)
    return sum(
        1
        for via in board.GetTracks()
        if type(via).__name__ == "PCB_VIA"
        and via.GetNetname() == CASCADE_NET
        and (
            round(pcbnew.ToMM(via.GetPosition().x), 3),
            round(pcbnew.ToMM(via.GetPosition().y), 3),
        )
        in expected
    )


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: fix_rev_a_refresh_counter.py <rev-a.kicad_pcb>")
    path = sys.argv[1]
    board = pcbnew.LoadBoard(path)
    if board is None:
        raise SystemExit(f"could not load {path}")

    ground = board.FindNet(GROUND_NET)
    cascade = board.FindNet(CASCADE_NET)
    if ground is None or cascade is None:
        raise SystemExit(f"missing target net {GROUND_NET} or {CASCADE_NET}")
    reset_pads = [pad(board, *endpoint) for endpoint in RESET_ENDPOINTS]
    clock_pad = pad(board, *CASCADE_ENDPOINT)
    retired = board.FindNet(RETIRED_NET)
    retired_tracks = (
        [track for track in board.GetTracks() if track.GetNetname() == RETIRED_NET]
        if retired is not None
        else []
    )
    expected_tracks = expected_cascade_tracks()
    expected_vias = set(CASCADE_VIAS)
    present_tracks = present_cascade_tracks(board)
    present_vias = present_cascade_vias(board)

    already_corrected = (
        all(item.GetNetname() == GROUND_NET for item in reset_pads)
        and clock_pad.GetNetname() == CASCADE_NET
        and not retired_tracks
        and present_tracks == expected_tracks
        and present_vias == expected_vias
        and matching_cascade_track_count(board) == len(expected_tracks)
        and matching_cascade_via_count(board) == len(expected_vias)
    )
    if already_corrected:
        print("Rev A refresh counter: already cascaded and resets tied to GND")
        return 0

    if retired is None:
        raise SystemExit(f"missing expected source net {RETIRED_NET}")
    if any(item.GetNetname() != RETIRED_NET for item in reset_pads):
        actual = ", ".join(
            f"{ref}.{pin}={item.GetNetname()}"
            for (ref, pin), item in zip(RESET_ENDPOINTS, reset_pads)
        )
        raise SystemExit(f"unexpected refresh-reset pad nets: {actual}")
    if clock_pad.GetNetname() != GROUND_NET:
        raise SystemExit(
            f"unexpected {CASCADE_ENDPOINT[0]}.{CASCADE_ENDPOINT[1]} net "
            f"{clock_pad.GetNetname()}, expected {GROUND_NET}"
        )
    if len(retired_tracks) != EXPECTED_RETIRED_TRACKS:
        raise SystemExit(
            f"{RETIRED_NET}: expected {EXPECTED_RETIRED_TRACKS} routed segments, "
            f"found {len(retired_tracks)}"
        )
    if present_tracks or present_vias:
        raise SystemExit("unexpected partial refresh-counter cascade route")

    for item in reset_pads + retired_tracks:
        item.SetNet(ground)
    clock_pad.SetNet(cascade)
    layers = {"F.Cu": pcbnew.F_Cu, "B.Cu": pcbnew.B_Cu}
    for layer, start, end in CASCADE_TRACKS:
        track = pcbnew.PCB_TRACK(board)
        track.SetNet(cascade)
        track.SetLayer(layers[layer])
        track.SetStart(vector(*start))
        track.SetEnd(vector(*end))
        track.SetWidth(pcbnew.FromMM(TRACK_WIDTH_MM))
        board.Add(track)
    for position in CASCADE_VIAS:
        via = pcbnew.PCB_VIA(board)
        via.SetNet(cascade)
        via.SetPosition(vector(*position))
        via.SetWidth(pcbnew.FromMM(VIA_DIAMETER_MM))
        via.SetDrill(pcbnew.FromMM(VIA_DRILL_MM))
        via.SetViaType(pcbnew.VIATYPE_THROUGH)
        board.Add(via)

    board.BuildListOfNets()
    board.RemoveUnusedNets(None)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(path, board)

    check = pcbnew.LoadBoard(path)
    for ref, pin in RESET_ENDPOINTS:
        if pad(check, ref, pin).GetNetname() != GROUND_NET:
            raise SystemExit(f"saved PCB did not move {ref}.{pin} to {GROUND_NET}")
    if pad(check, *CASCADE_ENDPOINT).GetNetname() != CASCADE_NET:
        raise SystemExit(
            f"saved PCB did not move {CASCADE_ENDPOINT[0]}.{CASCADE_ENDPOINT[1]} "
            f"to {CASCADE_NET}"
        )
    if any(track.GetNetname() == RETIRED_NET for track in check.GetTracks()):
        raise SystemExit(f"saved PCB still contains {RETIRED_NET} copper")
    if (
        present_cascade_tracks(check) != expected_tracks
        or present_cascade_vias(check) != expected_vias
        or matching_cascade_track_count(check) != len(expected_tracks)
        or matching_cascade_via_count(check) != len(expected_vias)
    ):
        raise SystemExit("saved PCB is missing refresh-counter cascade copper")
    print(
        "Rev A refresh counter: retained reset trace moved to GND; "
        f"added {len(expected_tracks)} tracks/{len(expected_vias)} vias "
        "for U22.6-to-U22.13 cascade"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
