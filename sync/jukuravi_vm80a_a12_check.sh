#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

nasm -f bin -o "$tmp/probe.bin" \
  spinoffs/jukuravi/firmware/ram-a12-increment-registers-4000.asm
od -An -v -tx1 "$tmp/probe.bin" | tr -s '[:space:]' '\n' | sed '/^$/d' \
  > "$tmp/probe.hex"

for fault in 0 1; do
  iverilog -g2012 \
    -Pjukuravi_vm80a_a12_tb.FAULT=$fault \
    -o "$tmp/vm80a-a12-$fault" \
    hdl/vendor/vm80a.v hdl/sim/jukuravi_vm80a_a12_tb.v
  output=$(vvp "$tmp/vm80a-a12-$fault" +probe="$tmp/probe.hex")
  printf '%s\n' "$output"
  grep -q "JUKURAVI-VM80A-A12: PASS" <<<"$output"
  if grep -q "JUKURAVI-VM80A-A12: FAIL" <<<"$output"; then
    exit 1
  fi
done

echo "JUKURAVI-VM80A-A12-CHECK: PASS"
