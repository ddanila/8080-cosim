#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

CC=${CC:-cc}
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

python3 spinoffs/jukuravi/firmware/build_d0_low4k.py --check
python3 -m py_compile \
  spinoffs/jukuravi/host.py \
  spinoffs/jukuravi/firmware/build_d0_resilient.py \
  spinoffs/jukuravi/firmware/build_d2_loader_v2.py \
  spinoffs/jukuravi/firmware/build_d5_loader_v5.py \
  spinoffs/jukuravi/firmware/build_d0_low4k.py \
  tests/jukuravi_t30_boundary_repro_test.py \
  tests/jukuravi_t31_low4k_test.py

"$CC" -std=c11 -O2 -Wall -Wextra -Werror -I cosim \
  -o "$tmp/trace" \
  cosim/trace.c cosim/i8080.c cosim/juku_fdc.c cosim/juk_disk.c

python3 tests/jukuravi_t30_boundary_repro_test.py \
  "$tmp/trace" spinoffs/jukuravi/firmware/diag-d0-txready.bin
python3 tests/jukuravi_t31_low4k_test.py \
  "$tmp/trace" spinoffs/jukuravi/firmware/diag-d0-low4k.bin

echo "JUKURAVI-T31-CHECK: PASS"
