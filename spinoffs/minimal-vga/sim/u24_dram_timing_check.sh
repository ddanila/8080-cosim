#!/usr/bin/env bash
set -euo pipefail

MV="$(cd "$(dirname "$0")/.." && pwd)"
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

iverilog -g2012 -Wall -o "$TMP/u24" \
  "$MV/hdl/u24_dram_timing.v" \
  "$MV/hdl/u24_dram_timing_tb.v"
vvp "$TMP/u24"
