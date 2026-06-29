#!/bin/sh
# Full LVS pipeline: regenerate the KiCad schematic from the board spec, export its
# netlist, elaborate the HDL, and diff connectivity. Exit non-zero on mismatch.
# Usage: sync/check.sh        (run from anywhere; uses repo root)
#   KICAD_CLI=/path/to/kicad-cli  to override the kicad-cli location.
set -e
cd "$(dirname "$0")/.."

# locate kicad-cli
if [ -n "$KICAD_CLI" ]; then :
elif command -v kicad-cli >/dev/null 2>&1; then KICAD_CLI=kicad-cli
elif [ -x "/opt/homebrew/Caskroom/kicad/10.0.4/KiCad/KiCad.app/Contents/MacOS/kicad-cli" ]; then
  KICAD_CLI="/opt/homebrew/Caskroom/kicad/10.0.4/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
else echo "kicad-cli not found (set KICAD_CLI)"; exit 2; fi

echo "==> board spec -> KiCad schematic"
python3 kicad/gen_kicad_sch.py kicad/juku.board.json kicad/juku.kicad_sch

echo "==> KiCad schematic -> netlist"
"$KICAD_CLI" sch export netlist --format kicadxml -o kicad/juku.net.xml kicad/juku.kicad_sch 2>/dev/null

echo "==> HDL -> netlist (yosys)"
yosys -q -p "read_verilog hdl/devices.v hdl/juku_top.v; hierarchy -top juku_top; write_json hdl/juku_top.json"

echo "==> LVS connectivity check"
python3 sync/lvs.py --hdl hdl/juku_top.json --kicad kicad/juku.net.xml --map sync/map.json

echo "==> provenance"
python3 sync/provenance.py kicad/juku.board.json | tail -2
