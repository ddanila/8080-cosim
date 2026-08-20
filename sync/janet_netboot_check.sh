#!/usr/bin/env bash
# Native EktaSoft NetBios/Janet serial-network boot guard.
set -euo pipefail
cd "$(dirname "$0")/.."
CC=${CC:-cc}
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

$CC -O2 -I cosim -o "$TMP/trace" \
  cosim/trace.c cosim/i8080.c cosim/juk_disk.c cosim/juku_fdc.c
python3 tests/jukuhost_contract_test.py
python3 tests/janet_disk_server_test.py
python3 tests/janet_fastboot_protocol_test.py
python3 tests/janet_netboot_test.py "$TMP/trace"
