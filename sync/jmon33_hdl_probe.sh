#!/usr/bin/env bash
# Prove that jmon33 runs far enough on the LVS-checked juku_top model to write
# video RAM with frame interrupts enabled.
set -euo pipefail
cd "$(dirname "$0")/.."
command -v iverilog >/dev/null || { echo "iverilog not found"; exit 2; }
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT

MAXVRAM=${JMON33_HDL_MAXVRAM:-1}
FRAMEIRQ=${JMON33_HDL_FRAMEIRQ:-200000}
TIMECAP=${JMON33_HDL_TIMECAP:-120000000}

echo "== generate jmon33 readmemh image =="
python3 - <<'PY'
from pathlib import Path
rom = Path("roms/jmon33.bin").read_bytes()
Path("hdl/sim/jmon33.hex").write_text("\n".join(f"{byte:02x}" for byte in rom) + "\n")
PY

echo "== juku_top jmon33 HDL probe =="
iverilog -g2012 -o "$TMP/juku_top_jmon33" hdl/vendor/vm80a.v hdl/devices.v hdl/juku_top.v hdl/sim/juku_top_tb.v
out=$(vvp "$TMP/juku_top_jmon33" +rom=hdl/sim/jmon33.hex +frameirq="$FRAMEIRQ" +maxvram="$MAXVRAM" +timecap="$TIMECAP")
echo "$out"

first=$(printf '%s\n' "$out" | sed -n 's/.*first video write @0x\([0-9a-fA-F]*\).*/\1/p' | head -1)
writes=$(printf '%s\n' "$out" | sed -n 's/.*\[VRAM\] \([0-9][0-9]*\) writes.*/\1/p' | head -1)
mcyc=$(printf '%s\n' "$out" | sed -n 's/.*first video write @0x[0-9a-fA-F]* mcyc=\([0-9][0-9]*\).*/\1/p' | head -1)

if [ "${first,,}" != "ff40" ] || [ "$writes" != "$MAXVRAM" ]; then
  echo "JMON33-HDL-PROBE: FAIL"
  exit 1
fi

cat > docs/jmon33-hdl-probe.md <<EOF
# jmon33 HDL probe

Status: **JMON33 REACHES VIDEO RAM ON JUKU_TOP**

This probe runs the Monitor 3.3 ROM on the LVS-checked structural model
\`juku_top\` with frame interrupts enabled. It proves that the HDL twin reaches
jmon33's first video-memory write instead of only proving the path in cosim.

## Command

\`\`\`sh
sync/jmon33_hdl_probe.sh
\`\`\`

Environment overrides:

- \`JMON33_HDL_MAXVRAM\` default \`$MAXVRAM\`
- \`JMON33_HDL_FRAMEIRQ\` default \`$FRAMEIRQ\`
- \`JMON33_HDL_TIMECAP\` default \`$TIMECAP\`

## Evidence

| Check | Result |
| --- | --- |
| jmon33 readmemh generated from \`roms/jmon33.bin\` | PASS |
| \`juku_top\` runs with frame IRQ period \`$FRAMEIRQ\` | PASS |
| first video write address | \`0x$first\` |
| first video write machine cycle | \`$mcyc\` |
| captured video writes | \`$writes\` |

## Remaining Boundary

- This is a first-video-write HDL probe, not a user-visible jmon33 prompt.
- The cosim-side interrupt path is deeper and remains documented in
  \`docs/jmon33-interrupt-probe.md\`.
- Next step: identify a stable monitor-ready screen/RAM oracle and compare the
  cosim and \`juku_top\` jmon33 states at that boundary.
EOF

echo "JMON33-HDL-PROBE: PASS"
echo "Wrote docs/jmon33-hdl-probe.md"
