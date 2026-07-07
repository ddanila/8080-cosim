#!/usr/bin/env bash
# Bounded diagnostic for the full juku_top ROMBIOS -> FDC boundary.
#
# This is intentionally not a CI gate yet: the full EKDOS prompt path is still
# slow in the bit-sliced top-level sim. The probe makes the current state
# reproducible and stops as soon as decoded WD1793 I/O is observed.
set -euo pipefail
cd "$(dirname "$0")/.."

command -v iverilog >/dev/null || { echo "iverilog not found"; exit 2; }
command -v vvp >/dev/null || { echo "vvp not found"; exit 2; }

REPORT=${JUKU_TOP_FDC_REPORT:-docs/juku-top-fdc-probe.md}
REPORT_TITLE=${JUKU_TOP_FDC_REPORT_TITLE:-juku_top FDC probe}
DISK=${JUKU_TOP_FDC_DISK:-media/disks/JUKU1.CPM}
KEYAT=${JUKU_TOP_FDC_KEYAT:-42000}
KHOLD=${JUKU_TOP_FDC_KHOLD:-900000}
KGAP=${JUKU_TOP_FDC_KGAP:-900000}
FRAMEIRQ=${JUKU_TOP_FDC_FRAMEIRQ:-80000}
MAXVRAM=${JUKU_TOP_FDC_MAXVRAM:-88000}
TIMECAP=${JUKU_TOP_FDC_TIMECAP:-900000000}
TRACEPROGRESS=${JUKU_TOP_FDC_TRACEPROGRESS:-5000}
TRACEIO=${JUKU_TOP_FDC_TRACEIO:-0}
STOPIO=${JUKU_TOP_FDC_STOPIO:-0}
STOPFDC=${JUKU_TOP_FDC_STOPFDC:-1}
STOPPIC=${JUKU_TOP_FDC_STOPPIC:-0}
STOPPPI=${JUKU_TOP_FDC_STOPPPI:-0}
TIMEOUT_S=${JUKU_TOP_FDC_TIMEOUT:-60}

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

SIM="$TMP/juku_top_tb"
OUT="$TMP/out.txt"
OLD_VRAM="$TMP/vram_top.old"
if [ -f hdl/sim/vram_top.bin ]; then cp hdl/sim/vram_top.bin "$OLD_VRAM"; fi

iverilog -g2012 -o "$SIM" hdl/vendor/vm80a.v hdl/devices.v hdl/juku_top.v hdl/sim/juku_top_tb.v

set +e
if command -v timeout >/dev/null; then
  timeout "$TIMEOUT_S" vvp "$SIM" \
    +disk="$DISK" +disk_heads=2 \
    +frameirq="$FRAMEIRQ" \
    +traceprogress="$TRACEPROGRESS" \
    +ekdoskeys=1 +keyat="$KEYAT" +khold="$KHOLD" +kgap="$KGAP" \
    +traceio="$TRACEIO" +stopio="$STOPIO" +tracekbd=1 +tracepic=1 +stoppic="$STOPPIC" +traceppi=1 +traceirq=1 +stopppi="$STOPPPI" +tracefdc=1 +stopfdc="$STOPFDC" \
    +maxvram="$MAXVRAM" +timecap="$TIMECAP" >"$OUT" 2>&1
  rc=$?
else
  vvp "$SIM" \
    +disk="$DISK" +disk_heads=2 \
    +frameirq="$FRAMEIRQ" \
    +traceprogress="$TRACEPROGRESS" \
    +ekdoskeys=1 +keyat="$KEYAT" +khold="$KHOLD" +kgap="$KGAP" \
    +traceio="$TRACEIO" +stopio="$STOPIO" +tracekbd=1 +tracepic=1 +stoppic="$STOPPIC" +traceppi=1 +traceirq=1 +stopppi="$STOPPPI" +tracefdc=1 +stopfdc="$STOPFDC" \
    +maxvram="$MAXVRAM" +timecap="$TIMECAP" >"$OUT" 2>&1
  rc=$?
fi
set -e

if [ -f "$OLD_VRAM" ]; then cp "$OLD_VRAM" hdl/sim/vram_top.bin; else rm -f hdl/sim/vram_top.bin; fi

