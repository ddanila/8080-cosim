#!/usr/bin/env bash
# Guard the К555ИЕ7 / 74LS193 primitive used by D44-D47 and FDC-area D106.
set -euo pipefail
cd "$(dirname "$0")/.."

command -v iverilog >/dev/null || { echo "iverilog not found"; exit 2; }
command -v vvp >/dev/null || { echo "vvp not found"; exit 2; }

REPORT=${IE7_REPORT:-docs/ie7-counter-readiness.md}
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

iverilog -g2012 -s ie7_ctr_tb -o "$TMP/ie7_ctr_tb" \
  hdl/devices.v hdl/sim/ie7_ctr_tb.v
vvp "$TMP/ie7_ctr_tb" > "$TMP/ie7.out"
pass_line=$(grep -m1 '^IE7-CTR: PASS' "$TMP/ie7.out" || true)
if [ -z "$pass_line" ]; then
  cat "$TMP/ie7.out"
  echo "IE7-CHECK: FAIL"
  exit 1
fi

cat > "$REPORT" <<EOF
# К555ИЕ7 / 74LS193 counter readiness

Status: **FULL DIGITAL DEVICE CONTRACT GUARDED**

The shared \`ie7_ctr\` primitive models the standard К555ИЕ7 / SN74LS193
package used at video-address counters D44-D47 and identified at FDC data-
separator position D106.

## Primary specification

Texas Instruments, *SN54192, SN54193, SN54LS192, SN54LS193, SN74192,
SN74193, SN74LS192, SN74LS193 — Synchronous 4-Bit Up/Down Counters (Dual
Clock With Clear)*, SDLS074, December 1972, revised March 1988:

<https://www.ti.com/lit/ds/symlink/sn74ls193.pdf>

The guarded contract is:

- active-high asynchronous clear, independent of load and clocks;
- active-low asynchronous parallel load, including data changes while held low;
- rising-edge up/down counting only while the opposite clock is high;
- modulo-16 wrap in both directions;
- active-low carry and borrow pulses equal to the low clock phase at terminal
  counts \`F\` and \`0\`;
- two-package carry and borrow cascade without an early or late digit change.

## Command

\`\`\`sh
sync/ie7_check.sh
\`\`\`

## Result

\`\`\`text
$pass_line
\`\`\`

## Evidence boundary

This closes the standard package's digital behavior. Recovered \`.009\` Э3
sheet 3 independently closes the board wiring around D106: D95.9 clocks DOWN,
R78 pulls UP and all four preset inputs high, D97.4/D93.27 RAW READ drives
/LOAD, CLR is grounded, Q3 drives D28.9, and Q0-Q2 plus /CO and /BO are explicit
no-connects. The downstream D28/R85/D96 waveform quality and separator lock
margin remain board bring-up measurements even though D96 connectivity is now
source-closed.
EOF

echo "$pass_line"
echo "IE7-CHECK: PASS"
