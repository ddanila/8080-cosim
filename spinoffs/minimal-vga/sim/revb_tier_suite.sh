#!/usr/bin/env bash
# VJUGA rev B — B0 tier suite. One command that runs every B0-phase gate:
# shared-commons guard, per-card unit TBs, the bus-conflict assertion, and the
# assembled-backplane banner boot (byte-identical to cosim, both decode modes).
# Deeper tier suites (jmon33 / keyboard-react at B3, FDC/EKDOS at B4) attach here
# as those tiers come online.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"
. spinoffs/minimal-vga/kicad/revb/env.sh

# Hosted CI is a behavioral smoke gate, not a five-board manufacturing release.
# The default full suite below still requires Galette, KiCad and release tools.
case "${1:-full}" in
  --ci)
    python3 scripts/check_spinoff_commons.py
    python3 scripts/check_revb_boards.py --completeness
    python3 spinoffs/minimal-vga/roms/build_revb_rom.py --check
    spinoffs/minimal-vga/sim/revb_card_tb_check.sh
    spinoffs/minimal-vga/sim/revb_bus_assert_check.sh
    spinoffs/minimal-vga/sim/revb_bringup_check.sh
    spinoffs/minimal-vga/sim/revb_serial_console_check.sh
    spinoffs/minimal-vga/sim/revb_io_expansion_check.sh
    REVB_BOOT_PHASE=modes WRITES=1000 spinoffs/minimal-vga/sim/revb_rom_system_check.sh
    spinoffs/minimal-vga/sim/revb_video_check.sh
    echo "REVB-TIER-SUITE-CI: PASS (behavioral smoke; full release suite is local-only)"
    exit 0
    ;;
  full) ;;
  *) echo "usage: $0 [--ci]" >&2; exit 2 ;;
esac

echo "== rev B: shared-commons guard =="
python3 scripts/check_spinoff_commons.py

echo "== rev B: card connectivity specs + netlist completeness (T1.3-T1.6, D1.18) =="
python3 scripts/check_revb_boards.py --completeness

echo "== rev B: five reproducible GALs + physical 27C256 image (R5.P1/R5.V3) =="
spinoffs/minimal-vga/pld/revb/build_revb_gals.sh
python3 spinoffs/minimal-vga/roms/build_revb_rom.py --check

echo "== rev B: board-relative TTL serial continuity (R5.S1) =="
python3 spinoffs/minimal-vga/kicad/revb/check_revb_serial_contract.py

echo "== rev B: protected TTL levels + selectable baud clock (R5.S2) =="
python3 spinoffs/minimal-vga/kicad/revb/check_revb_serial_electrical.py

echo "== rev B: bidirectional 8251 console + C10 transaction (R5.S3) =="
spinoffs/minimal-vga/sim/revb_serial_console_check.sh

echo "== rev B: D57/POST contract and hardware twin (R5.I1/R5.I2) =="
spinoffs/minimal-vga/sim/revb_io_expansion_check.sh

echo "== rev B: expanded I/O GAL/netlist/pin closure (R5.I4) =="
spinoffs/minimal-vga/pld/revb/build_revb_gals.sh
python3 spinoffs/minimal-vga/kicad/revb/check_revb_io_board_expansion.py --self-test

echo "== rev B: reproducible EKTA/NETC10/DIAG 27C256 set (R5.I3) =="
python3 spinoffs/minimal-vga/roms/check_revb_rom_set.py

echo "== rev B: complete GOST-labelled routed I/O card (R5.I5) =="
if revb_have KICAD_PYTHON; then
  "$KICAD_PYTHON" spinoffs/minimal-vga/kicad/revb/check_revb_io_pcb.py --self-test
  python3 spinoffs/minimal-vga/kicad/revb/check_revb_drc.py io --total
else
  echo "  SKIP  R5.I5 physical gate: pcbnew not found"
fi

echo "== rev B: integrated three-ROM system and recovery modes (R5.I6) =="
spinoffs/minimal-vga/sim/revb_rom_system_check.sh

