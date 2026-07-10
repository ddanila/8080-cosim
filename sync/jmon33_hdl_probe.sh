#!/usr/bin/env bash
# Prove that jmon33 runs far enough on the LVS-checked juku_top model to write
# video RAM with frame interrupts enabled.
set -euo pipefail
cd "$(dirname "$0")/.."
command -v iverilog >/dev/null || { echo "iverilog not found"; exit 2; }
CC=${CC:-cc}
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

echo "== cosim jmon33 first-write reference =="
$CC -O2 -I cosim -o "$TMP/trace" cosim/trace.c cosim/i8080.c cosim/juk_disk.c cosim/juku_fdc.c
( cd cosim && "$TMP/trace" ../roms/jmon33.bin 5000000 "$MAXVRAM" "$FRAMEIRQ" >"$TMP/cosim.out" 2>"$TMP/cosim.err" )
cat "$TMP/cosim.err"
cp cosim/vram.bin "$TMP/cosim-vram.bin"
cosim_first=$(sed -n 's/.*first video write @0x\([0-9a-fA-F]*\).*/\1/p' "$TMP/cosim.err" | head -1)
cosim_cyc=$(sed -n 's/.*first video write @0x[0-9a-fA-F]* cyc=\([0-9][0-9]*\).*/\1/p' "$TMP/cosim.err" | head -1)

echo "== juku_top jmon33 HDL probe =="
iverilog -g2012 -o "$TMP/juku_top_jmon33" hdl/vendor/vm80a.v hdl/devices.v hdl/juku_top.v hdl/sim/juku_top_tb.v
out=$(vvp "$TMP/juku_top_jmon33" +rom=hdl/sim/jmon33.hex +frameirq="$FRAMEIRQ" +maxvram="$MAXVRAM" +timecap="$TIMECAP")
echo "$out"

first=$(printf '%s\n' "$out" | sed -n 's/.*first video write @0x\([0-9a-fA-F]*\).*/\1/p' | head -1)
writes=$(printf '%s\n' "$out" | sed -n 's/.*\[VRAM\] \([0-9][0-9]*\) writes.*/\1/p' | head -1)
mcyc=$(printf '%s\n' "$out" | sed -n 's/.*first video write @0x[0-9a-fA-F]* mcyc=\([0-9][0-9]*\).*/\1/p' | head -1)

if [ "${first,,}" != "ff40" ] || [ "${cosim_first,,}" != "ff40" ] || [ "$writes" != "$MAXVRAM" ]; then
  echo "JMON33-HDL-PROBE: FAIL"
  exit 1
fi

if ! cmp -s "$TMP/cosim-vram.bin" hdl/sim/vram_top.bin; then
  echo "JMON33-HDL-PROBE: FAIL (first-write VRAM dump differs from cosim)"
  exit 1
fi

cat > docs/jmon33-hdl-probe.md <<EOF
# jmon33 HDL probe

Status: **JMON33 FIRST-WRITE MATCHES COSIM AND JUKU_TOP**

This probe runs the Monitor 3.3 ROM on the LVS-checked structural model
\`juku_top\` with frame interrupts enabled. It proves that the HDL twin reaches
jmon33's first video-memory write and matches the cosim first-write boundary.

## Command

\`\`\`sh
sync/jmon33_hdl_probe.sh
\`\`\`

Environment overrides:

- \`JMON33_HDL_MAXVRAM\` default \`$MAXVRAM\`
- \`JMON33_HDL_FRAMEIRQ\` default \`$FRAMEIRQ\`
- \`JMON33_HDL_TIMECAP\` default \`$TIMECAP\`

The underlying HDL testbench also accepts \`+cursorstop=1\`, which stops when
the cosim jmon33 monitor-idle cursor bytes are present in \`juku_top\` VRAM.
That stronger boundary is intentionally not the default for this fast guard.

## Evidence

| Check | Result |
| --- | --- |
| jmon33 readmemh generated from \`roms/jmon33.bin\` | PASS |
| cosim first video write address | \`0x$cosim_first\` |
| cosim first video write cycle | \`$cosim_cyc\` |
| \`juku_top\` runs with frame IRQ period \`$FRAMEIRQ\` | PASS |
| \`juku_top\` first video write address | \`0x$first\` |
| \`juku_top\` first video write machine cycle | \`$mcyc\` |
| captured video writes | \`$writes\` |
| first-write VRAM dump equals cosim | PASS |

## Scope

- This remains the fast first-video-write HDL guard; it is not the stronger
  user-visible completion check by itself.
- The cosim-side interrupt path is documented in
  \`docs/jmon33-interrupt-probe.md\`.
- \`docs/jmon33-ready-probe.md\` defines the cosim monitor-idle framebuffer
  oracle, and \`docs/jmon33-hdl-cursor-probe.md\` records that \`juku_top\`
  reaches the matching cursor/hash boundary.
EOF

echo "JMON33-HDL-PROBE: PASS"
echo "Wrote docs/jmon33-hdl-probe.md"
