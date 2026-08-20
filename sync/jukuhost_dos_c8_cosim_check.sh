#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
sync/jukuhost_dos_build.sh
tools/package-jukuhost-dos.py
python3 tests/jukuhost_dos_stock_cosim_test.py
python3 tests/jukuhost_dos_c8_cosim_test.py
