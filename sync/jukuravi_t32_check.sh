#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

CC=${CC:-cc}
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

python3 spinoffs/jukuravi/firmware/build_d0_waitclass.py --check
python3 -m py_compile \
  spinoffs/jukuravi/firmware/build_d0_waitclass.py \
  spinoffs/jukuravi/probe_a12_path.py \
  spinoffs/jukuravi/probe_pc_a12.py \
  spinoffs/jukuravi/probe_waitclass.py \
  tests/jukuravi_ram_a12_alias_test.py \
  tests/jukuravi_t32_low4k_test.py \
  tests/jukuravi_t32_waitclass_test.py
nasm -f bin -DTARGET=0x1A00 -DEXPECTED0=0x3E -DEXPECTED1=0x1A \
  -o "$tmp/rom-read-pair.bin" \
  spinoffs/jukuravi/firmware/rom-read-pair-4000.asm
nasm -f bin -o "$tmp/rom-overlay-source.bin" \
  spinoffs/jukuravi/firmware/rom-overlay-source-4000.asm
nasm -f bin -o "$tmp/ram-a12-alias-regions.bin" \
  spinoffs/jukuravi/firmware/ram-a12-alias-regions-4000.asm

"$CC" -std=c11 -O2 -Wall -Wextra -Werror -I cosim \
  -o "$tmp/trace" \
  cosim/trace.c cosim/i8080.c cosim/juku_fdc.c cosim/juk_disk.c

python3 tests/jukuravi_t32_low4k_test.py \
  "$tmp/trace" spinoffs/jukuravi/firmware/diag-d0-waitclass.bin
python3 tests/jukuravi_t32_waitclass_test.py \
  "$tmp/trace" spinoffs/jukuravi/firmware/diag-d0-waitclass.bin
python3 tests/jukuravi_ram_a12_alias_test.py \
  "$tmp/trace" spinoffs/jukuravi/firmware/diag-d0-waitclass.bin \
  "$tmp/ram-a12-alias-regions.bin"

# Reproduce the complete CS00015 upper-ROM failure signature.  Once D15 has
# supplied one byte, consecutive reads alias through A12=0.  That loses the
# loader at three representative entries but accidentally reaches 0A0Ch from
# 1A00h without changing the RAM premarker.  The independently observed bad
# first opcode at 5A00h accounts for its CALL/JUMP marker distinction.
for target in 1100 1200 1400; do
  JUKU_ROM_CONSECUTIVE_A12_LOW=1 \
  JUKU_T32_TARGET="$target" \
  JUKU_T32_PREMARKER=D5 \
  JUKU_T32_EXPECT_LOADER_LOSS=1 \
  JUKU_T32_LOADER_TIMEOUT=2 \
    python3 tests/jukuravi_t32_waitclass_test.py \
      "$tmp/trace" spinoffs/jukuravi/firmware/diag-d0-waitclass.bin
done
for source in 4000 5000; do
  JUKU_ROM_CONSECUTIVE_A12_LOW=1 \
  JUKU_T32_TARGET=1A00 \
  JUKU_T32_JUMP_ADDRESS="$source" \
  JUKU_T32_PREMARKER=D5 \
  JUKU_T32_EXPECT_MARKER=D5 \
    python3 tests/jukuravi_t32_waitclass_test.py \
      "$tmp/trace" spinoffs/jukuravi/firmware/diag-d0-waitclass.bin
done
JUKU_EXEC_BYTE_FAULT=5A00:00 \
JUKU_ROM_CONSECUTIVE_A12_LOW=1 \
JUKU_T32_TARGET=1A00 \
JUKU_T32_JUMP_ADDRESS=5A00 \
JUKU_T32_PREMARKER=D5 \
JUKU_T32_EXPECT_MARKER=01 \
  python3 tests/jukuravi_t32_waitclass_test.py \
    "$tmp/trace" spinoffs/jukuravi/firmware/diag-d0-waitclass.bin

echo "JUKURAVI-T32-CHECK: PASS"
