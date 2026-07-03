#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../../.."

SCH="spinoffs/minimal-vga/kicad/minimal-vga.kicad_sch"
NET="spinoffs/minimal-vga/kicad/minimal-vga.net.xml"
JSON="spinoffs/minimal-vga/hdl/minimal_vga_lvs.json"

echo "==> minimal-vga board spec -> KiCad schematic"
python3 kicad/gen_kicad_sch.py spinoffs/minimal-vga/kicad/minimal-vga.board.json "$SCH"

echo "==> minimal-vga HDL -> netlist"
yosys -q -p "read_verilog -lib spinoffs/minimal-vga/hdl/minimal_vga_lvs.v; read_verilog spinoffs/minimal-vga/hdl/minimal_vga_lvs.v; hierarchy -top minimal_vga_lvs_top; write_json $JSON"

if kicad-cli sch export netlist --format kicadxml -o "$NET" "$SCH" >/dev/null 2>&1; then
  echo "==> minimal-vga LVS (real KiCad round-trip)"
  python3 sync/lvs.py --hdl "$JSON" --kicad "$NET" --map spinoffs/minimal-vga/sync/map.json
else
  echo "==> minimal-vga LVS (board spec fallback)"
  python3 sync/lvs.py --hdl "$JSON" --board spinoffs/minimal-vga/kicad/minimal-vga.board.json --map spinoffs/minimal-vga/sync/map.json
fi
