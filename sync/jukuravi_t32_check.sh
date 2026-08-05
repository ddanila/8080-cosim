#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

CC=${CC:-cc}
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

python3 spinoffs/jukuravi/firmware/build_d0_waitclass.py --check
python3 -m py_compile \
  spinoffs/jukuravi/firmware/build_d0_waitclass.py \
  spinoffs/jukuravi/probe_a12_increment.py \
  spinoffs/jukuravi/probe_pc_a12.py \
  spinoffs/jukuravi/probe_waitclass.py \
  tests/jukuravi_cpu_a12_increment_test.py \
  tests/jukuravi_t32_physical_sessions_test.py \
  tests/jukuravi_t32_low4k_test.py \
  tests/jukuravi_t32_waitclass_test.py
nasm -f bin -DTARGET=0x1A00 -DEXPECTED0=0x3E -DEXPECTED1=0x1A \
  -o "$tmp/rom-read-pair.bin" \
  spinoffs/jukuravi/firmware/rom-read-pair-4000.asm
nasm -f bin -o "$tmp/rom-overlay-source.bin" \
  spinoffs/jukuravi/firmware/rom-overlay-source-4000.asm
for probe in lhld-classes write-map instruction-classes ready-classes boundary increment-registers; do
  nasm -f bin -o "$tmp/$probe.bin" \
    "spinoffs/jukuravi/firmware/ram-a12-$probe-4000.asm"
done

"$CC" -std=c11 -O2 -Wall -Wextra -Werror -I cosim \
  -o "$tmp/trace" \
  cosim/trace.c cosim/i8080.c cosim/juku_fdc.c cosim/juk_disk.c

python3 tests/jukuravi_t32_low4k_test.py \
  "$tmp/trace" spinoffs/jukuravi/firmware/diag-d0-waitclass.bin
python3 tests/jukuravi_t32_waitclass_test.py \
  "$tmp/trace" spinoffs/jukuravi/firmware/diag-d0-waitclass.bin
python3 tests/jukuravi_t32_physical_sessions_test.py
bash sync/jukuravi_vm80a_a12_check.sh
python3 tests/jukuravi_cpu_a12_increment_test.py \
  "$tmp/trace" spinoffs/jukuravi/firmware/diag-d0-waitclass.bin \
  "$tmp/lhld-classes.bin" "$tmp/write-map.bin" \
  "$tmp/instruction-classes.bin" "$tmp/ready-classes.bin" \
  "$tmp/boundary.bin" "$tmp/increment-registers.bin"

# The D1 increment model loses upper-ROM execution in all wait classes and
# follows the physical low-alias stream back to the loader from 1A00h.
for target in 1100 1200 1400; do
  JUKU_CPU_A12_INCREMENT_FAULT=1 \
  JUKU_T32_TARGET="$target" \
  JUKU_T32_PREMARKER=D5 \
  JUKU_T32_EXPECT_LOADER_LOSS=1 \
  JUKU_T32_LOADER_TIMEOUT=2 \
    python3 tests/jukuravi_t32_waitclass_test.py \
      "$tmp/trace" spinoffs/jukuravi/firmware/diag-d0-waitclass.bin
done
for source in 4000 5000; do
  JUKU_CPU_A12_INCREMENT_FAULT=1 \
  JUKU_T32_TARGET=1A00 \
  JUKU_T32_JUMP_ADDRESS="$source" \
  JUKU_T32_PREMARKER=D5 \
  JUKU_T32_EXPECT_MARKER=D5 \
    python3 tests/jukuravi_t32_waitclass_test.py \
      "$tmp/trace" spinoffs/jukuravi/firmware/diag-d0-waitclass.bin
done
# Retain the older fitted 5A00h marker regression separately. The direct D1
# increment model explains its cross-page stream but not the observed first
# fetched 00h, so this remains a bounded historical fit rather than root cause.
JUKU_EXEC_BYTE_FAULT=5A00:00 \
JUKU_ROM_CONSECUTIVE_A12_LOW=1 \
JUKU_T32_TARGET=1A00 \
JUKU_T32_JUMP_ADDRESS=5A00 \
JUKU_T32_PREMARKER=D5 \
JUKU_T32_EXPECT_MARKER=01 \
  python3 tests/jukuravi_t32_waitclass_test.py \
    "$tmp/trace" spinoffs/jukuravi/firmware/diag-d0-waitclass.bin

echo "JUKURAVI-T32-CHECK: PASS"
