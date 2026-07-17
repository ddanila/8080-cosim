#!/usr/bin/env bash
# Guard the К555ИЕ10 / 74LS161 package and the traced D103/D33 /13 loop.
set -euo pipefail
cd "$(dirname "$0")/.."

command -v iverilog >/dev/null || { echo "iverilog not found"; exit 2; }
command -v vvp >/dev/null || { echo "vvp not found"; exit 2; }

REPORT=${IE10_REPORT:-docs/ie10-counter-readiness.md}
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

iverilog -g2012 -s ie10_ctr_tb -o "$TMP/ie10_ctr_tb" \
  hdl/devices.v hdl/sim/ie10_ctr_tb.v
vvp "$TMP/ie10_ctr_tb" > "$TMP/ie10.out"
pass_line=$(grep -m1 '^IE10-CTR: PASS' "$TMP/ie10.out" || true)
if [ -z "$pass_line" ]; then
  cat "$TMP/ie10.out"
  echo "IE10-CHECK: FAIL"
  exit 1
fi

cat > "$REPORT" <<EOF
# К555ИЕ10 / 74LS161 counter readiness

Status: **PACKAGE AND TRACED D103 /13 LOOP GUARDED**

The \`ie10_ctr\` primitive models the К555ИЕ10 / SN74LS161A-class package at
D103. The structural top now uses the source-proved \`0011\` preset instead of
the former placeholder zero, so D103 RCO through inverter D33 back to D103
\`/LOAD\` executes the traced modulo-13 circuit.

## Primary specification

Texas Instruments, *SN54160 through SN54163, SN54LS160A through SN54LS163A,
SN74LS160A through SN74LS163A — Synchronous 4-Bit Counters*, SDLS060,
October 1976, revised March 1988:

<https://www.ti.com/lit/ds/symlink/sn74ls161a.pdf>

The guard covers:

- active-low direct/asynchronous clear;
- active-low synchronous parallel load with priority over counting;
- independent ENP and ENT count gating;
- all sixteen binary states and wrap;
- combinational ENT-qualified terminal RCO; and
- the board-proved D103 RCO -> D33 inverter -> \`/LOAD\` loop, which repeats
  \`3..F\` every 13 input clocks and drives Q3's labeled 1.23 MHz rail from 16 MHz.

## Command

\`\`\`sh
sync/ie10_check.sh
\`\`\`

## Result

\`\`\`text
$pass_line
\`\`\`

## Evidence boundary

This closes D103's standard digital behavior and the already traced local /13
feedback topology. The native sheet still does not visibly close the upstream
OSC-to-XTAL16M bundle, so \`XTAL16M\` remains a physical continuity boundary; the
runnable raster continues to use its explicit simulation dot-clock input.
EOF

echo "$pass_line"
echo "IE10-CHECK: PASS"
