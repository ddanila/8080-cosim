#!/usr/bin/env bash
# Eighth staged Rev A physical-board LVS slice: complete U24 GAL22V10 DRAM
# timing/arbitration device, C18, and every endpoint on 19 non-power nets.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPO="$(cd "$ROOT/../.." && pwd)"
HDL="$ROOT/hdl/rev_a_dram_timing_lvs.v"
BOARD="$ROOT/kicad/rev-a-physical.board.json"
MAP="$ROOT/sync/rev_a_dram_timing_map.json"

cd "$REPO"
command -v yosys >/dev/null 2>&1 || {
    echo "  SKIP  Rev A DRAM-timing physical LVS: yosys not found"
    exit 0
}

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "== Rev A staged physical LVS: U24 DRAM timing + arbitration =="
yosys -q -p "read_verilog -lib $HDL; read_verilog $HDL; hierarchy -top rev_a_dram_timing_lvs_top; write_json $TMP/lvs.json"
python3 sync/lvs.py \
    --hdl "$TMP/lvs.json" \
    --board "$BOARD" \
    --map "$MAP" \
    --include-power

python3 - "$BOARD" \
    "$TMP/decode-input-miswire.board.json" \
    "$TMP/refresh-input-miswire.board.json" \
    "$TMP/pin13-miswire.board.json" \
    "$TMP/output-miswire.board.json" \
    "$TMP/decoupler-miswire.board.json" \
    "$TMP/missing-nc.board.json" \
    "$TMP/unexpected-nc.board.json" \
    "$TMP/open-scope.board.json" <<'PY'
import copy
import json
import sys

(
    source,
    decode_target,
    refresh_target,
    pin13_target,
    output_target,
    decoupler_target,
    missing_nc_target,
    unexpected_nc_target,
    scope_target,
) = sys.argv[1:]
board = json.load(open(source, encoding="utf-8"))

def nodes(entry):
    return entry["nodes"] if isinstance(entry, dict) else entry

decode_input_miswire = copy.deepcopy(board)
endpoint = ["U24", "3"]
nodes(decode_input_miswire["nets"]["RAM_CE_N"]).remove(endpoint)
nodes(decode_input_miswire["nets"]["MEM_RD_N"]).append(endpoint)
with open(decode_target, "w", encoding="utf-8") as out:
    json.dump(decode_input_miswire, out)

refresh_input_miswire = copy.deepcopy(board)
endpoint = ["U24", "8"]
nodes(refresh_input_miswire["nets"]["REFRESH_ROW0"]).remove(endpoint)
nodes(refresh_input_miswire["nets"]["REFRESH_ROW1"]).append(endpoint)
with open(refresh_target, "w", encoding="utf-8") as out:
    json.dump(refresh_input_miswire, out)

pin13_miswire = copy.deepcopy(board)
endpoint = ["U24", "13"]
nodes(pin13_miswire["nets"]["DECODE_WAIT_N"]).remove(endpoint)
nodes(pin13_miswire["nets"]["RAS_N"]).append(endpoint)
with open(pin13_target, "w", encoding="utf-8") as out:
    json.dump(pin13_miswire, out)

output_miswire = copy.deepcopy(board)
endpoint = ["U24", "14"]
nodes(output_miswire["nets"]["RAS_N"]).remove(endpoint)
nodes(output_miswire["nets"]["CAS_N"]).append(endpoint)
with open(output_target, "w", encoding="utf-8") as out:
    json.dump(output_miswire, out)

decoupler_miswire = copy.deepcopy(board)
endpoint = ["C18", "1"]
nodes(decoupler_miswire["nets"]["VCC"]).remove(endpoint)
nodes(decoupler_miswire["nets"]["GND"]).append(endpoint)
with open(decoupler_target, "w", encoding="utf-8") as out:
    json.dump(decoupler_miswire, out)

missing_nc = copy.deepcopy(board)
missing_nc["no_connects"].remove(["U24", "21"])
with open(missing_nc_target, "w", encoding="utf-8") as out:
    json.dump(missing_nc, out)

unexpected_nc = copy.deepcopy(board)
unexpected_nc["no_connects"].append(["U24", "20"])
with open(unexpected_nc_target, "w", encoding="utf-8") as out:
    json.dump(unexpected_nc, out)

open_scope = copy.deepcopy(board)
open_scope["no_connects"].remove(["U30", "18"])
nodes(open_scope["nets"]["WAIT_N"]).append(["U30", "18"])
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

expect_mismatch "$TMP/decode-input-miswire.board.json" \
    "U24.3 moved from RAM_CE_N to MEM_RD_N" \
    "$TMP/decode-input-miswire.out" "U_U24.P3"
expect_mismatch "$TMP/refresh-input-miswire.board.json" \
    "U24.8 moved from REFRESH_ROW0 to REFRESH_ROW1" \
    "$TMP/refresh-input-miswire.out" "U_U24.P8"
expect_mismatch "$TMP/pin13-miswire.board.json" \
    "U24.13 input moved from DECODE_WAIT_N to RAS_N" \
    "$TMP/pin13-miswire.out" "U_U24.P13"
expect_mismatch "$TMP/output-miswire.board.json" \
    "U24.14 moved from RAS_N to CAS_N" \
    "$TMP/output-miswire.out" "U_U24.P14"
expect_mismatch "$TMP/decoupler-miswire.board.json" \
    "C18.1 moved from VCC to GND" \
    "$TMP/decoupler-miswire.out" "U_C18.P1"
expect_mismatch "$TMP/missing-nc.board.json" \
    "missing U24.21 state-feedback no-connect declaration" \
    "$TMP/missing-nc.out" "[missing NC] U24.21"
expect_mismatch "$TMP/unexpected-nc.board.json" \
    "false U24.20 REFRESH_TICK no-connect declaration" \
    "$TMP/unexpected-nc.out" "[unexpected NC] U24.20"
expect_mismatch "$TMP/open-scope.board.json" \
    "unmapped U30.18 endpoint added to WAIT_N" \
    "$TMP/open-scope.out" \
    "[open scope] WAIT_N: endpoint U30.18 is outside map"
