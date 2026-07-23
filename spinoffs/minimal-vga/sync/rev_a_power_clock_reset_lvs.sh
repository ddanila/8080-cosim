#!/usr/bin/env bash
# First staged Rev A physical-board LVS slice. The independently authored HDL
# covers the complete POWER and CLOCK_RESET placement blocks and four U1
# boundary pins. A temporary one-pad VBUS mutation must fail the same compare.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPO="$(cd "$ROOT/../.." && pwd)"
HDL="$ROOT/hdl/rev_a_power_clock_reset_lvs.v"
BOARD="$ROOT/kicad/rev-a-physical.board.json"
MAP="$ROOT/sync/rev_a_power_clock_reset_map.json"

cd "$REPO"
command -v yosys >/dev/null 2>&1 || {
    echo "  SKIP  Rev A POWER+CLOCK_RESET LVS: yosys not found"
    exit 0
}

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "== Rev A staged physical LVS: POWER + CLOCK_RESET =="
yosys -q -p "read_verilog -lib $HDL; read_verilog $HDL; hierarchy -top rev_a_power_clock_reset_lvs_top; write_json $TMP/lvs.json"
python3 sync/lvs.py \
    --hdl "$TMP/lvs.json" \
    --board "$BOARD" \
    --map "$MAP" \
    --include-power

python3 - "$BOARD" "$TMP/negative.board.json" <<'PY'
import copy
import json
import sys

source, target = sys.argv[1:]
board = json.load(open(source, encoding="utf-8"))
bad = copy.deepcopy(board)

def nodes(entry):
    return entry["nodes"] if isinstance(entry, dict) else entry

endpoint = ["J3", "A9"]
nodes(bad["nets"]["VCC_RAW"]).remove(endpoint)
nodes(bad["nets"]["GND"]).append(endpoint)
with open(target, "w", encoding="utf-8") as out:
    json.dump(bad, out)
PY

if python3 sync/lvs.py \
    --hdl "$TMP/lvs.json" \
    --board "$TMP/negative.board.json" \
    --map "$MAP" \
    --include-power >"$TMP/negative.out" 2>&1
then
    cat "$TMP/negative.out"
    echo "ERROR: negative control accepted J3.A9 moved from VCC_RAW to GND" >&2
    exit 1
fi
grep -q '==> MISMATCH' "$TMP/negative.out"
echo "  PASS  negative control rejects J3.A9 VBUS miswire"
