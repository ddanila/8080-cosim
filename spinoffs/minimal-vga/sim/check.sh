#!/usr/bin/env bash
# Spin-off simulation shim. For now this runs the existing project oracles that
# prove the ROM/RAM/keyboard-capable core still boots. A spin-off HDL top should
# be added here once `../hdl/` contains it.
set -euo pipefail

cd "$(dirname "$0")/../../.."

echo "== VJUGA spin-off: existing boot oracle =="
sync/boot_check.sh

echo "== VJUGA spin-off: T80 smoke test =="
spinoffs/minimal-vga/sim/check_t80_smoke.sh

echo "== VJUGA spin-off: real Juku ekta37 ROM boots on the VJUGA top (Z80, VHDL) =="
spinoffs/minimal-vga/sim/boot_check.sh

echo "== VJUGA spin-off: Verilog twin boots ekta37 on tv80 + real К565РУ5 =="
spinoffs/minimal-vga/sim/vjuga_boot_check.sh

echo "== VJUGA spin-off: Phase 4 framebuffer-readback tool validated vs twin + cosim =="
spinoffs/minimal-vga/sim/vjuga_readback_check.sh

echo "== VJUGA spin-off: schematic/HDL LVS =="
spinoffs/minimal-vga/sync/check.sh

echo "== VJUGA spin-off: Rev A physical schematic target =="
spinoffs/minimal-vga/kicad/check_rev_a_physical.sh

echo "== VJUGA spin-off: Rev A PCB scaffold =="
spinoffs/minimal-vga/kicad/check_rev_a_pcb.sh

echo "== VJUGA spin-off: Rev A silk/placement collision check =="
spinoffs/minimal-vga/kicad/check_rev_a_placement.sh

echo "== VJUGA spin-off: Rev A footprint-vs-model check =="
spinoffs/minimal-vga/kicad/check_rev_a_footprints.sh

echo "== VJUGA spin-off: Rev A fabrication readiness report =="
spinoffs/minimal-vga/kicad/report_rev_a_fab_readiness.sh

echo "== VJUGA spin-off: DRAM row/column unit =="
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
iverilog -g2012 -o "$tmp/dram_unit_tb" hdl/sim/dram_unit_tb.v
vvp "$tmp/dram_unit_tb"
