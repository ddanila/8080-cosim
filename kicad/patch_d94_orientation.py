#!/usr/bin/python3
"""Correct the photo-proved D94 and D100 orientations/positions."""
import sys
import pcbnew

if len(sys.argv) != 3:
    raise SystemExit(f"usage: {sys.argv[0]} INPUT.kicad_pcb OUTPUT.kicad_pcb")

board = pcbnew.LoadBoard(sys.argv[1])
footprint = board.FindFootprintByReference("D94")
if footprint is None:
    raise SystemExit("D94 not found")
old = {pad.GetNumber(): pad.GetPosition() for pad in footprint.Pads()}
footprint.SetOrientationDegrees(90)
# The old placement used the DIP origin as if it were the body centre.  The
# package-local owner-photo fit proves the previous read was two pitches left;
# physical pin 1 is at board (229.275, 38.110) mm.
footprint.SetPosition(pcbnew.VECTOR2I_MM(229.275, 38.110))
for pad in sorted(footprint.Pads(), key=lambda item: int(item.GetNumber())):
    before, after = old[pad.GetNumber()], pad.GetPosition()
    print(pad.GetNumber(), f"{pcbnew.ToMM(before.x):.3f},{pcbnew.ToMM(before.y):.3f}",
          "->", f"{pcbnew.ToMM(after.x):.3f},{pcbnew.ToMM(after.y):.3f}")

d100 = board.FindFootprintByReference("D100")
if d100 is None:
    raise SystemExit("D100 not found")
old_d100 = {pad.GetNumber(): pad.GetPosition() for pad in d100.Pads()}
d100.SetOrientationDegrees(90)
d100.SetPosition(pcbnew.VECTOR2I_MM(257.65, 37.40))
for pad in sorted(d100.Pads(), key=lambda item: int(item.GetNumber())):
    before, after = old_d100[pad.GetNumber()], pad.GetPosition()
    print("D100." + pad.GetNumber(), f"{pcbnew.ToMM(before.x):.3f},{pcbnew.ToMM(before.y):.3f}",
          "->", f"{pcbnew.ToMM(after.x):.3f},{pcbnew.ToMM(after.y):.3f}")
pcbnew.SaveBoard(sys.argv[2], board)
