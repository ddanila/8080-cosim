#!/usr/bin/env bash
# Guard the digital beeper source: D57 (8253 #3) channel 1 must be programmable
# and toggle the traced SOUND net.
set -euo pipefail
cd "$(dirname "$0")/.."
command -v iverilog >/dev/null || { echo "iverilog not found"; exit 2; }
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT

echo "== HDL D57 SOUND channel check =="
iverilog -g2012 -o "$TMP/beeper_path_tb" hdl/vendor/vm80a.v hdl/devices.v hdl/sim/beeper_path_tb.v
out=$(vvp "$TMP/beeper_path_tb")
echo "$out"
if ! printf '%s\n' "$out" | grep -q "BEEPER-PATH: PASS"; then
  echo "BEEPER-CHECK: FAIL"
  exit 1
fi

cat > docs/beeper-readiness.md <<'EOF'
# Beeper readiness

Status: **DIGITAL BEEPER SOURCE READY**

This guard proves the runnable digital source of the Juku beeper path:

- D57 is the third 8253 PIT (`0x18..0x1B`), and channel 1 / `OUT1` is the
  traced `SOUND` source.
- `hdl/sim/beeper_path_tb.v` programs D57 channel 1 with a small reload value
  and requires `OUT1` to toggle.
- The physical analog path after `SOUND` is already traced in the board data:
  `D57.OUT1 -> R90 -> VT1/VD4/R91 clamp -> R48 -> SPKR`.

## Command

```sh
sync/beeper_check.sh
```

## Evidence

| Check | Result |
| --- | --- |
| D57 channel 1 accepts control/data writes | PASS |
| D57 `OUT1` / `SOUND` toggles after programming | PASS |

## Remaining Boundary

- This is a digital source guard, not an analog speaker model. Physical bring-up
  still needs the speaker unit, clamp polarity, and level/current check on real
  hardware.
EOF

echo "BEEPER-CHECK: PASS"
echo "Wrote docs/beeper-readiness.md"
