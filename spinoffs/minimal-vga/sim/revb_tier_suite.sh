#!/usr/bin/env bash
# VJUGA rev B — B0 tier suite. One command that runs every B0-phase gate:
# shared-commons guard, per-card unit TBs, the bus-conflict assertion, and the
# assembled-backplane banner boot (byte-identical to cosim, both decode modes).
# Deeper tier suites (jmon33 / keyboard-react at B3, FDC/EKDOS at B4) attach here
# as those tiers come online.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"

echo "== rev B: shared-commons guard =="
python3 scripts/check_spinoff_commons.py

echo "== rev B: per-card unit TBs (BFM) =="
spinoffs/minimal-vga/sim/revb_card_tb_check.sh

echo "== rev B: bus-conflict assertion =="
spinoffs/minimal-vga/sim/revb_bus_assert_check.sh

echo "== rev B: modular backplane boots ekta37 byte-identical to cosim (banner) =="
spinoffs/minimal-vga/sim/revb_boot_check.sh

echo "REVB-TIER-SUITE(B0): PASS"
