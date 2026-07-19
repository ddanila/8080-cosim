#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
command -v iverilog >/dev/null || { echo "iverilog not found"; exit 2; }
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
iverilog -g2012 -s kp12_mux_tb -o "$tmp/kp12_mux_tb" \
  hdl/devices.v hdl/sim/kp12_mux_tb.v
out=$(vvp "$tmp/kp12_mux_tb")
printf '%s\n' "$out"
grep -q '^KP12-MUX: PASS$' <<<"$out"
