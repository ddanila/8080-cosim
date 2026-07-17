#!/usr/bin/env python3
"""Content-check the generated mem-card PCB (TD.7.3, pattern: check_rev_a_pcb.py).
Run with KICAD_PYTHON. pcbnew emits UUIDs so byte-diff is meaningless (D1.25); this
verifies WHAT matters: outline size, every board.json ref placed, the bus connector
on the bottom edge, and the required silk. Skips if pcbnew is unavailable.
"""
import json, os, sys
try:
    import pcbnew
except Exception:
    print("  SKIP  mem PCB content check: pcbnew not importable"); sys.exit(0)

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
PCB = os.path.join(REPO, "fab", "minimal-vga", "revb", "mem.kicad_pcb")
BOARD_W, BOARD_H, TOL = 100.0, 60.0, 0.4

fail = []
if not os.path.isfile(PCB):
    print(f"mem PCB content check FAILED:\n- missing {PCB}"); sys.exit(1)

b = pcbnew.LoadBoard(PCB)
fps = {f.GetReference(): f for f in b.GetFootprints()}

# 1) outline size
bb = b.GetBoardEdgesBoundingBox()
w, h = pcbnew.ToMM(bb.GetWidth()), pcbnew.ToMM(bb.GetHeight())
if abs(w - BOARD_W) > TOL or abs(h - BOARD_H) > TOL:
    fail.append(f"outline {w:.2f}x{h:.2f} != {BOARD_W}x{BOARD_H} (+-{TOL})")

# 2) every board.json ref placed (bus connector -> J_BUS + J_EXT)
spec = json.load(open(os.path.join(HERE, "mem.board.json")))
expected = set()
for c in spec["chips"]:
    expected |= {"J_BUS", "J_EXT"} if c["type"] == "REVB_BUS_39_10" else {c["ref"]}
missing = expected - set(fps)
if missing:
    fail.append(f"refs not placed: {sorted(missing)}")

# 3) bus base connector on the bottom edge (y in the lower quarter)
if "J_BUS" in fps:
    y = pcbnew.ToMM(fps["J_BUS"].GetPosition().y)
    if y < BOARD_H * 0.75:
        fail.append(f"J_BUS at y={y:.1f} not on the bottom edge")

# 4) required silk present
txt = "".join(d.GetText() for d in b.GetDrawings() if d.GetClass() == "PCB_TEXT")
for need in ("REVB", "NO HOT-PLUG"):
    if need not in txt:
        fail.append(f"silk missing {need!r}")

# 5) footprints carry a pad 1 (pin-1 provenance)
if "U1" in fps and not any(str(p.GetNumber()) == "1" for p in fps["U1"].Pads()):
    fail.append("U1 has no pad 1")

if fail:
    print("mem PCB content check FAILED:")
    for f in fail:
        print(f"- {f}")
    sys.exit(1)
print(f"mem PCB content check OK: {w:.1f}x{h:.1f} mm, {len(fps)} footprints placed, silk present.")
