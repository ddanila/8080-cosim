#!/usr/bin/env python3
# Routing finalize: import a freerouting .ses into the generated board and set the copper-to-edge
# design rule to 0.3 mm (standard fab capability, e.g. JLC/PCBWay) -- freerouting hugs the outline
# and KiCad's 0.5 mm default flags those routes; relaxing to the documented fab limit keeps the
# router's copper untouched (moving it blindly creates shorts -- learned the hard way).
#
# SES sanitize (FALLBACK ONLY): when the board carries pre-route wires, freerouting echoes them
# back in the SES as "(wire ... (type protect))" blocks. Some of those echoes (seen with the old
# DB5/DB6 bottom-band bars) make pcbnew.ImportSpecctraSES() return False with no diagnostics.
# We first import raw -- a healthy echo is WANTED, because the import wipes the wiring of every
# net listed in the session (pre-route bars included) and the echo is what restores them. Only if
# the raw import fails do we strip the protect echoes and retry; after such a fallback any
# pre-routed net in the session has lost its bars, and if the router T-junctioned into a bar the
# net splits into islands -- re-inject the bars post-import (learned on or3: 46 unconnected).
# Run with KiCad's python:  <kicad-python3> kicad/finalize_route.py <in.ses> <out.kicad_pcb>
import sys, os, pcbnew

SES, OUT = sys.argv[1], sys.argv[2]


def strip_protect_wires(text):
    """Drop every (wire ...) block that carries (type protect). Returns (text, count)."""
    def block_end(s, start):
        depth = 0
        for j in range(start, len(s)):
            if s[j] == '(':
                depth += 1
            elif s[j] == ')':
                depth -= 1
                if depth == 0:
                    return j + 1
        return len(s)

    out, k, dropped = [], 0, 0
    while True:
        w = text.find('(wire', k)
        if w < 0:
            out.append(text[k:])
            break
        we = block_end(text, w)
        out.append(text[k:w])
        if '(type protect)' in text[w:we]:
            dropped += 1
        else:
            out.append(text[w:we])
        k = we
    return ''.join(out), dropped


BOARD = os.path.join(os.path.dirname(__file__), "juku.kicad_pcb")
b = pcbnew.LoadBoard(BOARD)
if not pcbnew.ImportSpecctraSES(b, SES):
    clean, dropped = strip_protect_wires(open(SES).read())
    assert dropped, "SES import failed and no protect-wire echoes to strip"
    SES_CLEAN = SES + '.clean'
    open(SES_CLEAN, 'w').write(clean)
    print(f"raw import failed; retrying with {dropped} protect-wire echo(es) stripped "
          f"(pre-routed nets may need bar re-injection -- check DRC unconnected!)")
    b = pcbnew.LoadBoard(BOARD)  # fresh board -- the failed import may have half-applied
    assert pcbnew.ImportSpecctraSES(b, SES_CLEAN), "SES import failed even after sanitize"
b.GetDesignSettings().m_CopperEdgeClearance = pcbnew.FromMM(0.3)
pcbnew.SaveBoard(OUT, b)
tracks = sum(1 for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK')
vias = sum(1 for t in b.GetTracks() if t.GetClass() == 'PCB_VIA')
print(f"imported {SES}: {tracks} tracks + {vias} vias; edge rule = 0.3mm -> {OUT}")
