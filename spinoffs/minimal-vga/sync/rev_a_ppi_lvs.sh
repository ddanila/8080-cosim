#!/usr/bin/env bash
# Ninth staged Rev A physical-board LVS slice: complete U30 82C55 PPI, C19,
# and every endpoint on all 28 non-power nets touched by the PPI.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPO="$(cd "$ROOT/../.." && pwd)"
HDL="$ROOT/hdl/rev_a_ppi_lvs.v"
BOARD="$ROOT/kicad/rev-a-physical.board.json"
MAP="$ROOT/sync/rev_a_ppi_map.json"

cd "$REPO"
command -v yosys >/dev/null 2>&1 || {
    echo "  SKIP  Rev A PPI physical LVS: yosys not found"
    exit 0
}

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "== Rev A staged physical LVS: complete 82C55 PPI =="
yosys -q -p "read_verilog -lib $HDL; read_verilog $HDL; hierarchy -top rev_a_ppi_lvs_top; write_json $TMP/lvs.json"
python3 sync/lvs.py \
    --hdl "$TMP/lvs.json" \
    --board "$BOARD" \
    --map "$MAP" \
    --include-power

python3 - "$BOARD" \
    "$TMP/address-miswire.board.json" \
    "$TMP/data-miswire.board.json" \
    "$TMP/control-miswire.board.json" \
    "$TMP/row-miswire.board.json" \
    "$TMP/column-miswire.board.json" \
    "$TMP/mode-miswire.board.json" \
    "$TMP/decoupler-miswire.board.json" \
    "$TMP/missing-nc.board.json" \
    "$TMP/unexpected-nc.board.json" \
    "$TMP/open-scope.board.json" <<'PY'
import copy
import json
import sys

(
    source,
    address_target,
    data_target,
    control_target,
    row_target,
    column_target,
    mode_target,
    decoupler_target,
    missing_nc_target,
    unexpected_nc_target,
    scope_target,
) = sys.argv[1:]
board = json.load(open(source, encoding="utf-8"))

def nodes(entry):
    return entry["nodes"] if isinstance(entry, dict) else entry

def move_endpoint(model, endpoint, source_net, target_net):
    nodes(model["nets"][source_net]).remove(endpoint)
    nodes(model["nets"][target_net]).append(endpoint)

address_miswire = copy.deepcopy(board)
move_endpoint(address_miswire, ["U30", "9"], "A0", "A1")
with open(address_target, "w", encoding="utf-8") as out:
    json.dump(address_miswire, out)

data_miswire = copy.deepcopy(board)
move_endpoint(data_miswire, ["U30", "34"], "D0", "D1")
with open(data_target, "w", encoding="utf-8") as out:
    json.dump(data_miswire, out)

control_miswire = copy.deepcopy(board)
move_endpoint(control_miswire, ["U30", "5"], "IO_RD_N", "IO_WR_N")
with open(control_target, "w", encoding="utf-8") as out:
    json.dump(control_miswire, out)

row_miswire = copy.deepcopy(board)
move_endpoint(row_miswire, ["U30", "13"], "KBD_ROW_A0_N", "KBD_ROW_A1_N")
with open(row_target, "w", encoding="utf-8") as out:
    json.dump(row_miswire, out)

column_miswire = copy.deepcopy(board)
move_endpoint(column_miswire, ["U30", "4"], "KBD_COL0_DRV", "KBD_COL1_DRV")
with open(column_target, "w", encoding="utf-8") as out:
    json.dump(column_miswire, out)

mode_miswire = copy.deepcopy(board)
move_endpoint(mode_miswire, ["U30", "14"], "PC0", "PC1")
with open(mode_target, "w", encoding="utf-8") as out:
    json.dump(mode_miswire, out)

decoupler_miswire = copy.deepcopy(board)
move_endpoint(decoupler_miswire, ["C19", "1"], "VCC", "GND")
with open(decoupler_target, "w", encoding="utf-8") as out:
    json.dump(decoupler_miswire, out)

missing_nc = copy.deepcopy(board)
missing_nc["no_connects"].remove(["U30", "18"])
with open(missing_nc_target, "w", encoding="utf-8") as out:
    json.dump(missing_nc, out)

unexpected_nc = copy.deepcopy(board)
unexpected_nc["no_connects"].append(["U30", "10"])
with open(unexpected_nc_target, "w", encoding="utf-8") as out:
    json.dump(unexpected_nc, out)

open_scope = copy.deepcopy(board)
open_scope["no_connects"].remove(["U31", "15"])
nodes(open_scope["nets"]["KBD_ROW_A0_N"]).append(["U31", "15"])
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

expect_mismatch "$TMP/address-miswire.board.json" \
    "U30.9 moved from A0 to A1" \
    "$TMP/address-miswire.out" "U_U30.P9"
expect_mismatch "$TMP/data-miswire.board.json" \
    "U30.34 moved from D0 to D1" \
    "$TMP/data-miswire.out" "U_U30.P34"
expect_mismatch "$TMP/control-miswire.board.json" \
    "U30.5 moved from IO_RD_N to IO_WR_N" \
    "$TMP/control-miswire.out" "U_U30.P5"
expect_mismatch "$TMP/row-miswire.board.json" \
    "U30.13 moved from KBD_ROW_A0_N to KBD_ROW_A1_N" \
    "$TMP/row-miswire.out" "U_U30.P13"
expect_mismatch "$TMP/column-miswire.board.json" \
    "U30.4 moved from KBD_COL0_DRV to KBD_COL1_DRV" \
    "$TMP/column-miswire.out" "U_U30.P4"
expect_mismatch "$TMP/mode-miswire.board.json" \
    "U30.14 moved from PC0 to PC1" \
    "$TMP/mode-miswire.out" "U_U30.P14"
expect_mismatch "$TMP/decoupler-miswire.board.json" \
    "C19.1 moved from VCC to GND" \
    "$TMP/decoupler-miswire.out" "U_C19.P1"
expect_mismatch "$TMP/missing-nc.board.json" \
    "missing U30.18 no-connect declaration" \
    "$TMP/missing-nc.out" "[missing NC] U30.18"
expect_mismatch "$TMP/unexpected-nc.board.json" \
    "false U30.10 KBD_GS_N no-connect declaration" \
    "$TMP/unexpected-nc.out" "[unexpected NC] U30.10"
expect_mismatch "$TMP/open-scope.board.json" \
    "unmapped U31.15 endpoint added to KBD_ROW_A0_N" \
    "$TMP/open-scope.out" \
    "[open scope] KBD_ROW_A0_N: endpoint U31.15 is outside map"
