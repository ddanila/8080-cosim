#!/usr/bin/env bash
# Fast top-level decoded peripheral bus guard for the PIC/PPI/FDC M2 boundary.
set -euo pipefail
cd "$(dirname "$0")/.."

command -v iverilog >/dev/null || { echo "iverilog not found"; exit 2; }
command -v vvp >/dev/null || { echo "vvp not found"; exit 2; }

REPORT=${JUKU_TOP_PERIPH_BUS_REPORT:-docs/juku-top-periph-bus-check.md}
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

SIM="$TMP/juku_top_periph_bus_tb"
OUT="$TMP/out.txt"

iverilog -g2012 -o "$SIM" hdl/vendor/vm80a.v hdl/devices.v hdl/juku_top.v hdl/sim/juku_top_periph_bus_tb.v
vvp "$SIM" +disk=media/disks/JUKU1.CPM +disk_heads=2 >"$OUT"

status="PASS"
if ! grep -q '^JUKU-TOP-PERIPH-BUS: PASS' "$OUT"; then
  status="FAIL"
fi
disk_line=$(grep -m1 '^FDC-1793: loaded raw disk' "$OUT" || true)
pass_line=$(grep -m1 '^JUKU-TOP-PERIPH-BUS: PASS' "$OUT" || true)

cat > "$REPORT" <<EOF
# juku_top peripheral bus check

Status: **$status**

This fast harness drives the LVS-checked \`juku_top\` buffered CPU bus directly
through \`BA\`, \`DB\`, \`iord_n\`, \`iowr_n\`, and \`inta_n\`, while leaving the
real top-level chip-select decode and peripheral instances in place. It proves
the post-banner keyboard/PIC/PPI/FDC path without waiting for ROMBIOS to redraw
the screen.

## Command

\`\`\`sh
sync/juku_top_periph_bus_check.sh
\`\`\`

## Evidence

| Check | Result |
| --- | --- |
| Vendored \`JUKU1.CPM\` loaded by top-level FDC | $(if [ -n "$disk_line" ]; then echo PASS; else echo FAIL; fi) |
| PIC register write/read through decoded ports \`0x00/0x01\` | $status |
| Frame tick raises \`INTR\` and INTA returns \`CD D4 FE\` for vector \`0xFED4\` | $status |
| PPI0 no-key scan reads \`0xCF\` like the first ROMBIOS keyboard poll | $status |
| PPI0 keyboard scan reads shifted \`T\` as \`0x88\` through decoded ports \`0x04/0x05\` | $status |
| PPI0 Port C motor-on latch through decoded port \`0x06\` | $status |
| FDC accepts exact ROMBIOS first command \`0x02\` as restore and returns track 0 | $status |
| FDC seek/status/data through decoded ports \`0x1C..0x1F\` | $status |
| First byte of \`JUKU1.CPM\` track 0 sector 2 read through top-level bus is \`0xC3\` | $status |

## Stop State

- Disk line: \`${disk_line:-none}\`
- Pass line: \`${pass_line:-none}\`

## Boundary

- This is a direct-bus harness, not proof that the full ROMBIOS \`TDD\` CPU path
  has reached decoded FDC I/O.
- It narrows the remaining M2 blocker: the top-level peripheral decode mirrors
  the pinned EKDOS no-key read, shifted-\`T\` read, PIC vector, motor latch, and
  first FDC restore command when reached. The harness then extends the same path
  to a media-backed sector read. The open problem is still getting the full CPU
  run through the slow post-banner path efficiently.
EOF

cat "$REPORT"

if [ "$status" != PASS ]; then
  cat "$OUT"
  exit 1
fi
