#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

CC=${CC:-cc}
check_tmp=$(mktemp -d)
trap 'rm -rf "$check_tmp"' EXIT

python3 spinoffs/jukuravi/firmware/build_d0_refresh.py --check
python3 -m py_compile \
  spinoffs/jukuravi/protocol.py \
  spinoffs/jukuravi/host.py \
  spinoffs/jukuravi/firmware/build_d0_resilient.py \
  spinoffs/jukuravi/firmware/build_d0_low4k.py \
  spinoffs/jukuravi/firmware/build_d2_loader_v2.py \
  spinoffs/jukuravi/firmware/build_d6_loader_v6.py \
  spinoffs/jukuravi/firmware/build_d0_refresh.py \
  spinoffs/jukuravi/batch.py \
  tests/jukuravi_refresh_row_address_test.py \
  tests/jukuravi_t35_physical_sessions_test.py

"$CC" -std=c11 -O2 -Wall -Wextra -Werror -I cosim \
  -o "$check_tmp/trace" \
  cosim/trace.c cosim/i8080.c cosim/juku_fdc.c cosim/juk_disk.c

python3 tests/jukuravi_t28_protocol_test.py
python3 tests/jukuravi_refresh_row_address_test.py
python3 tests/jukuravi_t35_physical_sessions_test.py

echo "JUKURAVI-T35-HISTORICAL-CHECK: PASS"
