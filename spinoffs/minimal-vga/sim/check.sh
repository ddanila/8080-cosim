#!/usr/bin/env bash
# Spin-off simulation shim. For now this runs the existing project oracles that
# prove the ROM/RAM/keyboard-capable core still boots. A spin-off HDL top should
# be added here once `../hdl/` contains it.
set -euo pipefail

cd "$(dirname "$0")/../../.."

echo "== minimal-vga spin-off: existing boot oracle =="
sync/boot_check.sh

echo "== minimal-vga spin-off: T80 smoke test =="
spinoffs/minimal-vga/sim/check_t80_smoke.sh

echo "== minimal-vga spin-off: schematic/HDL LVS =="
spinoffs/minimal-vga/sync/check.sh

echo "== minimal-vga spin-off: DRAM row/column unit =="
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
iverilog -g2012 -o "$tmp/dram_unit_tb" hdl/sim/dram_unit_tb.v
vvp "$tmp/dram_unit_tb"
