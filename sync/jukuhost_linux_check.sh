#!/usr/bin/env bash
# Native Linux build and PTY integration gate.
set -euo pipefail
cd "$(dirname "$0")/.."
sync/jukuhost_linux_build.sh
python3 tests/jukuhost_config_test.py
python3 tests/jukuhost_linux_pty_test.py
