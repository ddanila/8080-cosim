#!/usr/bin/env bash
# Sixth staged Rev A physical-board LVS slice: complete U22 74HCT393 refresh
# counter, C16 decoupler, and every endpoint on CLK plus eight refresh-row nets.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPO="$(cd "$ROOT/../.." && pwd)"
HDL="$ROOT/hdl/rev_a_refresh_counter_lvs.v"
BOARD="$ROOT/kicad/rev-a-physical.board.json"
MAP="$ROOT/sync/rev_a_refresh_counter_map.json"

cd "$REPO"
command -v yosys >/dev/null 2>&1 || {
    echo "  SKIP  Rev A refresh-counter physical LVS: yosys not found"
    exit 0
}

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "== Rev A staged physical LVS: cascaded 74HCT393 refresh counter =="
yosys -q -p "read_verilog -lib $HDL; read_verilog $HDL; hierarchy -top rev_a_refresh_counter_lvs_top; write_json $TMP/lvs.json"
python3 sync/lvs.py \
    --hdl "$TMP/lvs.json" \
    --board "$BOARD" \
    --map "$MAP" \
    --include-power

python3 - "$BOARD" \
    "$TMP/clock-miswire.board.json" \
    "$TMP/output-miswire.board.json" \
    "$TMP/cascade-miswire.board.json" \
    "$TMP/reset-island.board.json" \
    "$TMP/unexpected-nc.board.json" \
    "$TMP/open-scope.board.json" <<'PY'
import copy
import json
import sys

(
    source,
    clock_target,
    output_target,
    cascade_target,
    reset_target,
    nc_target,
    scope_target,
) = sys.argv[1:]
board = json.load(open(source, encoding="utf-8"))

def nodes(entry):
    return entry["nodes"] if isinstance(entry, dict) else entry

clock_miswire = copy.deepcopy(board)
endpoint = ["U22", "1"]
nodes(clock_miswire["nets"]["CLK"]).remove(endpoint)
nodes(clock_miswire["nets"]["REFRESH_TICK"]).append(endpoint)
with open(clock_target, "w", encoding="utf-8") as out:
    json.dump(clock_miswire, out)

output_miswire = copy.deepcopy(board)
endpoint = ["U22", "3"]
nodes(output_miswire["nets"]["REFRESH_ROW0"]).remove(endpoint)
nodes(output_miswire["nets"]["REFRESH_ROW1"]).append(endpoint)
with open(output_target, "w", encoding="utf-8") as out:
    json.dump(output_miswire, out)

cascade_miswire = copy.deepcopy(board)
endpoint = ["U22", "13"]
nodes(cascade_miswire["nets"]["REFRESH_ROW3"]).remove(endpoint)
nodes(cascade_miswire["nets"]["GND"]).append(endpoint)
with open(cascade_target, "w", encoding="utf-8") as out:
    json.dump(cascade_miswire, out)

reset_island = copy.deepcopy(board)
reset_endpoints = [["U22", "2"], ["U22", "12"]]
for endpoint in reset_endpoints:
    nodes(reset_island["nets"]["GND"]).remove(endpoint)
reset_island["nets"]["REFRESH_CLR"] = reset_endpoints
with open(reset_target, "w", encoding="utf-8") as out:
    json.dump(reset_island, out)

unexpected_nc = copy.deepcopy(board)
unexpected_nc["no_connects"].append(["U22", "8"])
with open(nc_target, "w", encoding="utf-8") as out:
    json.dump(unexpected_nc, out)

open_scope = copy.deepcopy(board)
open_scope["no_connects"].remove(["U23", "3"])
nodes(open_scope["nets"]["REFRESH_ROW0"]).append(["U23", "3"])
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

expect_mismatch "$TMP/clock-miswire.board.json" \
    "U22.1 moved from CLK to REFRESH_TICK" \
    "$TMP/clock-miswire.out" "U_U22.P1"
expect_mismatch "$TMP/output-miswire.board.json" \
    "U22.3 moved from REFRESH_ROW0 to REFRESH_ROW1" \
    "$TMP/output-miswire.out" "U_U22.P3"
expect_mismatch "$TMP/cascade-miswire.board.json" \
    "U22.13 cascade clock moved from REFRESH_ROW3 to GND" \
    "$TMP/cascade-miswire.out" "U_U22.P13"
expect_mismatch "$TMP/reset-island.board.json" \
    "former floating U22.2/U22.12 REFRESH_CLR island" \
    "$TMP/reset-island.out" "U_U22.P2"
expect_mismatch "$TMP/unexpected-nc.board.json" \
    "false U22.8 no-connect declaration" \
    "$TMP/unexpected-nc.out" "[unexpected NC] U22.8"
expect_mismatch "$TMP/open-scope.board.json" \
    "unmapped U23.3 endpoint added to REFRESH_ROW0" \
    "$TMP/open-scope.out" \
    "[open scope] REFRESH_ROW0: endpoint U23.3 is outside map"
