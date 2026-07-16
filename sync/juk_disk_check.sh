#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

CC=${CC:-cc}
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

"$CC" -std=c11 -Wall -Wextra -Werror -I cosim \
  -o "$tmp/juk_disk_test" \
  tests/juk_disk_test.c cosim/juk_disk.c
"$tmp/juk_disk_test"

"$CC" -std=c11 -Wall -Wextra -Werror -I cosim \
  -o "$tmp/juku_fdc_test" \
  tests/juku_fdc_test.c cosim/juku_fdc.c cosim/juk_disk.c
"$tmp/juku_fdc_test"

"$CC" -std=c11 -Wall -Wextra -Werror -I cosim \
  -o "$tmp/rombios_fdc_write_test" \
  tests/rombios_fdc_write_test.c cosim/i8080.c cosim/juku_fdc.c cosim/juk_disk.c

"$CC" -std=c11 -O2 -Wall -Wextra -Werror -I cosim \
  -o "$tmp/trace" \
  cosim/trace.c cosim/i8080.c cosim/juku_fdc.c cosim/juk_disk.c
root=$PWD
(
  cd "$tmp"
  JUKU_CHECKPOINT_PREFIX="$tmp/rombios-init" \
  JUKU_CHECKPOINT_CYC=3200000 \
    "$tmp/trace" "$root/roms/ekta37.bin" 3300000 0 200000 >/dev/null 2>/dev/null
)
"$tmp/rombios_fdc_write_test" "$tmp/rombios-init.ram"