echo "== rev B: mechanical mating contract (TG.1/D1.31; pure python, no CAD tools) =="
python3 spinoffs/minimal-vga/kicad/revb/check_revb_mating.py

echo "== rev B: footprint package guards (D1.36 phys + DIP width; skips w/o KiCad libs) =="
for _c in mem io cpu backplane video; do
  python3 spinoffs/minimal-vga/kicad/revb/check_revb_footprints.py "$_c"
done
python3 spinoffs/minimal-vga/kicad/revb/check_revb_footprints.py video --self-test

echo "== rev B: exact Video purchasing/land-pattern contract (R5.V4) =="
python3 spinoffs/minimal-vga/kicad/revb/check_revb_video_parts.py --self-test

echo "== rev B: mem-card LVS (structural netlist vs board.json; skips w/o yosys) =="
spinoffs/minimal-vga/sync/revb_lvs.sh mem

echo "== rev B: io-card LVS (populated 8251 + GAL) =="
spinoffs/minimal-vga/sync/revb_lvs.sh io

echo "== rev B: video real-silicon/pin audit + full 23-package LVS (R5.V1/V3) =="
python3 spinoffs/minimal-vga/kicad/revb/check_revb_video_digital.py --self-test
spinoffs/minimal-vga/sync/revb_lvs.sh video
spinoffs/minimal-vga/sync/revb_video_lvs_mutation_check.sh

echo "== rev B: Video decoupling, RGB loads and five-card current (R5.V2) =="
python3 spinoffs/minimal-vga/kicad/revb/check_revb_video_power.py --self-test

echo "== rev B: routed Video stack/planes/geometry/critical paths (R5.V5) =="
if revb_have KICAD_PYTHON; then
  echo "== rev B: consistent GOST silkscreen and assembly/safety labels =="
  for _c in cpu mem io backplane video; do
    "$KICAD_PYTHON" spinoffs/minimal-vga/kicad/revb/check_revb_pcb.py "$_c"
  done
  "$KICAD_PYTHON" spinoffs/minimal-vga/kicad/revb/check_revb_video_pcb.py --self-test
  python3 spinoffs/minimal-vga/kicad/revb/check_revb_drc.py video --total
  echo "== rev B: assembled mechanics + protected five-board power path (R5.V6) =="
  "$KICAD_PYTHON" spinoffs/minimal-vga/kicad/revb/check_revb_system_physical.py --self-test
  python3 spinoffs/minimal-vga/kicad/revb/check_revb_drc.py backplane --total
  echo "== rev B: JLCPCB five-board geometry and archive profile (R5.J1) =="
  "$KICAD_PYTHON" spinoffs/minimal-vga/kicad/revb/check_revb_jlcpcb.py --self-test
else
  echo "  SKIP  R5.V5/R5.V6/R5.J1 physical gates: pcbnew not found"
fi

echo "== rev B: exact five-card requalification and release-source guards (R5.I7/J2/J3) =="
spinoffs/minimal-vga/kicad/revb/revb_i7_release_check.sh

echo "== rev B: hash-bound final release hold (R5.R1) =="
python3 spinoffs/minimal-vga/kicad/revb/check_revb_release_gate.py --self-test

echo "== rev B: per-card unit TBs (BFM) =="
spinoffs/minimal-vga/sim/revb_card_tb_check.sh

echo "== rev B: bus-conflict assertion =="
spinoffs/minimal-vga/sim/revb_bus_assert_check.sh

echo "== rev B: minimum-tier bring-up ROM TX stream == cosim (real 8251, no Video) =="
spinoffs/minimal-vga/sim/revb_bringup_check.sh

echo "== rev B: B2 video card (TTL twin: timing + crop + scanout + /WAIT) =="
spinoffs/minimal-vga/sim/revb_video_check.sh

echo "REVB-TIER-SUITE(B0+B1sim+B2video): PASS"
