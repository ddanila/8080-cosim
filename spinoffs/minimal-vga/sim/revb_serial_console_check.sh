#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
python3 spinoffs/minimal-vga/sim/revb_serial_c10_vectors.py --out-dir "$TMP"
iverilog -g2012 -s revb_serial_console_tb -o "$TMP/serial" \
  hdl/devices.v spinoffs/minimal-vga/hdl/revb/revb_serial_console_tb.v
vvp "$TMP/serial" +request="$TMP/request.hex" +reply="$TMP/reply.hex" | tee "$TMP/good.log"
grep -q '^REVB-SERIAL-CONSOLE: PASS' "$TMP/good.log"

if vvp "$TMP/serial" +request="$TMP/request.hex" +reply="$TMP/reply.hex" \
    +inject_isolation_fault | grep -q '^REVB-SERIAL-CONSOLE: PASS'; then
  echo "REVB-SERIAL-CONSOLE: negative control FAILED (isolation fault passed)"
  exit 1
fi
echo "REVB-SERIAL-CONSOLE-CHECK: PASS (positive + isolation negative control)"
