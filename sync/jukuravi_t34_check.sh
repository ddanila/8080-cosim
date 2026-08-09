#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

CC=${CC:-cc}
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

python3 spinoffs/jukuravi/firmware/build_d0_clocked_pit.py --check
python3 -m py_compile \
  spinoffs/jukuravi/firmware/build_d0_clocked_pit.py \
  tests/jukuravi_t34_clocked_pit_test.py

"$CC" -std=c11 -O2 -Wall -Wextra -Werror -I cosim \
  -o "$tmp/trace" \
  cosim/trace.c cosim/i8080.c cosim/juku_fdc.c cosim/juk_disk.c

python3 tests/jukuravi_t34_clocked_pit_test.py \
  "$tmp/trace" spinoffs/jukuravi/firmware/diag-d0-clocked-pit.bin

echo 'JUKURAVI-T34-CHECK: PASS'
