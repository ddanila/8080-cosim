#!/usr/bin/env bash
# Third staged Rev A physical-board LVS slice: complete U1/U2 CPU+ROM core,
# its two decouplers, and every endpoint on all 36 non-power core nets.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPO="$(cd "$ROOT/../.." && pwd)"
HDL="$ROOT/hdl/rev_a_cpu_rom_lvs.v"
BOARD="$ROOT/kicad/rev-a-physical.board.json"
MAP="$ROOT/sync/rev_a_cpu_rom_map.json"

cd "$REPO"
command -v yosys >/dev/null 2>&1 || {
    echo "  SKIP  Rev A CPU+ROM physical LVS: yosys not found"
    exit 0
}

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "== Rev A staged physical LVS: Z80 CPU + ROM core =="
yosys -q -p "read_verilog -lib $HDL; read_verilog $HDL; hierarchy -top rev_a_cpu_rom_lvs_top; write_json $TMP/lvs.json"
python3 sync/lvs.py \
    --hdl "$TMP/lvs.json" \
    --board "$BOARD" \
    --map "$MAP" \
    --include-power

python3 - "$BOARD" \
    "$TMP/miswire.board.json" \
    "$TMP/missing-nc.board.json" \
    "$TMP/open-scope.board.json" <<'PY'
import copy
import json
import sys

source, miswire_target, nc_target, scope_target = sys.argv[1:]
board = json.load(open(source, encoding="utf-8"))

def nodes(entry):
    return entry["nodes"] if isinstance(entry, dict) else entry

miswire = copy.deepcopy(board)
endpoint = ["U1", "30"]
nodes(miswire["nets"]["A0"]).remove(endpoint)
nodes(miswire["nets"]["A1"]).append(endpoint)
with open(miswire_target, "w", encoding="utf-8") as out:
    json.dump(miswire, out)

missing_nc = copy.deepcopy(board)
missing_nc["no_connects"].remove(["U1", "18"])
with open(nc_target, "w", encoding="utf-8") as out:
    json.dump(missing_nc, out)

open_scope = copy.deepcopy(board)
open_scope["no_connects"].remove(["U23", "3"])
nodes(open_scope["nets"]["A0"]).append(["U23", "3"])
with open(scope_target, "w", encoding="utf-8") as out:
    json.dump(open_scope, out)
PY

expect_mismatch() {
    local board="$1"
    local label="$2"
    local output="$3"
    local evidence="$4"
    if python3 sync/lvs.py \
        --hdl "$TMP/lvs.json" \
        --board "$board" \
        --map "$MAP" \
        --include-power >"$output" 2>&1
    then
        cat "$output"
        echo "ERROR: negative control accepted $label" >&2
        exit 1
    fi
    grep -q '==> MISMATCH' "$output"
    grep -Fq -- "$evidence" "$output"
    echo "  PASS  negative control rejects $label"
}

expect_mismatch "$TMP/miswire.board.json" "U1.30 moved from A0 to A1" "$TMP/miswire.out" "U_CPU.P30"
expect_mismatch "$TMP/missing-nc.board.json" "missing U1.18 no-connect declaration" "$TMP/missing-nc.out" "[missing NC] U1.18"
expect_mismatch "$TMP/open-scope.board.json" "unmapped U23.3 endpoint added to A0" "$TMP/open-scope.out" "[open scope] A0: endpoint U23.3 is outside map"
