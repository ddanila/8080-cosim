#!/usr/bin/env /usr/bin/python3
"""Apply the native .009 D35/D37/D42 source split to all PCB snapshots."""
from pathlib import Path
import pcbnew

ROOT = Path(__file__).resolve().parent
BOARDS = (
    ROOT / "juku.kicad_pcb",
    ROOT / "juku_routed.kicad_pcb",
    ROOT / "juku_routed_candidate.kicad_pcb",
)


def mm(point):
    return pcbnew.ToMM(point.x), pcbnew.ToMM(point.y)


def patch(path):
    board = pcbnew.LoadBoard(str(path))
    footprints = {fp.GetReference(): fp for fp in board.GetFootprints()}
    d35_4 = footprints["D35"].FindPadByNumber("4")
    d37_11 = footprints["D37"].FindPadByNumber("11")
    d37_12 = footprints["D37"].FindPadByNumber("12")
    d37_13 = footprints["D37"].FindPadByNumber("13")
    d42_10 = footprints["D42"].FindPadByNumber("10")
    old = (d35_4.GetNetname(), d37_11.GetNetname(), d37_12.GetNetname(),
           d37_13.GetNetname(), d42_10.GetNetname())
    expected = ("VID_MIX1", "VID_MIX1", "D42_Q", "D42_Q", "D42_Q")
    if old != expected:
        raise RuntimeError(f"{path.name}: unexpected pad nets {old}")
    new_net = board.FindNet("D37_I12_TAG3")
    if new_net is None:
        new_net = pcbnew.NETINFO_ITEM(board, "D37_I12_TAG3")
        board.Add(new_net)
    d35_4.SetNet(board.FindNet("D42_Q"))
    d37_12.SetNet(new_net)

    # The routed variants have one direct, false D37.13-to-D37.12 copper
    # bridge. The source PCB has no copper on these nets.
    removed = 0
    p12 = mm(d37_12.GetPosition())
    p13 = mm(d37_13.GetPosition())
    for track in list(board.GetTracks()):
        if track.GetNetname() != "D42_Q" or not isinstance(track, pcbnew.PCB_TRACK):
            continue
        ends = (mm(track.GetStart()), mm(track.GetEnd()))
        if set(ends) == {p12, p13}:
            board.Remove(track)
            removed += 1
    expected_removed = 0 if path.name == "juku.kicad_pcb" else 1
    if removed != expected_removed:
        raise RuntimeError(f"{path.name}: expected {expected_removed} direct bridge(s), found {removed}")
    pcbnew.SaveBoard(str(path), board)
    print(f"{path.name}: D35.4->D42_Q, D37.12->D37_I12_TAG3, removed {removed} bridge")


if __name__ == "__main__":
    for pcb in BOARDS:
        patch(pcb)
