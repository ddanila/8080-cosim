#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

CC=${CC:-cc}
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

python3 spinoffs/jukuravi/firmware/build_d0_waitclass.py --check
python3 -m py_compile \
  spinoffs/jukuravi/firmware/build_d0_waitclass.py \
  spinoffs/jukuravi/probe_pc_a12.py \
  spinoffs/jukuravi/probe_waitclass.py \
  tests/jukuravi_t32_low4k_test.py \
  tests/jukuravi_t32_waitclass_test.py

"$CC" -std=c11 -O2 -Wall -Wextra -Werror -I cosim \
  -o "$tmp/trace" \
  cosim/trace.c cosim/i8080.c cosim/juku_fdc.c cosim/juk_disk.c

python3 tests/jukuravi_t32_low4k_test.py \
  "$tmp/trace" spinoffs/jukuravi/firmware/diag-d0-waitclass.bin
python3 tests/jukuravi_t32_waitclass_test.py \
  "$tmp/trace" spinoffs/jukuravi/firmware/diag-d0-waitclass.bin

echo "JUKURAVI-T32-CHECK: PASS"
