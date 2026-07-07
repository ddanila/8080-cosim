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
if [ -n "$KICAD_CLI" ]; then
  if [ -x "$KICAD_CLI" ] || command -v "$KICAD_CLI" >/dev/null 2>&1; then
    KCLI="$KICAD_CLI"
  fi
elif command -v kicad-cli-nightly >/dev/null 2>&1; then
  KCLI="$(command -v kicad-cli-nightly)"
elif command -v kicad-cli >/dev/null 2>&1; then
  KCLI="$(command -v kicad-cli)"
else
  for candidate in \
    /Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli \
    /Applications/KiCad/kicad-cli \
    /opt/homebrew/Caskroom/kicad/*/KiCad/KiCad.app/Contents/MacOS/kicad-cli \
    /usr/local/Caskroom/kicad/*/KiCad/KiCad.app/Contents/MacOS/kicad-cli
  do
    if [ -x "$candidate" ]; then KCLI="$candidate"; break; fi
  done
fi

echo "==> board spec -> KiCad schematic"
python3 kicad/gen_kicad_sch.py kicad/juku.board.json kicad/juku.kicad_sch

echo "==> HDL -> netlist (yosys)"
# LVS compares CONNECTIVITY, not chip internals. Read devices.v as a -lib (blackbox: ports only),
# so yosys keeps the chips as cells and doesn't try to resolve their now-functional tri-state
# bodies (which its "limited tri-state support" mis-merges). juku_top is pure structure (instances
# + wires) -> the instance/pin connectivity the LVS needs is preserved exactly.
yosys -q -p "read_verilog -lib hdl/devices.v; read_verilog hdl/juku_top.v; hierarchy -top juku_top; write_json hdl/juku_top.json"

if [ -n "$KCLI" ] && "$KCLI" sch export netlist --format kicadxml -o kicad/juku.net.xml kicad/juku.kicad_sch 2>/dev/null; then
  echo "==> LVS (real KiCad round-trip via $KCLI)"
  python3 sync/lvs.py --hdl hdl/juku_top.json --kicad kicad/juku.net.xml --map sync/map.json
else
  echo "==> LVS (KiCad-free, board spec direct -- kicad-cli absent/incompatible)"
  python3 sync/lvs.py --hdl hdl/juku_top.json --board kicad/juku.board.json --map sync/map.json
fi

echo "==> provenance"
python3 sync/provenance.py kicad/juku.board.json | tail -2
