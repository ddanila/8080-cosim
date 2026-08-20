#!/usr/bin/env bash
# Five frozen stock systems plus automatic Janet identity through the C host.
set -euo pipefail
cd "$(dirname "$0")/.."
sync/jukuhost_linux_build.sh
python3 tests/jukuhost_stock_cosim_test.py
