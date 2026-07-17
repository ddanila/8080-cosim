#!/usr/bin/env bash
# VJUGA rev B per-card LVS (TD.6.3). Compares the independently-authored structural
# netlist (hdl/revb/revb_<card>_lvs.v) against the generated <card>.board.json via
# the generated pinmap (sync/revb_<card>_map.json). Board-direct path (yosys +
# sync/lvs.py --board) is the gate and the CI path; the kicad-cli schematic
# round-trip is a future bonus. Skips (not fails) when yosys is absent.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"      # spinoffs/minimal-vga
REPO="$(cd "$ROOT/../.." && pwd)"
cd "$REPO"

CARD="${1:-mem}"
command -v yosys >/dev/null 2>&1 || { echo "  SKIP  rev B LVS ($CARD): yosys not found"; exit 0; }

MAPGEN="$ROOT/kicad/revb/gen_revb_lvs_map.py"
LVSV="$ROOT/hdl/revb/revb_${CARD}_lvs.v"
BOARD="$ROOT/kicad/revb/${CARD}.board.json"
MAP="$ROOT/sync/revb_${CARD}_map.json"
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT

echo "== rev B LVS: $CARD =="
python3 "$MAPGEN" >/dev/null                     # regen map from the board generator (single source)
yosys -q -p "read_verilog -lib $LVSV; read_verilog $LVSV; hierarchy -top revb_${CARD}_lvs_top; write_json $TMP/lvs.json"
python3 sync/lvs.py --hdl "$TMP/lvs.json" --board "$BOARD" --map "$MAP"
