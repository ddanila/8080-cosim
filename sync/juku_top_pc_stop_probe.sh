#!/usr/bin/env bash
# Fast guard for the juku_top_tb +stoppc=HEX diagnostic hook.
set -euo pipefail
cd "$(dirname "$0")/.."

REPORT=${JUKU_TOP_PC_STOP_REPORT:-docs/juku-top-pc-stop-probe.md}
TARGET=${JUKU_TOP_PC_STOP_TARGET:-01A8}
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

JUKU_TOP_FDC_REPORT="$TMP/pc-stop.md" \
JUKU_TOP_FDC_STOPPC="$TARGET" \
JUKU_TOP_FDC_STOPFDC=0 \
JUKU_TOP_FDC_TIMEOUT=60 \
sync/juku_top_fdc_probe.sh >/dev/null

pc_stop=$(grep -m1 'PC stop line:' "$TMP/pc-stop.md" | sed 's/^- PC stop line: `//; s/`$//' || true)
cpu_line=$(grep -m1 'CPU state line:' "$TMP/pc-stop.md" | sed 's/^- CPU state line: `//; s/`$//' || true)
status="PASS"
if ! printf '%s\n' "$pc_stop" | grep -qi "pc=0x$TARGET"; then
  status="FAIL"
fi

cat > "$REPORT" <<EOF
# juku_top PC-stop probe

Status: **$status**

This fast diagnostic proves the \`juku_top_tb\` \`+stoppc=HEX\` hook used by
\`sync/juku_top_fdc_probe.sh\`. It stops at an early ROMBIOS address before the
long framebuffer clear, so it can guard the instrumentation without paying the
full post-banner simulation cost.

## Command

\`\`\`sh
sync/juku_top_pc_stop_probe.sh
\`\`\`

## Evidence

| Check | Result |
| --- | --- |
| Target PC | \`0x$TARGET\` |
| PC stop line observed | $([ "$status" = PASS ] && echo PASS || echo FAIL) |

## Stop State

- PC stop line: \`${pc_stop:-none}\`
- CPU state line: \`${cpu_line:-none}\`

## Disposition

- Use \`JUKU_TOP_FDC_STOPPC=HEX\` plus optional \`JUKU_TOP_FDC_STOPPC_SKIP=N\`
  with \`sync/juku_top_fdc_probe.sh\` for ROMBIOS boundary stops.
- The hook is diagnostic only; default boot and LVS guards leave it disabled.
EOF

cat "$REPORT"

if [ "$status" != PASS ]; then
  exit 1
fi
