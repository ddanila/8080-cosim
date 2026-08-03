#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

CC=${CC:-cc}
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

python3 spinoffs/jukuravi/firmware/build_d0_buffer_verified.py --check
python3 tests/jukuravi_t28_protocol_test.py
python3 -m py_compile \
  spinoffs/jukuravi/protocol.py \
  spinoffs/jukuravi/host.py \
  spinoffs/jukuravi/firmware/build_d2_loader_v2.py \
  spinoffs/jukuravi/firmware/build_d0_buffer_verified.py \
  tests/jukuravi_t28_*.py

nasm -f bin spinoffs/jukuravi/firmware/return-4000.asm \
  -o "$tmp/return-4000.bin"
cmp "$tmp/return-4000.bin" spinoffs/jukuravi/firmware/return-4000.bin

nasm -f bin spinoffs/jukuravi/firmware/smoke-4000.asm \
  -o "$tmp/smoke-4000.bin"
cmp "$tmp/smoke-4000.bin" spinoffs/jukuravi/firmware/smoke-4000.bin

"$CC" -std=c11 -O2 -Wall -Wextra -Werror -I cosim \
  -o "$tmp/trace" \
  cosim/trace.c cosim/i8080.c cosim/juku_fdc.c cosim/juk_disk.c

rom=spinoffs/jukuravi/firmware/diag-d0-buffer-verified.bin
for test in \
  jukuravi_t28_loader_test.py \
  jukuravi_t28_return_test.py \
  jukuravi_t28_restore_test.py \
  jukuravi_t28_strong_crc_test.py \
  jukuravi_t28_replay_test.py \
  jukuravi_t28_host_replay_test.py \
  jukuravi_t28_attach_test.py \
  jukuravi_t28_smoke_test.py
do
  python3 "tests/$test" "$tmp/trace" "$rom"
done

echo "JUKURAVI-T28-CHECK: PASS"
