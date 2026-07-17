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
QUAL_SIM="$TMP/juku_top_periph_bus_qualified_tb"
ALWAYS_SIM="$TMP/juku_top_periph_bus_always_tb"
OUT="$TMP/out.txt"
WRITABLE_OUT="$TMP/writable-out.txt"
QUAL_OUT="$TMP/qualified-out.txt"
QUAL_WRITABLE_OUT="$TMP/qualified-writable-out.txt"
ALWAYS_OUT="$TMP/always-out.txt"
ALWAYS_WRITABLE_OUT="$TMP/always-writable-out.txt"

iverilog -g2012 -DFDC_BYTE_TIMING -DFDC_TYPE_I_TIMING -o "$SIM" hdl/vendor/vm80a.v hdl/devices.v hdl/juku_top.v hdl/sim/juku_top_periph_bus_tb.v
iverilog -g2012 -DFDC_BYTE_TIMING -DFDC_TYPE_I_TIMING -DFDC_VA87_CS_QUALIFIED -o "$QUAL_SIM" \
  hdl/vendor/vm80a.v hdl/devices.v hdl/juku_top.v hdl/sim/juku_top_periph_bus_tb.v
iverilog -g2012 -DFDC_BYTE_TIMING -DFDC_TYPE_I_TIMING -DFDC_VA87_ALWAYS_ENABLED -o "$ALWAYS_SIM" \
  hdl/vendor/vm80a.v hdl/devices.v hdl/juku_top.v hdl/sim/juku_top_periph_bus_tb.v
vvp "$SIM" +disk=media/disks/JUKU1.CPM +disk_heads=2 >"$OUT"
cp media/disks/JUKU1.CPM "$TMP/JUKU1-writable.CPM"
vvp "$SIM" +disk="$TMP/JUKU1-writable.CPM" +disk_heads=2 +disk_writable \
  +expect_writable >"$WRITABLE_OUT"
vvp "$QUAL_SIM" +disk=media/disks/JUKU1.CPM +disk_heads=2 +fdc_bus_invert >"$QUAL_OUT"
cp media/disks/JUKU1.CPM "$TMP/JUKU1-qualified-writable.CPM"
vvp "$QUAL_SIM" +disk="$TMP/JUKU1-qualified-writable.CPM" +disk_heads=2 \
  +disk_writable +expect_writable +fdc_bus_invert >"$QUAL_WRITABLE_OUT"
vvp "$ALWAYS_SIM" +disk=media/disks/JUKU1.CPM +disk_heads=2 +fdc_bus_invert >"$ALWAYS_OUT"
cp media/disks/JUKU1.CPM "$TMP/JUKU1-always-writable.CPM"
vvp "$ALWAYS_SIM" +disk="$TMP/JUKU1-always-writable.CPM" +disk_heads=2 \
  +disk_writable +expect_writable +fdc_bus_invert >"$ALWAYS_WRITABLE_OUT"

status="PASS"
if ! grep -q '^JUKU-TOP-PERIPH-BUS: PASS' "$OUT"; then
  status="FAIL"
fi
if ! grep -q '^JUKU-TOP-PERIPH-BUS: PASS' "$WRITABLE_OUT"; then
  status="FAIL"
fi
for physical_out in "$QUAL_OUT" "$QUAL_WRITABLE_OUT" "$ALWAYS_OUT" "$ALWAYS_WRITABLE_OUT"; do
  if ! grep -q '^JUKU-TOP-PERIPH-BUS: PASS' "$physical_out"; then
    status="FAIL"
  fi
done
disk_line=$(grep -m1 '^FDC-1793: loaded raw disk' "$OUT" || true)
pass_line=$(grep -m1 '^JUKU-TOP-PERIPH-BUS: PASS' "$OUT" || true)
writable_line=$(grep -m1 '^FDC-1793: loaded raw disk' "$WRITABLE_OUT" || true)
writable_pass_line=$(grep -m1 '^JUKU-TOP-PERIPH-BUS: PASS' "$WRITABLE_OUT" || true)
qualified_pass_line=$(grep -m1 '^JUKU-TOP-PERIPH-BUS: PASS' "$QUAL_WRITABLE_OUT" || true)
always_pass_line=$(grep -m1 '^JUKU-TOP-PERIPH-BUS: PASS' "$ALWAYS_WRITABLE_OUT" || true)
if [ -n "$writable_line" ]; then
  writable_line="FDC-1793: loaded raw disk <temporary-copy> (2 sides, writable)"
