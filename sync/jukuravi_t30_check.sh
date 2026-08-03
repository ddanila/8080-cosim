#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

CC=${CC:-cc}
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

python3 spinoffs/jukuravi/firmware/build_d0_txready.py --check
python3 -m py_compile \
  spinoffs/jukuravi/firmware/build_d0_resilient.py \
  spinoffs/jukuravi/firmware/build_d2_loader_v2.py \
  spinoffs/jukuravi/firmware/build_d4_loader_v4.py \
  spinoffs/jukuravi/firmware/build_d0_txready.py \
  tests/jukuravi_t29_recovery_test.py \
  tests/jukuravi_t30_txempty_test.py

"$CC" -std=c11 -O2 -Wall -Wextra -Werror -I cosim \
  -o "$tmp/trace" \
  cosim/trace.c cosim/i8080.c cosim/juku_fdc.c cosim/juk_disk.c

python3 tests/jukuravi_t30_txempty_test.py \
  "$tmp/trace" spinoffs/jukuravi/firmware/diag-d0-txready.bin

echo "JUKURAVI-T30-CHECK: PASS"
