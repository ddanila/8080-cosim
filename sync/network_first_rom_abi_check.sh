#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

CC=${CC:-cc}
check_tmp=$(mktemp -d)
trap 'rm -rf "$check_tmp"' EXIT

python3 -m py_compile \
  spinoffs/jukuravi/network-rom/build_network_rom.py \
  tests/network_first_rom_abi_test.py \
  tests/network_first_rom_extended_test.py \
  tests/network_first_rom_c9_test.py \
  tests/network_first_rom_c10_video_test.py \
  tests/network_first_rom_c12_test.py \
  tests/network_first_rom_boot_test.py
python3 spinoffs/jukuravi/network-rom/build_network_rom.py --check

"$CC" -std=c11 -O2 -Wall -Wextra -Werror -I cosim \
  -o "$check_tmp/trace" \
  cosim/trace.c cosim/i8080.c cosim/juku_fdc.c cosim/juk_disk.c
python3 tests/network_first_rom_abi_test.py "$check_tmp/trace"
python3 tests/network_first_rom_locale_test.py "$check_tmp/trace"
python3 tests/network_first_rom_extended_test.py "$check_tmp/trace"
python3 tests/network_first_rom_c9_test.py "$check_tmp/trace"
NETWORK_FIRST_ROM_RELEASE=c10 \
  python3 tests/network_first_rom_c9_test.py "$check_tmp/trace"
python3 tests/network_first_rom_c10_video_test.py "$check_tmp/trace"
python3 tests/network_first_rom_c12_test.py "$check_tmp/trace"
python3 tests/network_first_rom_boot_test.py "$check_tmp/trace"

echo "NETWORK-FIRST-ROM-ABI-CHECK: PASS"
