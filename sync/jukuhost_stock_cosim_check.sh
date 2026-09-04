#!/usr/bin/env bash
# Five frozen stock systems plus automatic Janet identity through the C host.
set -euo pipefail
cd "$(dirname "$0")/.."
sync/jukuhost_linux_build.sh
python3 tests/jukuhost_stock_cosim_test.py
CPM_PLUS_JUKU_ROOT=${CPM_PLUS_JUKU_ROOT:-../cpm-plus-juku} \
    python3 tests/jukuhost_stock_recovery_cosim_test.py