fdc_stop=$(grep -m1 '^\[FDC\] stop' "$OUT" || true)
fdc_first=$(grep -m1 '^\[FDC\]' "$OUT" || true)
key_first=$(grep -m1 '^\[KBD\]' "$OUT" || true)
key_last=$(grep '^\[KBD\]' "$OUT" | tail -1 || true)
pic_first=$(grep -m1 '^\[PIC\]' "$OUT" || true)
pic_stop=$(grep -m1 '^\[PIC\] stop' "$OUT" || true)
ppi_key_first=$(grep -m1 '^\[PPI0\] IN' "$OUT" || true)
ppi_stop=$(grep -m1 '^\[PPI0\] stop' "$OUT" || true)
irq_first=$(grep -m1 '^\[IRQ\]' "$OUT" || true)
rawio_first=$(grep -m1 '^\[RAWIO\]' "$OUT" || true)
rawio_stop=$(grep -m1 '^\[RAWIO\] stop' "$OUT" || true)
io_summary=$(grep -m1 '^\[IO\]' "$OUT" || true)
first_vram=$(grep -m1 '^\[VRAM\] first video write' "$OUT" || true)
last_progress=$(grep '^\[VRAM\] progress' "$OUT" | tail -1 || true)
vram_stop=$(grep -m1 '^\[VRAM\] [0-9][0-9]* writes' "$OUT" || true)
timecap_line=$(grep -m1 '^\[SIM\] time cap' "$OUT" || true)
cpu_line=$(grep -m1 '^\[CPU\]' "$OUT" || true)
disk_line=$(grep -m1 '^FDC-1793: loaded raw disk' "$OUT" || true)
fdc_lines=$(grep -c '^\[FDC\]' "$OUT" || true)
kbd_lines=$(grep -c '^\[KBD\]' "$OUT" || true)
progress_lines=$(grep -c '^\[VRAM\] progress' "$OUT" || true)
pic_lines=$(grep -c '^\[PIC\]' "$OUT" || true)
ppi_key_lines=$(grep -c '^\[PPI0\] IN' "$OUT" || true)
irq_lines=$(grep -c '^\[IRQ\]' "$OUT" || true)
rawio_lines=$(grep -c '^\[RAWIO\]' "$OUT" || true)

status="HDL JUKU_TOP FDC PATH NOT YET OBSERVED"
fdc_result="NO"
if [ -n "$fdc_stop" ]; then
  status="HDL JUKU_TOP FDC PATH OBSERVED"
  fdc_result="YES"
elif [ "$rc" -eq 124 ]; then
  status="HDL JUKU_TOP FDC PROBE TIMED OUT BEFORE FDC I/O"
fi

cat > "$REPORT" <<EOF
# $REPORT_TITLE

Status: **$status**

