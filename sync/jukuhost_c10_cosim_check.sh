#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

JUKUHOST_ROM_RELEASE=c10 python3 tests/jukuhost_c8_cosim_test.py
JUKUHOST_ROM_RELEASE=c10 JUKUHOST_C8_REPLACE_HOST=1 \
  python3 tests/jukuhost_c8_cosim_test.py

echo "JUKUHOST-C10-COSIM-CHECK: PASS"