fi

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
| Physical D94 table produces mutually exclusive FDC \`/RE\` and \`/WE\` strobes | $status |
| Low D101.Q0/A4 steers register 3 from D93 strobes to the pulled-up D94 D0 branch | $status |
| Chip-select-qualified D100 path uses actual D93 \`/RE\` and stays A->B on the suppressed-\`/RE\` branch | $(if [ -n "$qualified_pass_line" ]; then echo PASS; else echo FAIL; fi) |
| Always-enabled D100 path uses actual D93 \`/RE\` and stays A->B on the suppressed-\`/RE\` branch | $(if [ -n "$always_pass_line" ]; then echo PASS; else echo FAIL; fi) |
| FDC accepts exact ROMBIOS first command \`0x02\` as restore and returns track 0 | $status |
| FDC completion/status acknowledgement plus D0, persistent D8, READY-transition, and repeated-index Force Interrupt lifecycle | $status |
| Timed Type-I physical-head/update/verify/SEEK-ERROR completion plus exact 15-idle-index HLD release through decoded ports \`0x1C..0x1F\` | $status |
| One missed read-byte deadline sets LOST DATA and exposes sector 2 byte 1 (\`0x5C\`) through the top-level bus | $status |
| Type-III Read Track reconstructs and drains one 6,250-byte MFM revolution with all ten sector IDs through logical DB and both physical D100 families | $status |
| Type-II multi-read traverses vendored sectors 9/10 and ends at sector 11 with RNF | $status |
| ROMBIOS \`0xA2\` write-sector streams 512 bytes through D94-decoded port \`0x1F\` and reads them back from a writable copy | $status |
| Type-II multi-write persists sectors 9/10 and ends at sector 11 with RNF | $status |
| Type-III Write Track streams 6,230 formatter bytes and persists sectors 1-10 on a writable copy through logical DB and both physical D100 families | $status |
| CMA-profile CPU bytes cross physical D100/DAL for restore, seek, media read, and 512-byte write/readback under both control families | $status |

## Stop State

- Disk line: \`${disk_line:-none}\`
- Pass line: \`${pass_line:-none}\`
- Writable-copy disk line: \`${writable_line:-none}\`
- Writable-copy pass line: \`${writable_pass_line:-none}\`
- Qualified-D100 writable pass line: \`${qualified_pass_line:-none}\`
- Always-enabled-D100 writable pass line: \`${always_pass_line:-none}\`

## Boundary

- This is a direct-bus harness, not the full ROMBIOS \`TDD\` CPU path.
- The behavioral FDC consumes D94's physical-table strobes. D94 enable,
  A3=active-low \`IOWR\`, and pulled-high A4 are explicit simulation-only
  functional sources; they preserve, rather than close, the physical probes.
- A separate forced-low A4 check exercises the alternate register-3 D0 branch
  without assigning that physically pulled-up output an unmeasured load.
- Two opt-in builds route the behavioral controller through physical D100/DAL.
  Their CPU-side FDC bytes are complemented like CMA-profile firmware. Both use
  actual D93 \`/RE\` for direction, not raw \`IORD\`; this keeps D100 A->B when
  D94's low-A4 branch suppresses the controller read strobe. One build qualifies
  \`/OE\` with FDC chip-select and the other grounds it like D23-D25. These are
  executable functional candidates, not measured copper assignments.
- It remains a fast lower-level guard: the top-level peripheral decode mirrors
  the pinned EKDOS no-key read, shifted-\`T\` read, PIC vector, motor latch, and
  first FDC restore command when reached. The harness then extends the same path
  to media-backed single/multiple-record and reconstructed whole-track reads,
  plus opt-in temporary-copy single/multiple-record writes and whole-track
  format/readback.
EOF

cat "$REPORT"

if [ "$status" != PASS ]; then
  cat "$OUT"
  cat "$WRITABLE_OUT"
  cat "$QUAL_OUT"
  cat "$QUAL_WRITABLE_OUT"
  cat "$ALWAYS_OUT"
  cat "$ALWAYS_WRITABLE_OUT"
  exit 1
fi
