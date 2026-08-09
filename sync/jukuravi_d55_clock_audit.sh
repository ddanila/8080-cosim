#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

python3 spinoffs/jukuravi/firmware/build_d0_low4k.py --check
python3 spinoffs/jukuravi/firmware/build_d0_clocked_pit.py --check

xxd -p -c1 spinoffs/jukuravi/firmware/diag-d0-low4k.bin > "$tmp/t31.hex"
xxd -p -c1 spinoffs/jukuravi/firmware/diag-d0-clocked-pit.bin > "$tmp/t34.hex"
iverilog -g2012 -o "$tmp/d55-audit" \
  hdl/vendor/vm80a.v hdl/devices.v hdl/juku_top.v \
  hdl/sim/jukuravi_d55_clock_audit_tb.v

run_case() {
  local name=$1 rom=$2 expected_e=$3 predicates=$4 expect_unclocked=$5 fault=$6
  local out
  out=$(vvp "$tmp/d55-audit" \
    +rom="$rom" +expected_e="$expected_e" \
    +expected_predicates="$predicates" \
    +expect_unclocked="$expect_unclocked" +fault="$fault")
  printf '%s\n' "$out"
  grep -q 'JUKURAVI-D55-CLOCK-AUDIT: PASS' <<<"$out"
  if grep -q 'JUKURAVI-D55-CLOCK-AUDIT: FAIL' <<<"$out"; then
    return 1
  fi
  printf 'JUKURAVI-D55-CLOCK-CASE: PASS %s\n' "$name"
}

run_case t31-negative-control "$tmp/t31.hex" 08 4 1 0
run_case t34-clean "$tmp/t34.hex" 00 6 0 0
run_case t34-d55-db7 "$tmp/t34.hex" 08 6 0 1
run_case t34-d54-hchain "$tmp/t34.hex" 08 6 1 2
run_case t34-d56-clock "$tmp/t34.hex" 08 6 1 3
run_case t34-d9-chip-select "$tmp/t34.hex" 08 6 0 4

echo 'JUKURAVI-D55-CLOCK-AUDIT: ALL PASS'
