#!/usr/bin/env bash
# Full C8/CP/M Plus simulator session through the native C host.
set -euo pipefail
cd "$(dirname "$0")/.."
sync/jukuhost_linux_build.sh
python3 tests/jukuhost_c8_cosim_test.py
