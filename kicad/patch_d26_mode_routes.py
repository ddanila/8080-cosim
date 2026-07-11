#!/usr/bin/env python3
"""Prepare the routed PCB for the corrected D26 PC2/3/4 mode wiring.

Copies only affected pad-net assignments from the regenerated source PCB and
removes copper belonging to the superseded mode nets. All unrelated routed
copper is retained so Freerouting can solve a small incremental ratsnest.
"""
import sys
import pcbnew

if len(sys.argv) not in (4, 5):
    raise SystemExit("usage: patch_d26_mode_routes.py SOURCE.kicad_pcb ROUTED.kicad_pcb OUT.kicad_pcb [controls|video-counters|d103]")

source = pcbnew.LoadBoard(sys.argv[1])
board = pcbnew.LoadBoard(sys.argv[2])

if len(sys.argv) == 5 and sys.argv[4] == "controls":
    affected = {"D1": {"13", "16", "24"}, "D4": {"9", "11"}, "D5": {"22"}, "D107": {"9", "11"}}
    old_nets = set()
elif len(sys.argv) == 5 and sys.argv[4] == "video-counters":
    affected = {"D44": {"4", "13", "14"}, "D45": {"4", "13", "14"},
                "D46": {"13"}, "D47": {"12", "13"}}
    old_nets = set()
elif len(sys.argv) == 5 and sys.argv[4] == "d103":
    affected = {"D103": {"1", "3", "4", "5", "6", "7", "10", "12", "13", "14"}}
    old_nets = set()
else:
    affected = {
        "D26": {"10", "11", "12", "13", "14", "15", "16", "17", "39"},
        "D6": {"1", "2", "15"},
        "D93": {"37"},
    }
    old_nets = {"MEM_MODE0", "MEM_MODE1", "MEM_MODE2", "FDC_DDEN"}

# Remove complete old-net route trees. Keeping a branch would retain the old
# physical short even after its endpoint pad changes net.
removed = 0
for track in list(board.GetTracks()):
    if track.GetNetname() in old_nets:
        # Delete (rather than Remove) keeps the SWIG wrapper from taking C++
        # ownership of dozens of detached tracks and double-freeing at exit.
        board.Delete(track); removed += 1

# Ensure every desired new net exists in the destination, then copy assignments.
for ref, pins in affected.items():
    src_fp = source.FindFootprintByReference(ref)
    dst_fp = board.FindFootprintByReference(ref)
    if not src_fp or not dst_fp:
        raise SystemExit(f"missing affected footprint {ref}")
    for pin in pins:
        src_pad = src_fp.FindPadByNumber(pin); dst_pad = dst_fp.FindPadByNumber(pin)
        if not src_pad or not dst_pad:
            raise SystemExit(f"missing affected pad {ref}.{pin}")
        name = src_pad.GetNetname()
        if name:
            net = board.FindNet(name)
            if not net:
                net = pcbnew.NETINFO_ITEM(board, name); board.Add(net)
            dst_pad.SetNet(net)
        else:
            dst_pad.SetNetCode(0)

board.BuildListOfNets()
pcbnew.SaveBoard(sys.argv[3], board)
mode = sys.argv[4] if len(sys.argv) == 5 else "D26"
print(f"prepared incremental {mode} reroute: removed {removed} old tracks/vias -> {sys.argv[3]}")
