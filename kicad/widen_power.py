#!/usr/bin/env python3
# STATUS: WIP -- PARKED. The widen->DRC->narrow cycle works in principle but this script's DRC
# violation COUNTING disagrees with manual kicad-cli runs (claims a 164-violation baseline on a
# board that greps clean; isolation showed the committed board is clean and a pure pcbnew
# load/save round-trip stays clean). Do NOT trust its numbers until the counter is fixed; it may
# also leave the board with mixed widths -- restore kicad/juku_routed.kicad_pcb from git after
# experiments. Correct next approach: pre-check widening geometrically (distance to nearest
# copper) instead of DRC round-trips.
# Widen power-net tracks where space allows (the original board uses thick power runs).
# One clean cycle: reset -> widen all -> DRC -> narrow every power segment near ANY clearance
# violation (either party's coordinates) -> verify DRC returns to baseline-clean.
import sys, subprocess, re, pcbnew
BOARD = sys.argv[1]
POWER = {'GND','P5V','P12V','M12V','M5V_DERIVED'}
WIDE, NARROW = pcbnew.FromMM(0.4), pcbnew.FromMM(0.25)
KCLI = "/opt/homebrew/Caskroom/kicad/10.0.4/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
def drc():
    subprocess.run([KCLI,"pcb","drc","-o","/tmp/wp-drc.rpt",BOARD],capture_output=True)
    txt=open("/tmp/wp-drc.rpt").read()
    viol=len(re.findall(r'\[(?:clearance|shorting_items|hole_clearance|solder_mask_bridge)\]',txt))
    pts=set()
    for block in re.split(r'\n(?=\[)',txt):
        if re.match(r'\[(?:clearance|shorting_items|hole_clearance|solder_mask_bridge)\]',block):
            for m in re.finditer(r'@\((\d+\.\d+) mm, (\d+\.\d+) mm\)',block):
                pts.add((float(m.group(1)),float(m.group(2))))
    return viol,pts
b=pcbnew.LoadBoard(BOARD)
for t in b.GetTracks():
    if t.GetClass()=='PCB_TRACK' and t.GetNetname() in POWER: t.SetWidth(NARROW)
pcbnew.SaveBoard(BOARD,b)
v0,_=drc(); print("baseline violations:",v0)
b=pcbnew.LoadBoard(BOARD); w=0
for t in b.GetTracks():
    if t.GetClass()=='PCB_TRACK' and t.GetNetname() in POWER: t.SetWidth(WIDE); w+=1
pcbnew.SaveBoard(BOARD,b)
v1,pts=drc(); print(f"widened {w}; violations now {v1}, points {len(pts)}")
T=pcbnew.ToMM
def d2seg(px,py,x1,y1,x2,y2):
    dx,dy=x2-x1,y2-y1; L2=dx*dx+dy*dy
    tt=0 if L2==0 else max(0,min(1,((px-x1)*dx+(py-y1)*dy)/L2))
    return ((px-(x1+tt*dx))**2+(py-(y1+tt*dy))**2)**0.5
b=pcbnew.LoadBoard(BOARD); n=0
for t in b.GetTracks():
    if t.GetClass()=='PCB_TRACK' and t.GetNetname() in POWER and t.GetWidth()==WIDE:
        s_,e_=t.GetStart(),t.GetEnd()
        x1,y1,x2,y2=T(s_.x),T(s_.y),T(e_.x),T(e_.y)
        if any(d2seg(px,py,x1,y1,x2,y2)<1.5 for (px,py) in pts): t.SetWidth(NARROW); n+=1
pcbnew.SaveBoard(BOARD,b)
v2,_=drc(); print(f"narrowed {n} near violations; final violations {v2} (target {v0})")
