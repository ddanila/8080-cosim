#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

CC=${CC:-cc}
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

python3 spinoffs/jukuravi/firmware/build_d0_host_recover.py --check
python3 -m py_compile \
  spinoffs/jukuravi/firmware/build_d0_resilient.py \
  spinoffs/jukuravi/firmware/build_d2_loader_v2.py \
  spinoffs/jukuravi/firmware/build_d3_loader_v3.py \
  spinoffs/jukuravi/firmware/build_d0_host_recover.py \
  tests/jukuravi_t29_recovery_test.py

"$CC" -std=c11 -O2 -Wall -Wextra -Werror -I cosim \
  -o "$tmp/trace" \
  cosim/trace.c cosim/i8080.c cosim/juku_fdc.c cosim/juk_disk.c

python3 tests/jukuravi_t29_recovery_test.py \
  "$tmp/trace" spinoffs/jukuravi/firmware/diag-d0-host-recover.bin

echo "JUKURAVI-T29-CHECK: PASS"
