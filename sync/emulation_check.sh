#!/usr/bin/env bash
# Fast native consumer checks only: no HDL, PTY, firmware or disk images.
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ ! -f third_party/dac-emulation/machines/juku/juku.c ]]; then
  echo 'Initialize the emulator: git submodule update --init third_party/dac-emulation' >&2
  exit 1
fi
CC=${CC:-cc}
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
# Deliberately omit -I: sibling CP/M repositories use this exact source contract.
"$CC" -std=c11 -O2 -Wall -Wextra -Werror -o "$work/trace" \
  cosim/trace.c cosim/i8080.c cosim/juk_disk.c cosim/juku_fdc.c
"$CC" -std=c11 -O2 -Wall -Wextra -Werror -o "$work/cpu" \
  tests/i8080_conformance_test.c cosim/i8080.c
"$work/cpu"
"$CC" -std=c11 -O2 -Wall -Wextra -Werror -o "$work/disk" \
  tests/juk_disk_test.c cosim/juk_disk.c
"$work/disk"
"$CC" -std=c11 -O2 -Wall -Wextra -Werror -o "$work/fdc" \
  tests/juku_fdc_test.c cosim/juku_fdc.c cosim/juk_disk.c
"$work/fdc"
python3 tests/cosim_watch_checkpoint_test.py "$work/trace"
python3 tests/cosim_pit_latch_test.py "$work/trace"
