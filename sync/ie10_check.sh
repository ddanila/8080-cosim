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
D103. The structural top uses the source-proved \`0011\` preset; D103 RCO
through inverter D33 back to D103
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

Run from the repository root with Bash and Icarus Verilog (\`iverilog\` and
\`vvp\`). Compilation and simulation logs use a temporary directory, removed
on exit. After a passing simulation, the script overwrites this report; set
\`IE10_REPORT\` to select another path whose parent directory already exists.

\`\`\`sh
sync/ie10_check.sh
\`\`\`

## Result

\`\`\`text
$pass_line
\`\`\`

## Evidence boundary

The Icarus test instantiates the primitive and a separate modulo-13 fixture
with inverted RCO feedback. It does not compile the complete board, check JSON
or PCB connections, verify the PDF hash, or measure clock frequency. The
1.23 MHz figure is the nominal 16 MHz / 13 relationship.

The native sheet still does not visibly close the upstream
OSC-to-XTAL16M bundle, so \`XTAL16M\` remains a physical continuity boundary; the
runnable raster continues to use its explicit simulation dot-clock input.

The marked К555ИЕ10 in owner tile \`PXL_20260710_200445914.jpg\` has a
separate two-sided local fit; its reflected solder rows are visible in
\`PXL_20260710_200530933.MP.jpg\`. Pins 12–14 have distinct joints without
visible copper departure on either face. The nearby horizontal traces run
between the joints. This supports the exact-sheet NC treatment of Q2/Q1/Q0;
it does not close D103.2's upstream XTAL16M source.
EOF

echo "$pass_line"
echo "IE10-CHECK: PASS"
