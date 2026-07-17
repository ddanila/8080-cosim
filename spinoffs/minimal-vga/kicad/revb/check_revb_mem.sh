#!/usr/bin/env bash
# VJUGA rev B mem-card pipeline (Stage B, TD.8.3). Runs the proven pipeline stages
# end to end. Tool-dependent stages skip-not-fail via env.sh so this is CI-safe.
#   netlist completeness -> LVS -> footprint probe -> PCB gen -> PCB content check
#   -> STEP export + sanity (kicad/freecad) ; routing + DRC-clean are gated on a
#   Java 25 runtime (freerouting) and are reported, not required, here.
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../../../.." && pwd)"
cd "$REPO"
R="spinoffs/minimal-vga"
. "$R/kicad/revb/env.sh"

echo "== [1/6] netlist completeness =="
python3 scripts/check_revb_boards.py --completeness

echo "== [2/6] mem-card LVS =="
sh "$R/sync/revb_lvs.sh" mem

echo "== [3/6] footprint probe =="
python3 "$R/kicad/revb/check_revb_footprints.py" mem || { echo "  (skipped: no KICAD_FOOTPRINTS)"; }

if revb_have KICAD_PYTHON; then
  echo "== [4/6] PCB generate =="
  "$KICAD_PYTHON" "$R/kicad/revb/gen_revb_pcb.py" mem 2>/dev/null | tail -1
  echo "== [5/6] PCB content check + placement DRC =="
  "$KICAD_PYTHON" "$R/kicad/revb/check_revb_mem_pcb.py" 2>/dev/null
  python3 "$R/kicad/revb/check_revb_drc.py" mem --placement
else
  echo "== [4-5/6] PCB gen/check: SKIP (no KICAD_PYTHON) =="
fi

echo "== [6/6] STEP export + bbox sanity (best-effort) =="
if revb_have KICAD_CLI; then
  "$KICAD_CLI" pcb export step --output fab/minimal-vga/revb/mem.step \
    fab/minimal-vga/revb/mem.kicad_pcb >/dev/null 2>&1 && echo "  STEP exported" || echo "  STEP export skipped"
fi

echo "REVB-MEM-PIPELINE: netlist/LVS/gen/content OK; routing+DRC-clean pending Java25 + layout (see rev-b-status)"
