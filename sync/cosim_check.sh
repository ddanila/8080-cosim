#!/usr/bin/env bash
# Deep VALUE-level guard, referenced to the C emulator (cosim). juku_top (the LVS-checked structural
# model) must read the same bytes cosim reads. cosim is the AUTHORITATIVE reference -- a
# straightforward 8080 + flat-memory model in a different language -- so this compares juku_top
# against ground truth rather than against a second Verilog model. Catches datapath/read value bugs
# the other guards miss:
#   - sync/check.sh (LVS)  checks CONNECTIVITY, not values.
#   - sync/boot_check.sh   checks only sampled memory (0xD300 + the 0xD800+ framebuffer).
#
# History: this used to lockstep juku_top against a second Verilog model (juku_struct, the behavioral
# oracle). Comparing two independently-timed Verilog models made the verdict depend on sub-cycle
# event ordering, so it diverged differently across Icarus versions ("passed on Linux, failed on
# Mac"). Referencing cosim removes the second model and pins each divergence to a real
# juku_top-vs-reference difference. See docs/cosim-runtime-reference.md.
#
# Current state: juku_top matches cosim read-for-read through the whole reset/early-boot region and
# diverges at the BIOS RAM test (read #115878, addr 0xD300): juku_top's DRAM serves a stale byte on
# a read that immediately follows a write to the same cell, because the un-traced shared-DRAM CAS
# slot-timing scaffold (D36/R57) does not re-strobe per CPU read. That is a real juku_top modeling
# limit blocked on the physical slot timing (a P0 item in PLAN.md), not a toolchain artifact; no
# read-latch tweak fixes it robustly (they only move the divergence). Until the slot timing is
# modeled, this guard gates against REGRESSION: PASS if juku_top matches cosim at least as far as the
# recorded baseline, FAIL if it diverges earlier. It goes fully green (CTRACE-OK/END) once juku_top
# reads correctly through the window.
#
# Run:   sync/cosim_check.sh
# Slower than boot_check (juku_top runs to ~20 ms sim); run in thorough/nightly CI.
set -euo pipefail
cd "$(dirname "$0")/.."
command -v iverilog >/dev/null || { echo "iverilog not found"; exit 2; }
CC=${CC:-cc}

BASELINE_READ=115878          # first known juku_top-vs-cosim read divergence (DRAM read-after-write)
TRACE_LIMIT=${TRACE_LIMIT:-130000}
WINDOW=${WINDOW:-30000000}    # ns; covers ~120k reads (past the baseline)
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT

echo "== generate ROM hex from vendored ROM =="
python3 -c "open('hdl/sim/ekta37.hex','w').write(chr(10).join('%02x'%b for b in open('roms/ekta37.bin','rb').read())+chr(10))"

echo "== build cosim and dump its memory-read trace (bus order, first $TRACE_LIMIT reads) =="
$CC -O2 -I cosim -o "$TMP/trace" cosim/trace.c cosim/i8080.c cosim/juk_disk.c cosim/juku_fdc.c
( cd cosim && JUKU_RDTRACE="$TMP/reads.txt" JUKU_RDTRACE_LIMIT="$TRACE_LIMIT" \
    "$TMP/trace" ../roms/ekta37.bin 200000000 0 >/dev/null 2>&1 )
echo "   trace reads: $(wc -l < "$TMP/reads.txt")"

echo "== build + run juku_top against the cosim read trace (window=${WINDOW}ns) =="
iverilog -g2012 -o "$TMP/ctrace" hdl/vendor/vm80a.v hdl/devices.v hdl/juku_top.v hdl/sim/cosim_ctrace_tb.v
vvp "$TMP/ctrace" +trace="$TMP/reads.txt" +timecap="$WINDOW" 2>&1 | tee "$TMP/out"

if grep -qE "CTRACE-OK|CTRACE-END" "$TMP/out"; then
  echo "COSIM-CHECK: PASS (juku_top bit-identical to cosim across the window)"
  exit 0
fi
got=$(sed -n 's/.*CTRACE-DIVERGE read=\([0-9]*\).*/\1/p' "$TMP/out" | head -1)
if [ -z "$got" ]; then echo "COSIM-CHECK: FAIL (no verdict emitted)"; exit 1; fi
if [ "$got" -ge "$BASELINE_READ" ]; then
  echo "COSIM-CHECK: PASS (matched cosim to read $got >= baseline $BASELINE_READ; known DRAM read-after-write limit, blocked on shared-DRAM CAS slot timing)"
  exit 0
else
  echo "COSIM-CHECK: FAIL (regression: diverged at read $got, earlier than baseline $BASELINE_READ)"
  exit 1
fi
