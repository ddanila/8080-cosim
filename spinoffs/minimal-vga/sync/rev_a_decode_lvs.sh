#!/usr/bin/env bash
# Second staged Rev A physical-board LVS slice: complete decode PROM/socket/glue
# group plus every non-power external endpoint touched by that group.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPO="$(cd "$ROOT/../.." && pwd)"
HDL="$ROOT/hdl/rev_a_decode_lvs.v"
BOARD="$ROOT/kicad/rev-a-physical.board.json"
MAP="$ROOT/sync/rev_a_decode_map.json"

cd "$REPO"
command -v yosys >/dev/null 2>&1 || {
    echo "  SKIP  Rev A decode physical LVS: yosys not found"
    exit 0
}

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "== Rev A staged physical LVS: decode PROM sockets + glue =="
yosys -q -p "read_verilog -lib $HDL; read_verilog $HDL; hierarchy -top rev_a_decode_lvs_top; write_json $TMP/lvs.json"
python3 sync/lvs.py \
    --hdl "$TMP/lvs.json" \
    --board "$BOARD" \
    --map "$MAP" \
    --include-power

python3 - "$BOARD" "$TMP/miswire.board.json" "$TMP/missing-nc.board.json" <<'PY'
import copy
import json
import sys

source, miswire_target, nc_target = sys.argv[1:]
board = json.load(open(source, encoding="utf-8"))

def nodes(entry):
    return entry["nodes"] if isinstance(entry, dict) else entry

miswire = copy.deepcopy(board)
endpoint = ["U3", "12"]
nodes(miswire["nets"]["DEC_ROM_N"]).remove(endpoint)
nodes(miswire["nets"]["DEC_RAM_N"]).append(endpoint)
with open(miswire_target, "w", encoding="utf-8") as out:
    json.dump(miswire, out)

missing_nc = copy.deepcopy(board)
missing_nc["no_connects"].remove(["U6", "6"])
with open(nc_target, "w", encoding="utf-8") as out:
    json.dump(missing_nc, out)
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

expect_mismatch "$TMP/miswire.board.json" "U3.12 moved from DEC_ROM_N to DEC_RAM_N" "$TMP/miswire.out" "U_U3.P12"
expect_mismatch "$TMP/missing-nc.board.json" "missing U6.6 no-connect declaration" "$TMP/missing-nc.out" "[missing NC] U6.6"
