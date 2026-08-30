#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

JUKUHOST_ROM_RELEASE=c11 python3 tests/jukuhost_c8_cosim_test.py
JUKUHOST_ROM_RELEASE=c11 JUKUHOST_C8_REPLACE_HOST=1 \
  python3 tests/jukuhost_c8_cosim_test.py

echo "JUKUHOST-C11-COSIM-CHECK: PASS"
