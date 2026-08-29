#!/usr/bin/env bash
# R5.I1/I2: contract plus real-PIT/8251/POST twin and two fault controls.
set -euo pipefail
MV="$(cd "$(dirname "$0")/.." && pwd)"
ROOT="$(cd "$MV/../.." && pwd)"
REVB="$MV/hdl/revb"
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
command -v iverilog >/dev/null || { echo "iverilog not found"; exit 2; }

python3 "$MV/kicad/revb/check_revb_io_expansion.py"
fail=0

run() {
  local name="$1" expect="$2"; shift 2
  iverilog -g2012 -s revb_io_expansion_tb -o "$TMP/$name" "$@" \
    "$ROOT/hdl/devices.v" "$REVB/revb_io_card.v" "$REVB/revb_io_expansion_tb.v"
  local out got
  out=$(vvp "$TMP/$name" 2>&1 || true)
  if grep -q 'REVB-IO-EXPANSION-TB: PASS' <<<"$out"; then got=PASS; else got=FAIL; fi
  if [ "$got" = "$expect" ]; then
    echo "  ok $name -> $got"
  else
    echo "  FAIL $name -> $got (expected $expect)"
    sed 's/^/        /' <<<"$out"
    fail=1
  fi
}

run pit_normal PASS -Prevb_io_expansion_tb.CLK_SOURCE=1
run direct_19200 PASS -Prevb_io_expansion_tb.CLK_SOURCE=0
run direct_9600 PASS -Prevb_io_expansion_tb.CLK_SOURCE=2
run bad_pit_tap FAIL -Prevb_io_expansion_tb.CLK_SOURCE=1 -Prevb_io_expansion_tb.BAD_PIT_TAP=1
run post_alias FAIL -Prevb_io_expansion_tb.CLK_SOURCE=1 -Prevb_io_expansion_tb.POST_ALIAS_FAULT=1

if [ "$fail" = 0 ]; then
  echo "REVB-IO-EXPANSION-CHECK: PASS (PIT/direct clocks, POST, sound, 8251; mutations rejected)"
else
  echo "REVB-IO-EXPANSION-CHECK: FAIL"
  exit 1
fi
