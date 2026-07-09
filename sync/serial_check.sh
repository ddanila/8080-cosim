#!/usr/bin/env bash
set -euo pipefail

TMP=${TMPDIR:-/tmp}/juku-serial-check.$$
mkdir -p "$TMP"
trap 'rm -rf "$TMP"' EXIT

iverilog -g2012 -o "$TMP/usart_8251_tb" hdl/vendor/vm80a.v hdl/devices.v hdl/sim/usart_8251_tb.v
out=$(vvp "$TMP/usart_8251_tb")
echo "$out"
printf '%s\n' "$out" | grep -q "USART8251: PASS"

python3 scripts/report_serial_handoff.py
