#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

CC=${CC:-cc}
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

python3 spinoffs/jukuravi/firmware/build_d0_low4k.py --check
python3 spinoffs/jukuravi/firmware/build_smoke.py --check
python3 -m py_compile \
  spinoffs/jukuravi/host.py \
  spinoffs/jukuravi/firmware/build_d0_resilient.py \
  spinoffs/jukuravi/firmware/build_d2_loader_v2.py \
  spinoffs/jukuravi/firmware/build_d5_loader_v5.py \
  spinoffs/jukuravi/firmware/build_d0_low4k.py \
  tests/jukuravi_t30_boundary_repro_test.py \
  tests/jukuravi_t31_low4k_test.py \
  tests/jukuravi_t31_a12_test.py \
  tests/jukuravi_t31_smoke_test.py

check_rom_read() {
  local target=$1 expected=$2 name=$3
  nasm -f bin -DTARGET="${target}h" -DEXPECTED="${expected}h" \
    spinoffs/jukuravi/firmware/rom-read-one-4000.asm \
    -o "$tmp/$name"
  cmp "$tmp/$name" "spinoffs/jukuravi/firmware/$name"
}

check_rom_read 00017 001 rom-read-0017.bin
check_rom_read 0100C 0B1 rom-read-100C.bin
check_rom_read 01017 0FE rom-read-1017.bin
check_rom_read 0106F 0C3 rom-read-106F.bin
check_rom_read 01070 00C rom-read-1070.bin
check_rom_read 01071 00A rom-read-1071.bin
nasm -f bin spinoffs/jukuravi/firmware/rom-a12-4000.asm \
  -o "$tmp/rom-a12-4000.bin"
cmp "$tmp/rom-a12-4000.bin" \
  spinoffs/jukuravi/firmware/rom-a12-4000.bin
nasm -f bin spinoffs/jukuravi/firmware/rom-exec-106f-4000.asm \
  -o "$tmp/rom-exec-106f.bin"
cmp "$tmp/rom-exec-106f.bin" spinoffs/jukuravi/firmware/rom-exec-106f.bin
nasm -f bin spinoffs/jukuravi/firmware/rom-reenter-4000.asm \
  -o "$tmp/rom-reenter-4000.bin"
cmp "$tmp/rom-reenter-4000.bin" \
  spinoffs/jukuravi/firmware/rom-reenter-4000.bin
nasm -f bin spinoffs/jukuravi/firmware/rom-read-upper-4000.asm \
  -o "$tmp/rom-read-upper-4000.bin"
cmp "$tmp/rom-read-upper-4000.bin" \
  spinoffs/jukuravi/firmware/rom-read-upper-4000.bin
"$CC" -std=c11 -O2 -Wall -Wextra -Werror -I cosim \
  -o "$tmp/trace" \
  cosim/trace.c cosim/i8080.c cosim/juku_fdc.c cosim/juk_disk.c

python3 tests/jukuravi_t30_boundary_repro_test.py \
  "$tmp/trace" spinoffs/jukuravi/firmware/diag-d0-txready.bin
python3 tests/jukuravi_t31_low4k_test.py \
  "$tmp/trace" spinoffs/jukuravi/firmware/diag-d0-low4k.bin
python3 tests/jukuravi_t31_a12_test.py \
  "$tmp/trace" spinoffs/jukuravi/firmware/diag-d0-low4k.bin
python3 tests/jukuravi_t31_smoke_test.py \
  "$tmp/trace" spinoffs/jukuravi/firmware/diag-d0-low4k.bin

echo "JUKURAVI-T31-CHECK: PASS"
