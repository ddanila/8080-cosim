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
DISK=${JUKU_TOP_FDC_DISK:-media/disks/JUKU1.CPM}
KEYAT=${JUKU_TOP_FDC_KEYAT:-42000}
KHOLD=${JUKU_TOP_FDC_KHOLD:-900000}
KGAP=${JUKU_TOP_FDC_KGAP:-900000}
FRAMEIRQ=${JUKU_TOP_FDC_FRAMEIRQ:-80000}
MAXVRAM=${JUKU_TOP_FDC_MAXVRAM:-88000}
TIMECAP=${JUKU_TOP_FDC_TIMECAP:-900000000}
STOPFDC=${JUKU_TOP_FDC_STOPFDC:-1}
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
    +ekdoskeys=1 +keyat="$KEYAT" +khold="$KHOLD" +kgap="$KGAP" \
    +tracekbd=1 +traceppi=1 +stopppi="$STOPPPI" +tracefdc=1 +stopfdc="$STOPFDC" \
    +maxvram="$MAXVRAM" +timecap="$TIMECAP" >"$OUT" 2>&1
  rc=$?
else
  vvp "$SIM" \
    +disk="$DISK" +disk_heads=2 \
    +frameirq="$FRAMEIRQ" \
    +ekdoskeys=1 +keyat="$KEYAT" +khold="$KHOLD" +kgap="$KGAP" \
    +tracekbd=1 +traceppi=1 +stopppi="$STOPPPI" +tracefdc=1 +stopfdc="$STOPFDC" \
    +maxvram="$MAXVRAM" +timecap="$TIMECAP" >"$OUT" 2>&1
  rc=$?
fi
set -e

if [ -f "$OLD_VRAM" ]; then cp "$OLD_VRAM" hdl/sim/vram_top.bin; else rm -f hdl/sim/vram_top.bin; fi

fdc_stop=$(grep -m1 '^\[FDC\] stop' "$OUT" || true)
fdc_first=$(grep -m1 '^\[FDC\]' "$OUT" || true)
key_first=$(grep -m1 '^\[KBD\]' "$OUT" || true)
key_last=$(grep '^\[KBD\]' "$OUT" | tail -1 || true)
ppi_key_first=$(grep -m1 '^\[PPI0\] IN' "$OUT" || true)
ppi_stop=$(grep -m1 '^\[PPI0\] stop' "$OUT" || true)
io_summary=$(grep -m1 '^\[IO\]' "$OUT" || true)
first_vram=$(grep -m1 '^\[VRAM\] first video write' "$OUT" || true)
vram_stop=$(grep -m1 '^\[VRAM\] [0-9][0-9]* writes' "$OUT" || true)
timecap_line=$(grep -m1 '^\[SIM\] time cap' "$OUT" || true)
disk_line=$(grep -m1 '^FDC-1793: loaded raw disk' "$OUT" || true)
fdc_lines=$(grep -c '^\[FDC\]' "$OUT" || true)
kbd_lines=$(grep -c '^\[KBD\]' "$OUT" || true)
ppi_key_lines=$(grep -c '^\[PPI0\] IN' "$OUT" || true)

status="HDL JUKU_TOP FDC PATH NOT YET OBSERVED"
fdc_result="NO"
if [ -n "$fdc_stop" ]; then
  status="HDL JUKU_TOP FDC PATH OBSERVED"
  fdc_result="YES"
elif [ "$rc" -eq 124 ]; then
  status="HDL JUKU_TOP FDC PROBE TIMED OUT BEFORE FDC I/O"
fi

cat > "$REPORT" <<EOF
# juku_top FDC probe

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
- \`JUKU_TOP_FDC_STOPFDC\` default \`1\`
- \`JUKU_TOP_FDC_STOPPPI\` default \`0\`
- \`JUKU_TOP_FDC_TIMEOUT\` default \`60\` seconds

Current values: \`KEYAT=$KEYAT KHOLD=$KHOLD KGAP=$KGAP FRAMEIRQ=$FRAMEIRQ MAXVRAM=$MAXVRAM TIMECAP=$TIMECAP STOPFDC=$STOPFDC STOPPPI=$STOPPPI TIMEOUT=$TIMEOUT_S\`.

## Evidence

| Check | Result |
| --- | --- |
| vvp/timeout exit code | \`$rc\` |
| vendored raw disk loaded | $(if [ -n "$disk_line" ]; then echo PASS; else echo NO; fi) |
| first VRAM write observed | $(if [ -n "$first_vram" ]; then echo PASS; else echo NO; fi) |
| keyboard trace observed | $(if [ -n "$key_first" ]; then echo PASS; else echo NO; fi) |
| PPI key-read trace observed | $(if [ -n "$ppi_key_first" ]; then echo PASS; else echo NO; fi) |
| decoded FDC I/O observed | $fdc_result |
| keyboard trace lines | \`$kbd_lines\` |
| PPI key-read trace lines | \`$ppi_key_lines\` |
| FDC trace lines | \`$fdc_lines\` |

## Stop State

- Disk line: \`${disk_line:-none}\`
- First VRAM line: \`${first_vram:-none}\`
- VRAM stop line: \`${vram_stop:-none}\`
- First keyboard line: \`${key_first:-none}\`
- Last keyboard line: \`${key_last:-none}\`
- First PPI key-read line: \`${ppi_key_first:-none}\`
- PPI stop line: \`${ppi_stop:-none}\`
- First FDC line: \`${fdc_first:-none}\`
- FDC stop line: \`${fdc_stop:-none}\`
- Time-cap line: \`${timecap_line:-none}\`
- I/O summary line: \`${io_summary:-none}\`

## Disposition

- The top-level bench now has opt-in \`+ekdoskeys=1\`, \`+tracefdc=1\`, and
  \`+stopfdc=N\` hooks.
- Existing boot guards keep those hooks disabled, preserving the byte-identical
  ekta37 boot comparison.
- The remaining M2 target is still the full \`juku_top\` ROMBIOS \`TDD\` path to
  an EKDOS \`A>\` prompt.
EOF

echo "JUKU-TOP-FDC-PROBE: wrote $REPORT"
cat "$REPORT"

if [ "$rc" -ne 0 ] && [ "$rc" -ne 124 ]; then
  exit "$rc"
fi
