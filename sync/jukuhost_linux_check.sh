#!/usr/bin/env bash
# Native Linux build and PTY integration gate.
set -euo pipefail
cd "$(dirname "$0")/.."
sha256sum --check tests/fixtures/jukuhost-v15/SHA256SUMS
sync/jukuhost_linux_build.sh
python3 tests/jukuhost_config_test.py
python3 tests/jukuhost_linux_pty_test.py
python3 tests/jukuhost_v15_delayed_pty_test.py
python3 tests/jukuhost_stock_v15_cosim_test.py
python3 tests/jukuhost_serial_reconnect_test.py
python3 tests/python_host_retirement_test.py
