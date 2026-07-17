#!/usr/bin/env python3
"""DRC gate for a rev B card PCB (D1.27). Runs kicad-cli pcb drc and classifies:
  --placement : fail only on placement-class violations (courtyards, clearances,
                silk, holes, shorts); unconnected items are ignored (pre-routing gate).
  --total     : fail on ANY violation AND any unconnected item (post-routing gate).
Skips if kicad-cli is unavailable. Usage: check_revb_drc.py <card> [--placement|--total]
"""
import json, os, subprocess, sys, tempfile
from collections import Counter

CARD = sys.argv[1] if len(sys.argv) > 1 else "mem"
MODE = "--total" if "--total" in sys.argv else "--placement"
KCLI = os.environ.get("KICAD_CLI", "")
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
PCB = os.path.join(REPO, "fab", "minimal-vga", "revb", f"{CARD}.kicad_pcb")

PLACEMENT = {"courtyards_overlap", "pth_inside_courtyard", "clearance", "shorting_items",
             "solder_mask_bridge", "silk_over_copper", "silk_edge_clearance", "silk_overlap",
             "copper_edge_clearance", "hole_to_hole", "footprint_courtyard", "track_dangling"}

if not KCLI or not os.path.exists(PCB):
    print(f"  SKIP  DRC ({CARD}): kicad-cli or PCB unavailable"); sys.exit(0)

with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
    rep = tf.name
subprocess.run([KCLI, "pcb", "drc", "--format", "json", "--output", rep, PCB],
               capture_output=True)
d = json.load(open(rep)); os.unlink(rep)
viol = d.get("violations", []); unconn = d.get("unconnected_items", [])
c = Counter(v["type"] for v in viol)
place = sum(n for t, n in c.items() if t in PLACEMENT)

if MODE == "--total":
    ok = (len(viol) == 0 and len(unconn) == 0)
    print(f"DRC total ({CARD}): {len(viol)} violations, {len(unconn)} unconnected -> {'PASS' if ok else 'FAIL'}")
else:
    ok = (place == 0)
    print(f"DRC placement ({CARD}): {place} placement-class ({len(unconn)} unconnected ignored) -> {'PASS' if ok else 'FAIL'}")
if not ok:
    for t, n in c.most_common():
        print(f"    {n:3d} {t}")
    sys.exit(1)
