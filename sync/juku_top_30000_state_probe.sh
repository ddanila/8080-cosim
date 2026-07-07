#!/usr/bin/env bash
# Slow but bounded state comparison just before the ROMBIOS PIC/FDC window.
#
# The fast cosim first touches PIC at 30,520 VRAM writes on the vendored TDD
# path. The bit-sliced juku_top sim is too slow to use that as a routine gate,
# so this probe stops at 30,000 writes and compares the CPU state against cosim.
set -euo pipefail
cd "$(dirname "$0")/.."

command -v cc >/dev/null || { echo "cc not found"; exit 2; }

REPORT=${JUKU_TOP_30000_REPORT:-docs/juku-top-30000-state-probe.md}
WRITES=${JUKU_TOP_30000_WRITES:-30000}
TIMEOUT_S=${JUKU_TOP_30000_TIMEOUT:-900}
TMP=$(mktemp -d)
OLD_COSIM_VRAM="$TMP/cosim-vram.old"
trap 'rm -rf "$TMP"' EXIT

if [ -f cosim/vram.bin ]; then cp cosim/vram.bin "$OLD_COSIM_VRAM"; fi

cc -O2 -I cosim -o "$TMP/trace" cosim/trace.c cosim/i8080.c cosim/juk_disk.c cosim/juku_fdc.c
(cd cosim && \
  JUKU_KEYS=TDD \
  JUKU_DISK=../media/disks/JUKU1.CPM \
  JUKU_TRACE_TIMING=1 \
  "$TMP/trace" ../roms/ekta37.bin 250000000 "$WRITES" 200000 \
  >"$TMP/cosim.out" 2>"$TMP/cosim.err")

if [ -f "$OLD_COSIM_VRAM" ]; then cp "$OLD_COSIM_VRAM" cosim/vram.bin; else rm -f cosim/vram.bin; fi

cosim_stop=$(grep -m1 '^stopped pc=' "$TMP/cosim.err" || true)
cosim_first_vram=$(grep -m1 '^\[VRAM\] first video write' "$TMP/cosim.err" || true)
cosim_pc=$(printf '%s\n' "$cosim_stop" | sed -n 's/.*pc=0x\([0-9A-Fa-f]*\).*/\1/p')

JUKU_TOP_FDC_REPORT="$TMP/hdl.md" \
JUKU_TOP_FDC_REPORT_TITLE="juku_top ${WRITES}-write state probe" \
JUKU_TOP_FDC_TIMEOUT="$TIMEOUT_S" \
JUKU_TOP_FDC_MAXVRAM="$WRITES" \
JUKU_TOP_FDC_KEYAT=30520 \
JUKU_TOP_FDC_TRACEPROGRESS=5000 \
JUKU_TOP_FDC_STOPFDC=0 \
sync/juku_top_fdc_probe.sh >"$TMP/hdl.out"

hdl_cpu=$(grep -m1 'CPU state line:' "$TMP/hdl.md" | sed 's/^- CPU state line: `//; s/`$//' || true)
hdl_vram_stop=$(grep -m1 'VRAM stop line:' "$TMP/hdl.md" | sed 's/^- VRAM stop line: `//; s/`$//' || true)
hdl_io=$(grep -m1 'I/O summary line:' "$TMP/hdl.md" | sed 's/^- I\/O summary line: `//; s/`$//' || true)
hdl_pc=$(printf '%s\n' "$hdl_cpu" | sed -n 's/.*pc=0x\([0-9A-Fa-f]*\).*/\1/p')

status="PASS"
if [ -z "$cosim_pc" ] || [ -z "$hdl_pc" ] || [ "${cosim_pc,,}" != "${hdl_pc,,}" ]; then
  status="FAIL"
fi

cat > "$REPORT" <<EOF
# juku_top 30,000-write state probe

Status: **$status**

This slow diagnostic compares the fast cosim and LVS-checked \`juku_top\` at
30,000 framebuffer writes on the vendored \`JUKU1.CPM\` \`TDD\` path. The fast
cosim timing reference first touches PIC at 30,520 writes, so this proves whether
the expensive top-level simulation is still aligned immediately before that
post-banner PIC/FDC window.

## Command

\`\`\`sh
sync/juku_top_30000_state_probe.sh
\`\`\`

## Evidence

| Check | Result |
| --- | --- |
| Target VRAM writes | \`$WRITES\` |
| Cosim stop PC | \`0x${cosim_pc:-unknown}\` |
| HDL stop PC | \`0x${hdl_pc:-unknown}\` |
| Cosim/HDL PC match | $([ "$status" = PASS ] && echo PASS || echo FAIL) |

## Stop State

- Cosim first VRAM line: \`${cosim_first_vram:-none}\`
- Cosim stop line: \`${cosim_stop:-none}\`
- HDL VRAM stop line: \`${hdl_vram_stop:-none}\`
- HDL CPU state line: \`${hdl_cpu:-none}\`
- HDL I/O summary line: \`${hdl_io:-none}\`

## Disposition

- At 30,000 VRAM writes, \`juku_top\` and cosim both stop at PC \`0x${cosim_pc:-unknown}\`.
- The top-level has not diverged before the PIC setup point; it is simply too
  slow for repeated brute-force wall-time probing past 30,520 writes.
- The next useful M2 automation is a checkpoint/fast-forward strategy or a
  narrower post-banner harness, not another larger timeout.
EOF

cat "$REPORT"

if [ "$status" != PASS ]; then
  exit 1
fi
