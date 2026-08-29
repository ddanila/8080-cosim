#!/usr/bin/env bash
# R5.I7 desk requalification after the expanded D57/POST I/O card.
# This validates routed sources and release guards, but never grants upload/order
# authorization and does not require the still-stale R5.J2 fabrication archives.
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../../../.." && pwd)"
cd "$REPO"
. spinoffs/minimal-vga/kicad/revb/env.sh

echo "== R5.I7 exact expanded-I/O parts and BOM =="
python3 spinoffs/minimal-vga/kicad/revb/check_revb_io_parts.py --self-test
python3 spinoffs/minimal-vga/kicad/revb/review_revb_release.py --bom-only --self-test

echo "== R5.I7 current and RGB budget =="
python3 spinoffs/minimal-vga/kicad/revb/check_revb_video_power.py --self-test

echo "== R5.I7 package and assembly contracts =="
for card in mem io cpu backplane video; do
  python3 spinoffs/minimal-vga/kicad/revb/check_revb_footprints.py "$card"
done
python3 spinoffs/minimal-vga/kicad/revb/check_revb_footprints.py video --self-test

if revb_have KICAD_PYTHON; then
  "$KICAD_PYTHON" spinoffs/minimal-vga/kicad/revb/check_revb_io_pcb.py --self-test
  "$KICAD_PYTHON" spinoffs/minimal-vga/kicad/revb/check_revb_system_physical.py --self-test
  for card in cpu mem io backplane video; do
    "$KICAD_PYTHON" spinoffs/minimal-vga/kicad/revb/check_revb_pcb.py "$card"
    python3 spinoffs/minimal-vga/kicad/revb/check_revb_drc.py "$card" --total
  done
  "$KICAD_PYTHON" spinoffs/minimal-vga/kicad/revb/check_revb_jlcpcb.py --self-test
else
  echo "R5.I7 FAIL: pcbnew is required for the release-source physical gates"
  exit 1
fi

echo "== R5.I7 stale-package and unauthorized-release negative controls =="
python3 spinoffs/minimal-vga/kicad/revb/check_revb_release_gate.py --self-test-only

echo "R5.I7 RELEASE-SOURCE REQUALIFICATION: PASS / ORDER HOLD"
