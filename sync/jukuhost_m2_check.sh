#!/usr/bin/env bash
# Complete native-Linux parity and Python-host-retirement gate.
set -euo pipefail
cd "$(dirname "$0")/.."

# Frozen Python-era behavioral oracle and all five stock systems.
sync/janet_netboot_check.sh

# Portable/native C runtime, PTYs, media safety, evidence, and reconnect.
sync/jukuhost_linux_check.sh

# Production C host against stock and current C8/V16 simulator workloads.
sync/jukuhost_stock_cosim_check.sh
sync/jukuhost_c8_cosim_check.sh

# Normal operational wrapper and current ROM ABI/fault regressions.
python3 tests/juku_run_host_test.py
sync/network_first_rom_abi_check.sh

echo "JUKUHOST-M2-CHECK: PASS (Linux parity; C-only production host)"