This bounded diagnostic runs the LVS-checked \`juku_top\` with the vendored
Juku disk image, frame interrupts, and the fixed ROMBIOS \`TDD\` keyboard
sequence enabled. The testbench stops on decoded WD1793/VG93 I/O so the
remaining EKDOS prompt path can be chased without relying on a manual long
framebuffer run.

## Command

\`\`\`sh
sync/juku_top_fdc_probe.sh
\`\`\`

Environment overrides:

- \`JUKU_TOP_FDC_DISK\` default \`media/disks/JUKU1.CPM\`
- \`JUKU_TOP_FDC_KEYAT\` default \`42000\`
- \`JUKU_TOP_FDC_KHOLD\` default \`900000\`
- \`JUKU_TOP_FDC_KGAP\` default \`900000\`
- \`JUKU_TOP_FDC_FRAMEIRQ\` default \`80000\`
- \`JUKU_TOP_FDC_TRACEPROGRESS\` default \`5000\`
- \`JUKU_TOP_FDC_TRACEIO\` default \`0\`
- \`JUKU_TOP_FDC_STOPIO\` default \`0\`
- \`JUKU_TOP_FDC_STOPFDC\` default \`1\`
- \`JUKU_TOP_FDC_STOPPIC\` default \`0\`
- \`JUKU_TOP_FDC_STOPPPI\` default \`0\`
- \`JUKU_TOP_FDC_TIMEOUT\` default \`60\` seconds

Current values: \`KEYAT=$KEYAT KHOLD=$KHOLD KGAP=$KGAP FRAMEIRQ=$FRAMEIRQ TRACEPROGRESS=$TRACEPROGRESS TRACEIO=$TRACEIO STOPIO=$STOPIO MAXVRAM=$MAXVRAM TIMECAP=$TIMECAP STOPFDC=$STOPFDC STOPPIC=$STOPPIC STOPPPI=$STOPPPI TIMEOUT=$TIMEOUT_S\`.

## Evidence

| Check | Result |
| --- | --- |
| vvp/timeout exit code | \`$rc\` |
| vendored raw disk loaded | $(if [ -n "$disk_line" ]; then echo PASS; else echo NO; fi) |
| first VRAM write observed | $(if [ -n "$first_vram" ]; then echo PASS; else echo NO; fi) |
| VRAM progress trace observed | $(if [ -n "$last_progress" ]; then echo PASS; else echo NO; fi) |
| keyboard trace observed | $(if [ -n "$key_first" ]; then echo PASS; else echo NO; fi) |
| raw I/O trace observed | $(if [ -n "$rawio_first" ]; then echo PASS; else echo NO; fi) |
| PIC setup trace observed | $(if [ -n "$pic_first" ]; then echo PASS; else echo NO; fi) |
| PPI key-read trace observed | $(if [ -n "$ppi_key_first" ]; then echo PASS; else echo NO; fi) |
| IRQ trace observed | $(if [ -n "$irq_first" ]; then echo PASS; else echo NO; fi) |
| decoded FDC I/O observed | $fdc_result |
| keyboard trace lines | \`$kbd_lines\` |
| VRAM progress trace lines | \`$progress_lines\` |
| PIC trace lines | \`$pic_lines\` |
| PPI key-read trace lines | \`$ppi_key_lines\` |
| IRQ trace lines | \`$irq_lines\` |
| raw I/O trace lines | \`$rawio_lines\` |
| FDC trace lines | \`$fdc_lines\` |

## Stop State

- Disk line: \`${disk_line:-none}\`
- First VRAM line: \`${first_vram:-none}\`
- Last VRAM progress line: \`${last_progress:-none}\`
- VRAM stop line: \`${vram_stop:-none}\`
- First keyboard line: \`${key_first:-none}\`
- Last keyboard line: \`${key_last:-none}\`
- First PIC line: \`${pic_first:-none}\`
- PIC stop line: \`${pic_stop:-none}\`
- First PPI key-read line: \`${ppi_key_first:-none}\`
- PPI stop line: \`${ppi_stop:-none}\`
- First IRQ line: \`${irq_first:-none}\`
- First raw I/O line: \`${rawio_first:-none}\`
- Raw I/O stop line: \`${rawio_stop:-none}\`
- First FDC line: \`${fdc_first:-none}\`
- FDC stop line: \`${fdc_stop:-none}\`
- Time-cap line: \`${timecap_line:-none}\`
- CPU state line: \`${cpu_line:-none}\`
- I/O summary line: \`${io_summary:-none}\`

## Disposition

- The top-level bench now has opt-in \`+ekdoskeys=1\`, \`+traceio=1\`,
  \`+stopio=N\`, \`+tracepic=1\`, \`+stoppic=N\`, \`+tracefdc=1\`, and
  \`+stopfdc=N\` hooks.
- Existing boot guards keep those hooks disabled, preserving the byte-identical
  ekta37 boot comparison.
- \`docs/ekdos-timing-reference.md\` shows the fast cosim target for this same
  vendored \`TDD\` path: first PIC/PPI setup around 30,520 VRAM writes, first
  frame IRQ at 33,812 VRAM writes, and first FDC command at 63,085 VRAM writes.
- The remaining M2 target is still the full \`juku_top\` ROMBIOS \`TDD\` path to
  an EKDOS \`A>\` prompt.
EOF

echo "JUKU-TOP-FDC-PROBE: wrote $REPORT"
cat "$REPORT"

if [ "$rc" -ne 0 ] && [ "$rc" -ne 124 ]; then
  exit "$rc"
fi
