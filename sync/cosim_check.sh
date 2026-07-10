#!/usr/bin/env bash
# Deep VALUE-level guard: juku_top (the LVS-checked structural model) must execute BIT-IDENTICALLY
# to juku_struct (the behavioral reference oracle). Locksteps both on one clock+ROM and fails on the
# first divergent read. Catches datapath value bugs that the other guards miss:
#   - sync/check.sh (LVS)      checks CONNECTIVITY, not values.
#   - sync/boot_check.sh       checks only sampled memory (0xD300 + the 0xD800+ framebuffer).
# This guard found the DRAM CAS-timing write bug (a dropped write at 0xD441, silent to both above).
# Slower than boot_check (two DUTs in lockstep) -> run in thorough/nightly CI, not every commit.
#
# Run:   sync/cosim_check.sh            # default window (covers boot + full banner)
#        WINDOW=800000000 sync/cosim_check.sh   # shorter window (faster, boot + early banner)
# Runtime baseline and progress-output notes: docs/cosim-runtime-reference.md
set -euo pipefail
cd "$(dirname "$0")/.."
command -v iverilog >/dev/null || { echo "iverilog not found"; exit 2; }
WINDOW=${WINDOW:-1600000000}          # ns; 1.6e9 reaches past the banner draw (~833k reads)
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT

echo "== generate ROM hex from vendored ROM =="
python3 -c "open('hdl/sim/ekta37.hex','w').write(chr(10).join('%02x'%b for b in open('roms/ekta37.bin','rb').read())+chr(10))"

echo "== build co-sim (juku_top structural vs juku_struct oracle) =="
iverilog -g2012 -o "$TMP/cosim" hdl/vendor/vm80a.v hdl/devices.v hdl/juku_top.v \
         hdl/sim/juku_struct.v hdl/sim/cosim_diff_tb.v

echo "== run lockstep diff (window=${WINDOW}ns) =="
vvp "$TMP/cosim" +timecap="$WINDOW" 2>&1 | tee "$TMP/cosim.out"
if grep -q "NO-DIVERGE" "$TMP/cosim.out"; then
  echo "COSIM-CHECK: PASS (juku_top bit-identical to the oracle)"
else
  echo "COSIM-CHECK: FAIL"; exit 1
fi
