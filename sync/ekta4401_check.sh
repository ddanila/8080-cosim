#!/usr/bin/env bash
# Guard the ekta4401 remix ROM: deterministic rebuild from pinned ekta37,
# bounded patch set, the ROM's own eight chunk checksums, and a cosim boot
# proving the relocated command table, H help, V visual demo, and J loader
# startup execute.
# See spinoffs/jukuravi/EKTA37-REMIX-PLAN.md.
set -euo pipefail
cd "$(dirname "$0")/.."

CC=${CC:-cc}
check_tmp=$(mktemp -d)
trap 'rm -rf "$check_tmp"' EXIT

python3 -m py_compile \
  spinoffs/jukuravi/remix/build_ekta4401.py \
  tests/ekta4401_remix_test.py

python3 spinoffs/jukuravi/remix/build_ekta4401.py --check

"$CC" -std=c11 -O2 -Wall -Wextra -Werror -I cosim \
  -o "$check_tmp/trace" \
  cosim/trace.c cosim/i8080.c cosim/juku_fdc.c cosim/juk_disk.c

python3 tests/ekta4401_remix_test.py "$check_tmp/trace"

echo "EKTA4401-CHECK: PASS"
