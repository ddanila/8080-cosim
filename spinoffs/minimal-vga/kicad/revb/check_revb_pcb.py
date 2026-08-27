#!/usr/bin/env python3
"""Content-check a generated rev B card PCB (TD.7.3, generalized for TD.9+).
  KICAD_PYTHON check_revb_pcb.py <card>
pcbnew emits UUIDs so byte-diff is meaningless (D1.25); this verifies outline size,
every board.json ref placed, the bus connector on the bottom edge, and the silk.
Skips if pcbnew is unavailable.
"""
import json, os, sys
try:
    import pcbnew
except Exception:
    print("  SKIP  PCB content check: pcbnew not importable"); sys.exit(0)

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, HERE)
from revb_place import BOARD_H_BY_CARD  # noqa: E402

CARD = sys.argv[1] if len(sys.argv) > 1 else "mem"
if CARD not in BOARD_H_BY_CARD:
    print(f"PCB content check FAILED:\n- unsupported card {CARD!r}")
    sys.exit(1)
BOARD_H = BOARD_H_BY_CARD[CARD]
BOARD_W, TOL = 100.0, 0.4
PCB = os.path.join(REPO, "fab", "minimal-vga", "revb", f"{CARD}.kicad_pcb")

fail = []
if not os.path.isfile(PCB):
    print(f"{CARD} PCB content check FAILED:\n- missing {PCB}"); sys.exit(1)
b = pcbnew.LoadBoard(PCB)
fps = {f.GetReference(): f for f in b.GetFootprints()}

bb = b.GetBoardEdgesBoundingBox()
w, h = pcbnew.ToMM(bb.GetWidth()), pcbnew.ToMM(bb.GetHeight())
if abs(w - BOARD_W) > TOL or abs(h - BOARD_H) > TOL:
    fail.append(f"outline {w:.2f}x{h:.2f} != {BOARD_W}x{BOARD_H} (+-{TOL})")

spec = json.load(open(os.path.join(HERE, f"{CARD}.board.json")))
expected = set()
for c in spec["chips"]:
    if c["type"] == "REVB_BUS_39_10":
        if c["ref"] == "J_BUS":
            expected |= {"J_BUS", "J_EXT"}
        else:
            expected |= {f"{c['ref']}_BUS", f"{c['ref']}_EXT"}
    else:
        expected.add(c["ref"])
missing = expected - set(fps)
if missing:
    fail.append(f"refs not placed: {sorted(missing)}")

if "J_BUS" in fps:
    y = pcbnew.ToMM(fps["J_BUS"].GetPosition().y)
    if y < BOARD_H * 0.75:
        fail.append(f"J_BUS at y={y:.1f} not on the bottom edge")

txt = "".join(d.GetText() for d in b.GetDrawings() if d.GetClass() == "PCB_TEXT")
silk_required = (("REVB", "TTL ONLY", "NOT RS-232", "1:5V SENSE", "2:TX 3:RX 4:GND")
                 if CARD == "backplane" else ("REVB", "NO HOT-PLUG"))
for need in silk_required:
    if need not in txt:
        fail.append(f"silk missing {need!r}")

if fail:
    print(f"{CARD} PCB content check FAILED:")
    for f in fail:
        print(f"- {f}")
    sys.exit(1)
print(f"{CARD} PCB content check OK: {w:.1f}x{h:.1f} mm, {len(fps)} footprints placed, silk present.")
