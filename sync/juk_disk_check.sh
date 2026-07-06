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
