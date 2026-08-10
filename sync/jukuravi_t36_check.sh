#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

CC=${CC:-cc}
check_tmp=$(mktemp -d)
trap 'rm -rf "$check_tmp"' EXIT

python3 spinoffs/jukuravi/firmware/build_d0_refresh.py --check
python3 spinoffs/jukuravi/firmware/build_d0_row_refresh.py --check
python3 -m py_compile \
  scripts/analyze_jukuravi_partial_full_ram.py \
  spinoffs/jukuravi/protocol.py \
  spinoffs/jukuravi/host.py \
  spinoffs/jukuravi/batch.py \
  spinoffs/jukuravi/local_ram.py \
  spinoffs/jukuravi/firmware/build_d0_refresh.py \
  spinoffs/jukuravi/firmware/build_d0_row_refresh.py \
  tests/jukuravi_refresh_row_address_test.py \
  tests/jukuravi_full_ram_sweep_test.py \
  tests/jukuravi_local_full_ram_test.py \
  tests/jukuravi_t36_physical_sessions_test.py \
  tests/jukuravi_t36_refresh_test.py \
  tests/jukuravi_t36_batch_test.py

"$CC" -std=c11 -O2 -Wall -Wextra -Werror -I cosim \
  -o "$check_tmp/trace" \
  cosim/trace.c cosim/i8080.c cosim/juku_fdc.c cosim/juk_disk.c

python3 tests/jukuravi_t28_protocol_test.py
python3 tests/jukuravi_host_config_first_test.py
python3 tests/jukuravi_refresh_row_address_test.py
python3 tests/jukuravi_full_ram_sweep_test.py
python3 tests/jukuravi_t35_physical_sessions_test.py
python3 tests/jukuravi_t36_physical_sessions_test.py
python3 tests/jukuravi_t36_refresh_test.py \
  "$check_tmp/trace" spinoffs/jukuravi/firmware/diag-d0-row-refresh.bin
python3 tests/jukuravi_t36_batch_test.py \
  "$check_tmp/trace" spinoffs/jukuravi/firmware/diag-d0-row-refresh.bin
python3 tests/jukuravi_local_full_ram_test.py \
  "$check_tmp/trace" spinoffs/jukuravi/firmware/diag-d0-row-refresh.bin

echo "JUKURAVI-T36-CHECK: PASS"
