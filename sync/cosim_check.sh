#!/usr/bin/env bash
# Deep CPU-bus guard, referenced to the C emulator (cosim). juku_top (the LVS-checked structural
# model) must perform the same memory reads/writes and I/O reads/writes in the same order and with
# the same values. The shared format also supports interrupt acknowledges, whose path is exercised
# by focused interrupt guards. cosim is the AUTHORITATIVE reference -- a
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
# Current state: juku_top matches cosim across the complete bounded trace. The РУ5 model follows
# the 4164 early/delayed-write contract, while the functional D53 scaffold holds RAS from the row
# phase through the CAS column pulse. Any address or data divergence is a hard failure.
#
# Run:   sync/cosim_check.sh
# Slower than boot_check (juku_top runs to ~20 ms sim); run in thorough/nightly CI.
set -euo pipefail
cd "$(dirname "$0")/.."
command -v iverilog >/dev/null || { echo "iverilog not found"; exit 2; }
CC=${CC:-cc}

TRACE_LIMIT=${TRACE_LIMIT:-130000}
WINDOW=${WINDOW:-30000000}    # ns; covers the complete default 130k-event trace
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT

echo "== generate ROM hex from vendored ROM =="
python3 -c "open('hdl/sim/ekta37.hex','w').write(chr(10).join('%02x'%b for b in open('roms/ekta37.bin','rb').read())+chr(10))"

echo "== build cosim and dump its unified CPU-bus trace (first $TRACE_LIMIT events) =="
$CC -O2 -I cosim -o "$TMP/trace" cosim/trace.c cosim/i8080.c cosim/juk_disk.c cosim/juku_fdc.c
( cd cosim && JUKU_BUS_TRACE="$TMP/bus-events.txt" JUKU_BUS_TRACE_LIMIT="$TRACE_LIMIT" \
    "$TMP/trace" ../roms/ekta37.bin 200000000 0 >/dev/null 2>&1 )
echo "   trace events: $(wc -l < "$TMP/bus-events.txt")"
awk '{ count[$1]++ } END { for (kind in count) printf "   %-2s %d\n", kind, count[kind] }' \
  "$TMP/bus-events.txt" | sort
event_count=$(wc -l < "$TMP/bus-events.txt")
if [ "$event_count" -ne "$TRACE_LIMIT" ]; then
  echo "COSIM-CHECK: FAIL (cosim emitted $event_count events, expected $TRACE_LIMIT)"
  exit 1
fi
awk '
  $1 !~ /^(MR|MW|IR|IW|IA)$/ { bad = 1 }
  { seen[$1] = 1 }
  END {
    if (bad || !seen["MR"] || !seen["MW"] || !seen["IR"] || !seen["IW"])
      exit 1
  }
' "$TMP/bus-events.txt" || {
  echo "COSIM-CHECK: FAIL (malformed trace or default boot omitted MR/MW/IR/IW coverage)"
  exit 1
}

echo "== build + run juku_top against the cosim bus trace (window=${WINDOW}ns) =="
iverilog -g2012 -o "$TMP/ctrace" hdl/vendor/vm80a.v hdl/devices.v hdl/juku_top.v hdl/sim/cosim_ctrace_tb.v
vvp "$TMP/ctrace" +trace="$TMP/bus-events.txt" +timecap="$WINDOW" 2>&1 | tee "$TMP/out"

if grep -qE "BTRACE-OK|BTRACE-END" "$TMP/out"; then
  echo "COSIM-CHECK: PASS (juku_top CPU-bus events match cosim across the window)"
  exit 0
fi
echo "COSIM-CHECK: FAIL (address/data divergence or no verdict emitted)"
exit 1
