#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
CC=${CC:-cc}
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

echo "== independent Intel 8080 instruction/flag conformance =="
$CC -std=c11 -O2 -Wall -Wextra -Werror -I cosim \
  -o "$TMP/i8080_conformance_test" tests/i8080_conformance_test.c cosim/i8080.c
"$TMP/i8080_conformance_test"
