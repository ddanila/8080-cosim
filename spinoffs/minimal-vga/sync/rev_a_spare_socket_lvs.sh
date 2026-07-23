#!/usr/bin/env bash
# Seventh staged Rev A physical-board LVS slice: complete empty U23 spare
# socket, C17 decoupler, and every endpoint on its sole non-power net, CLK.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPO="$(cd "$ROOT/../.." && pwd)"
HDL="$ROOT/hdl/rev_a_spare_socket_lvs.v"
BOARD="$ROOT/kicad/rev-a-physical.board.json"
MAP="$ROOT/sync/rev_a_spare_socket_map.json"

cd "$REPO"
command -v yosys >/dev/null 2>&1 || {
    echo "  SKIP  Rev A spare-socket physical LVS: yosys not found"
    exit 0
}

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "== Rev A staged physical LVS: empty U23 spare socket =="
yosys -q -p "read_verilog -lib $HDL; read_verilog $HDL; hierarchy -top rev_a_spare_socket_lvs_top; write_json $TMP/lvs.json"
python3 sync/lvs.py \
    --hdl "$TMP/lvs.json" \
    --board "$BOARD" \
    --map "$MAP" \
    --include-power

python3 - "$BOARD" \
    "$TMP/clock-miswire.board.json" \
    "$TMP/second-clock-miswire.board.json" \
    "$TMP/decoupler-miswire.board.json" \
    "$TMP/missing-nc.board.json" \
    "$TMP/output-wired.board.json" \
    "$TMP/open-scope.board.json" <<'PY'
import copy
import json
import sys

(
    source,
    clock_target,
    second_clock_target,
    decoupler_target,
    nc_target,
    output_target,
    scope_target,
) = sys.argv[1:]
board = json.load(open(source, encoding="utf-8"))

def nodes(entry):
    return entry["nodes"] if isinstance(entry, dict) else entry

clock_miswire = copy.deepcopy(board)
endpoint = ["U23", "1"]
nodes(clock_miswire["nets"]["CLK"]).remove(endpoint)
nodes(clock_miswire["nets"]["GND"]).append(endpoint)
with open(clock_target, "w", encoding="utf-8") as out:
    json.dump(clock_miswire, out)

second_clock_miswire = copy.deepcopy(board)
endpoint = ["U23", "13"]
nodes(second_clock_miswire["nets"]["GND"]).remove(endpoint)
nodes(second_clock_miswire["nets"]["CLK"]).append(endpoint)
with open(second_clock_target, "w", encoding="utf-8") as out:
    json.dump(second_clock_miswire, out)

decoupler_miswire = copy.deepcopy(board)
endpoint = ["C17", "1"]
nodes(decoupler_miswire["nets"]["VCC"]).remove(endpoint)
nodes(decoupler_miswire["nets"]["GND"]).append(endpoint)
with open(decoupler_target, "w", encoding="utf-8") as out:
    json.dump(decoupler_miswire, out)

missing_nc = copy.deepcopy(board)
missing_nc["no_connects"].remove(["U23", "3"])
with open(nc_target, "w", encoding="utf-8") as out:
    json.dump(missing_nc, out)

output_wired = copy.deepcopy(board)
output_wired["no_connects"].remove(["U23", "8"])
nodes(output_wired["nets"]["CLK"]).append(["U23", "8"])
with open(output_target, "w", encoding="utf-8") as out:
    json.dump(output_wired, out)

open_scope = copy.deepcopy(board)
open_scope["no_connects"].remove(["U31", "15"])
nodes(open_scope["nets"]["CLK"]).append(["U31", "15"])
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
    "U23.1 moved from CLK to GND" \
    "$TMP/clock-miswire.out" "U_U23.P1"
expect_mismatch "$TMP/second-clock-miswire.board.json" \
    "grounded U23.13 second clock moved to CLK" \
    "$TMP/second-clock-miswire.out" "U_U23.P13"
expect_mismatch "$TMP/decoupler-miswire.board.json" \
    "C17.1 moved from VCC to GND" \
    "$TMP/decoupler-miswire.out" "U_C17.P1"
expect_mismatch "$TMP/missing-nc.board.json" \
    "missing U23.3 no-connect declaration" \
    "$TMP/missing-nc.out" "[missing NC] U23.3"
expect_mismatch "$TMP/output-wired.board.json" \
    "U23.8 counter output wired to CLK" \
    "$TMP/output-wired.out" "U_U23.P8"
expect_mismatch "$TMP/open-scope.board.json" \
    "unmapped U31.15 endpoint added to CLK" \
    "$TMP/open-scope.out" \
    "[open scope] CLK: endpoint U31.15 is outside map"
