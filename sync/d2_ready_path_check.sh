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
# D2 READY polarity simulation check

Status: **CAPTURED D2 RAW POLARITY GUARDED IN HDL**

This focused HDL bench loads the captured `.037` table into an open-collector
PROM model. It checks that address `00` sinks `READY_D`, address `80` (raw `F`)
releases the modeled pull-up, and either disabled enable releases all outputs.
D30 section A samples the low and released levels on `PHI2TTL`; its asynchronous
controls are held inactive in this bench.

Run from the repository root with a POSIX shell and Icarus Verilog
(`iverilog` and `vvp`). The model reads
`ref/physical-proms/validated/d2_037.raw.hex`. Simulation files are temporary;
the command overwrites this report only after the checks pass.

```sh
sync/d2_ready_path_check.sh
```

The acquisition and independent D2.12-to-D30.2/R6 continuity evidence are
recorded in [D2 physical truth](d2-physical-truth.md). This bench checks the
model's sampling polarity; it does not measure hardware or exercise the
D38 status strobe, H/DBIN gating, or complete cycle-by-cycle WAIT duration.
See [memory timing](memory-timing-boundary.md) for the remaining boundary.
EOF

cat "$tmp/output"
echo "D2-READY-PATH-CHECK: PASS"
