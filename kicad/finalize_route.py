#!/usr/bin/env python3
# Routing finalize: import a freerouting .ses into the generated board and set the copper-to-edge
# design rule to 0.3 mm (standard fab capability, e.g. JLC/PCBWay) -- freerouting hugs the outline
# and KiCad's 0.5 mm default flags those routes; relaxing to the documented fab limit keeps the
# router's copper untouched (moving it blindly creates shorts -- learned the hard way).
# Run with KiCad's python:  <kicad-python3> kicad/finalize_route.py <in.ses> <out.kicad_pcb>
import sys, pcbnew
SES, OUT = sys.argv[1], sys.argv[2]
b = pcbnew.LoadBoard("kicad/juku.kicad_pcb")
assert pcbnew.ImportSpecctraSES(b, SES), "SES import failed"
b.GetDesignSettings().m_CopperEdgeClearance = pcbnew.FromMM(0.3)
pcbnew.SaveBoard(OUT, b)
tracks = sum(1 for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK')
vias = sum(1 for t in b.GetTracks() if t.GetClass() == 'PCB_VIA')
print(f"imported {SES}: {tracks} tracks + {vias} vias; edge rule = 0.3mm -> {OUT}")
