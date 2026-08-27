#!/bin/sh
# Full C9/CP/M Plus simulator session through the native C host.
set -eu
cd "$(dirname "$0")/.."
JUKUHOST_ROM_RELEASE=c9 python3 tests/jukuhost_c8_cosim_test.py
JUKUHOST_ROM_RELEASE=c9 JUKUHOST_C8_REPLACE_HOST=1 \
  python3 tests/jukuhost_c8_cosim_test.py
