#!/usr/bin/env bash
# Fifth staged Rev A physical-board LVS slice: complete U20/U21 74HCT157
# address muxes, C14/C15 decouplers, and every endpoint on their 25 non-power
# nets.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPO="$(cd "$ROOT/../.." && pwd)"
HDL="$ROOT/hdl/rev_a_dram_mux_lvs.v"
BOARD="$ROOT/kicad/rev-a-physical.board.json"
MAP="$ROOT/sync/rev_a_dram_mux_map.json"

cd "$REPO"
command -v yosys >/dev/null 2>&1 || {
    echo "  SKIP  Rev A DRAM-mux physical LVS: yosys not found"
    exit 0
}

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "== Rev A staged physical LVS: 74HCT157 DRAM address muxes =="
yosys -q -p "read_verilog -lib $HDL; read_verilog $HDL; hierarchy -top rev_a_dram_mux_lvs_top; write_json $TMP/lvs.json"
python3 sync/lvs.py \
    --hdl "$TMP/lvs.json" \
    --board "$BOARD" \
    --map "$MAP" \
    --include-power

python3 - "$BOARD" \
    "$TMP/input-miswire.board.json" \
    "$TMP/output-miswire.board.json" \
    "$TMP/enable-miswire.board.json" \
    "$TMP/open-scope.board.json" <<'PY'
import copy
import json
import sys

source, input_target, output_target, enable_target, scope_target = sys.argv[1:]
board = json.load(open(source, encoding="utf-8"))

def nodes(entry):
    return entry["nodes"] if isinstance(entry, dict) else entry

input_miswire = copy.deepcopy(board)
endpoint = ["U20", "2"]
nodes(input_miswire["nets"]["A0"]).remove(endpoint)
nodes(input_miswire["nets"]["A1"]).append(endpoint)
with open(input_target, "w", encoding="utf-8") as out:
    json.dump(input_miswire, out)

output_miswire = copy.deepcopy(board)
endpoint = ["U21", "4"]
nodes(output_miswire["nets"]["DRAM_A4"]).remove(endpoint)
nodes(output_miswire["nets"]["DRAM_A5"]).append(endpoint)
with open(output_target, "w", encoding="utf-8") as out:
    json.dump(output_miswire, out)

enable_miswire = copy.deepcopy(board)
enable_endpoints = [["U20", "15"], ["U21", "15"]]
for endpoint in enable_endpoints:
    nodes(enable_miswire["nets"]["GND"]).remove(endpoint)
enable_miswire["nets"]["ADDRMUX_OE_N"] = enable_endpoints
with open(enable_target, "w", encoding="utf-8") as out:
    json.dump(enable_miswire, out)

open_scope = copy.deepcopy(board)
open_scope["no_connects"].remove(["U23", "3"])
nodes(open_scope["nets"]["ADDRMUX_SEL"]).append(["U23", "3"])
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

expect_mismatch "$TMP/input-miswire.board.json" \
    "U20.2 moved from A0 to A1" \
    "$TMP/input-miswire.out" "U_U20.P2"
expect_mismatch "$TMP/output-miswire.board.json" \
    "U21.4 moved from DRAM_A4 to DRAM_A5" \
    "$TMP/output-miswire.out" "U_U21.P4"
expect_mismatch "$TMP/enable-miswire.board.json" \
    "former floating U20.15/U21.15 ADDRMUX_OE_N island" \
    "$TMP/enable-miswire.out" "U_U20.P15"
expect_mismatch "$TMP/open-scope.board.json" \
    "unmapped U23.3 endpoint added to ADDRMUX_SEL" \
    "$TMP/open-scope.out" "[open scope] ADDRMUX_SEL: endpoint U23.3 is outside map"
