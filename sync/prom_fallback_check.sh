#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

sim="$(mktemp -t prom_fallback_tb.XXXXXX)"
trap 'rm -f "$sim"' EXIT

iverilog -g2012 -s prom_fallback_tb -o "$sim" \
  hdl/devices.v \
  hdl/sim/prom_fallback_tb.v

out="$("$sim")"
printf '%s\n' "$out"

if ! printf '%s\n' "$out" | grep -q '^PROM-FALLBACK: PASS$'; then
  echo "PROM-FALLBACK-CHECK: FAIL"
  exit 1
fi

echo "PROM-FALLBACK-CHECK: PASS"
