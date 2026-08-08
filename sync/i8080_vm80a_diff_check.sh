#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
command -v iverilog >/dev/null || { echo "iverilog not found"; exit 2; }
CPU_DIFF_TMP=$(mktemp -d)
trap 'rm -rf "$CPU_DIFF_TMP"' EXIT

${CC:-cc} -std=c11 -O2 -Wall -Wextra -Werror -I cosim \
  -o "$CPU_DIFF_TMP/i8080_vector_runner" \
  tests/i8080_vector_runner.c cosim/i8080.c
iverilog -g2012 -s i8080_vm80a_diff_tb \
  -o "$CPU_DIFF_TMP/i8080_vm80a_diff_tb" \
  hdl/vendor/vm80a.v hdl/sim/i8080_vm80a_diff_tb.v
python3 tests/i8080_vm80a_diff_test.py \
  "$CPU_DIFF_TMP/i8080_vector_runner" "$CPU_DIFF_TMP/i8080_vm80a_diff_tb"
