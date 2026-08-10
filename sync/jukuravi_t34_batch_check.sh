#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

CC=${CC:-cc}
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

python3 spinoffs/jukuravi/firmware/build_d0_clocked_pit.py --check
python3 -m py_compile \
  spinoffs/jukuravi/host.py \
  spinoffs/jukuravi/batch.py \
  tests/jukuravi_host_config_first_test.py \
  tests/jukuravi_t34_batch_test.py \
  tests/jukuravi_t34_physical_sessions_test.py
python3 tests/jukuravi_host_config_first_test.py
python3 tests/jukuravi_t34_physical_sessions_test.py

for probe in cpu-pit-ratio d57-raw; do
  nasm -f bin \
    -o "$tmp/$probe.bin" \
    "spinoffs/jukuravi/firmware/$probe-4000.asm"
  test -s "$tmp/$probe.bin"
done

"$CC" -std=c11 -O2 -Wall -Wextra -Werror -I cosim \
  -o "$tmp/trace" \
  cosim/trace.c cosim/i8080.c cosim/juku_fdc.c cosim/juk_disk.c

python3 tests/jukuravi_t34_batch_test.py \
  "$tmp/trace" spinoffs/jukuravi/firmware/diag-d0-clocked-pit.bin

echo 'JUKURAVI-T34-BATCH-CHECK: PASS'
