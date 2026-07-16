#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")/.."

command -v iverilog >/dev/null || { echo "iverilog not found"; exit 2; }
command -v vvp >/dev/null || { echo "vvp not found"; exit 2; }

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

iverilog -g2012 -s d2_ready_path_tb -o "$tmp/d2_ready_path_tb" hdl/devices.v hdl/sim/d2_ready_path_tb.v
vvp "$tmp/d2_ready_path_tb" > "$tmp/output"
grep -q '^D2-READY-PATH: PASS raw 00->READY 0, raw F/disabled->READY 1$' "$tmp/output"

cat > docs/d2-ready-path-check.md <<'EOF'
# D2 physical READY path check

Status: **PHYSICAL D2 RAW POLARITY EXECUTES THROUGH D30**

This focused HDL guard executes the validated `.037` table as a physical
open-collector PROM. It proves raw row `00` sinks `READY_D` low, raw row `80`
(`F`) releases the modeled R6 pull-up high, either disabled enable releases all
outputs, and D30 section A latches each resulting level on `PHI2TTL`.

```sh
sync/d2_ready_path_check.sh
```

The used D0/pin12 reader channel was Nano D10, not the Nano D13 LED-loaded
channel implicated in the D6 D3 re-read. Direct continuity independently puts
D2.12 on D30.2 and the R6 pull-up. These facts pin D2's raw electrical polarity;
they do not prove the complete cycle-by-cycle WAIT duration or the unresolved
`H` edge contact.
EOF

cat "$tmp/output"
echo "D2-READY-PATH-CHECK: PASS"
