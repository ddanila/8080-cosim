#!/usr/bin/env bash
# VJUGA rev B — B0 tier suite. One command that runs every B0-phase gate:
# shared-commons guard, per-card unit TBs, the bus-conflict assertion, and the
# assembled-backplane banner boot (byte-identical to cosim, both decode modes).
# Deeper tier suites (jmon33 / keyboard-react at B3, FDC/EKDOS at B4) attach here
# as those tiers come online.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"

echo "== rev B: shared-commons guard =="
python3 scripts/check_spinoff_commons.py

echo "== rev B: card connectivity specs + netlist completeness (T1.3-T1.6, D1.18) =="
python3 scripts/check_revb_boards.py --completeness

echo "== rev B: mechanical mating contract (TG.1/D1.31; pure python, no CAD tools) =="
python3 spinoffs/minimal-vga/kicad/revb/check_revb_mating.py

echo "== rev B: footprint package guards (D1.36 phys + DIP width; skips w/o KiCad libs) =="
for _c in mem io cpu backplane; do
  python3 spinoffs/minimal-vga/kicad/revb/check_revb_footprints.py "$_c"
done

echo "== rev B: mem-card LVS (structural netlist vs board.json; skips w/o yosys) =="
spinoffs/minimal-vga/sync/revb_lvs.sh mem

echo "== rev B: io-card LVS (populated 8251 + GAL) =="
spinoffs/minimal-vga/sync/revb_lvs.sh io

echo "== rev B: video-card LVS (3 decode/control GALs + framebuffer SRAM; B2) =="
spinoffs/minimal-vga/sync/revb_lvs.sh video

echo "== rev B: per-card unit TBs (BFM) =="
spinoffs/minimal-vga/sim/revb_card_tb_check.sh

echo "== rev B: bus-conflict assertion =="
spinoffs/minimal-vga/sim/revb_bus_assert_check.sh

echo "== rev B: modular backplane boots ekta37 byte-identical to cosim (banner) =="
spinoffs/minimal-vga/sim/revb_boot_check.sh

echo "== rev B: minimum-tier bring-up ROM TX stream == cosim (real 8251, no Video) =="
spinoffs/minimal-vga/sim/revb_bringup_check.sh

echo "== rev B: B2 video card (TTL twin: timing + crop + scanout + /WAIT) =="
spinoffs/minimal-vga/sim/revb_video_check.sh

echo "REVB-TIER-SUITE(B0+B1sim+B2video): PASS"
