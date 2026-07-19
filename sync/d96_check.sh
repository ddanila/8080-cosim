#!/usr/bin/env bash
# Guard the source-closed D96 read-clock divide-by-two toggle.
set -euo pipefail
cd "$(dirname "$0")/.."

command -v iverilog >/dev/null || { echo "iverilog not found"; exit 2; }
command -v vvp >/dev/null || { echo "vvp not found"; exit 2; }

REPORT=${D96_REPORT:-docs/d96-read-clock-readiness.md}
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

iverilog -g2012 -s fdc_read_clock_toggle_tb -o "$TMP/d96_tb" \
  hdl/devices.v hdl/sim/fdc_read_clock_toggle_tb.v
vvp "$TMP/d96_tb" > "$TMP/d96.out"
pass_line=$(grep -m1 '^D96-RCLK: PASS' "$TMP/d96.out" || true)
if [ -z "$pass_line" ]; then
  cat "$TMP/d96.out"
  echo "D96-CHECK: FAIL"
  exit 1
fi

cat > "$REPORT" <<EOF
# D96 FDC read-clock readiness

Status: **SOURCE-CLOSED / STRUCTURAL AND BEHAVIORAL CONTRACT GUARDED**

Recovered \`.009\` Э3 sheet 3 closes D96 section 1 as the read-clock
divide-by-two toggle: WREQ_N drives both active-low asynchronous controls,
/Q feeds D, the D28/R85 recovered-clock node clocks the flip-flop, and Q drives
D93 RCLK. The undrawn second half is unused; pin 8 retains its independently
photo-proved isolated test landing and pins 9-13 are explicit no-connects.

## Command

\`\`\`sh
sync/d96_check.sh
\`\`\`

## Result

\`\`\`text
$pass_line
\`\`\`

## Evidence boundary

This guard proves the digital WREQ reset/restart and divide-by-two behavior.
It does not replace bench measurement of D28/R85 open-collector rise time,
duty cycle, D96 setup/hold margin, or separator lock over both 4/8 MHz modes.
Exact connectivity is guarded separately by
\`kicad/check_fdc_read_clock_toggle.py\` and documented in
\`ref/schematics/fdc-read-clock-toggle-map.md\`.
EOF

echo "$pass_line"
echo "D96-CHECK: PASS"
