#!/usr/bin/env bash
# VJUGA rev B bus-conflict assertion check (Phase B0). Proves the bus monitor
# fires on an injected two-driver conflict and stays quiet for legal patterns.
# The full-boot conflict-clean check lives in sim/revb_boot_check.sh (it fails if
# any REVB-BUS-CONFLICT line appears during the ekta37 boot).
set -euo pipefail
MV="$(cd "$(dirname "$0")/.." && pwd)"
REVB="$MV/hdl/revb"
command -v iverilog >/dev/null || { echo "iverilog not found"; exit 2; }
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT

iverilog -g2012 -o "$TMP/mon" "$REVB/revb_bus_monitor.v" "$REVB/revb_bus_monitor_tb.v" 2>/dev/null
out=$(vvp "$TMP/mon" 2>/dev/null || true)
if echo "$out" | grep -q "REVB-BUS-MONITOR-TB: PASS" \
   && echo "$out" | grep -q "REVB-BUS-CONFLICT"; then
  echo "  ok    monitor stays quiet for one-hot and fires on injected conflict"
  echo "REVB-BUS-ASSERT-CHECK: PASS"
else
  echo "  FAIL  monitor did not behave as expected:"; echo "$out" | sed 's/^/        /'
  echo "REVB-BUS-ASSERT-CHECK: FAIL"; exit 1
fi
