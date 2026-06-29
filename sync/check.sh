#!/bin/sh
# LVS pipeline. HDL -> yosys netlist; board spec -> connectivity; diff.
# If kicad-cli is present (and matches our schematic format), it does the real
# KiCad round-trip (board -> schematic -> kicad-cli netlist). Otherwise it falls
# back to reading the board spec directly (same connectivity, no KiCad needed) --
# this keeps CI robust against KiCad version drift.
# Exit non-zero on mismatch.  KICAD_CLI=/path overrides kicad-cli location.
set -e
cd "$(dirname "$0")/.."

KCLI=""
if [ -n "$KICAD_CLI" ] && [ -x "$KICAD_CLI" ]; then KCLI="$KICAD_CLI"
elif command -v kicad-cli >/dev/null 2>&1; then KCLI="kicad-cli"
elif [ -x "/opt/homebrew/Caskroom/kicad/10.0.4/KiCad/KiCad.app/Contents/MacOS/kicad-cli" ]; then
  KCLI="/opt/homebrew/Caskroom/kicad/10.0.4/KiCad/KiCad.app/Contents/MacOS/kicad-cli"; fi

echo "==> board spec -> KiCad schematic"
python3 kicad/gen_kicad_sch.py kicad/juku.board.json kicad/juku.kicad_sch

echo "==> HDL -> netlist (yosys)"
yosys -q -p "read_verilog hdl/devices.v hdl/juku_top.v; hierarchy -top juku_top; write_json hdl/juku_top.json"

if [ -n "$KCLI" ] && "$KCLI" sch export netlist --format kicadxml -o kicad/juku.net.xml kicad/juku.kicad_sch 2>/dev/null; then
  echo "==> LVS (real KiCad round-trip via $KCLI)"
  python3 sync/lvs.py --hdl hdl/juku_top.json --kicad kicad/juku.net.xml --map sync/map.json
else
  echo "==> LVS (KiCad-free, board spec direct -- kicad-cli absent/incompatible)"
  python3 sync/lvs.py --hdl hdl/juku_top.json --board kicad/juku.board.json --map sync/map.json
fi

echo "==> provenance"
python3 sync/provenance.py kicad/juku.board.json | tail -2
