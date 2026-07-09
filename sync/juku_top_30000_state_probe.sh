#!/usr/bin/env bash
# Slow but bounded state comparison near the ROMBIOS PIC/FDC window.
#
# The fast cosim first touches PIC at 30,520 VRAM writes on the vendored TDD
# path. The bit-sliced juku_top sim is too slow to use that as a routine gate,
# so this probe stops at 30,000 writes and compares the CPU state against cosim.
set -euo pipefail
cd "$(dirname "$0")/.."

command -v cc >/dev/null || { echo "cc not found"; exit 2; }

REPORT=${JUKU_TOP_30000_REPORT:-docs/juku-top-30000-state-probe.md}
WRITES=${JUKU_TOP_30000_WRITES:-30000}
DISPLAY_WRITES=$WRITES
if [ "$WRITES" = "30000" ]; then DISPLAY_WRITES="30,000"; fi
if [ "$WRITES" = "30520" ]; then DISPLAY_WRITES="30,520"; fi
TIMEOUT_S=${JUKU_TOP_30000_TIMEOUT:-900}
SIMULATOR=${JUKU_TOP_30000_SIM:-icarus}
COSIM_FRAME_CYCLES=${JUKU_TOP_30000_COSIM_FRAME_CYCLES:-200000}
HDL_FRAMEIRQ=${JUKU_TOP_30000_HDL_FRAMEIRQ:-80000}
HDL_FRAMEPHASE=${JUKU_TOP_30000_HDL_FRAMEPHASE:-0}
HDL_FRAMEMCYC=${JUKU_TOP_30000_HDL_FRAMEMCYC:-0}
KEYAT=${JUKU_TOP_30000_KEYAT:-42000}
TMP=$(mktemp -d)
OLD_COSIM_VRAM="$TMP/cosim-vram.old"
COSIM_VRAM="$TMP/cosim-vram.bin"
HDL_VRAM="$TMP/hdl-vram.bin"
CHECKPOINT_PREFIX="$TMP/cosim-checkpoint"
trap 'rm -rf "$TMP"' EXIT

if [ -f cosim/vram.bin ]; then cp cosim/vram.bin "$OLD_COSIM_VRAM"; fi

cc -O2 -I cosim -o "$TMP/trace" cosim/trace.c cosim/i8080.c cosim/juk_disk.c cosim/juku_fdc.c
(cd cosim && \
  JUKU_KEYS=TDD \
  JUKU_DISK=../media/disks/JUKU1.CPM \
  JUKU_KEY_START_VRAM="$KEYAT" \
  JUKU_TRACE_TIMING=1 \
  JUKU_CHECKPOINT_PREFIX="$CHECKPOINT_PREFIX" \
  "$TMP/trace" ../roms/ekta37.bin 250000000 "$WRITES" "$COSIM_FRAME_CYCLES" \
  >"$TMP/cosim.out" 2>"$TMP/cosim.err")

if [ -f cosim/vram.bin ]; then cp cosim/vram.bin "$COSIM_VRAM"; fi
if [ -f "$OLD_COSIM_VRAM" ]; then cp "$OLD_COSIM_VRAM" cosim/vram.bin; else rm -f cosim/vram.bin; fi

cosim_stop=$(grep -m1 '^stopped pc=' "$TMP/cosim.err" || true)
cosim_first_vram=$(grep -m1 '^\[VRAM\] first video write' "$TMP/cosim.err" || true)
cosim_pc=$(printf '%s\n' "$cosim_stop" | sed -n 's/.*pc=0x\([0-9A-Fa-f]*\).*/\1/p')
cosim_state="$CHECKPOINT_PREFIX.state"
cosim_vram_sha="missing"
hdl_vram_sha="missing"
vram_bytes="unknown"
vram_match="NO"
if [ -f "$COSIM_VRAM" ]; then
  cosim_vram_sha=$(sha256sum "$COSIM_VRAM" | awk '{print $1}')
  vram_bytes=$(wc -c < "$COSIM_VRAM" | tr -d ' ')
fi

JUKU_TOP_FDC_REPORT="$TMP/hdl.md" \
JUKU_TOP_FDC_REPORT_TITLE="juku_top ${DISPLAY_WRITES}-write state probe" \
JUKU_TOP_FDC_SIM="$SIMULATOR" \
JUKU_TOP_FDC_VRAM_COPY="$HDL_VRAM" \
JUKU_TOP_FDC_TIMEOUT="$TIMEOUT_S" \
JUKU_TOP_FDC_MAXVRAM="$WRITES" \
JUKU_TOP_FDC_VRAMSTOP_SYNC=1 \
JUKU_TOP_FDC_FRAMEIRQ="$HDL_FRAMEIRQ" \
JUKU_TOP_FDC_FRAMEPHASE="$HDL_FRAMEPHASE" \
JUKU_TOP_FDC_FRAMEMCYC="$HDL_FRAMEMCYC" \
JUKU_TOP_FDC_KEYAT="$KEYAT" \
JUKU_TOP_FDC_TRACEPROGRESS=5000 \
JUKU_TOP_FDC_STOPFDC=0 \
sync/juku_top_fdc_probe.sh >"$TMP/hdl.out"

hdl_rc=$(grep -m1 'vvp/timeout exit code' "$TMP/hdl.md" | sed -n 's/.*| `\([0-9][0-9]*\)` |.*/\1/p')
hdl_cpu=$(grep -m1 'CPU state line:' "$TMP/hdl.md" | sed 's/^- CPU state line: `//; s/`$//' || true)
hdl_state=$(grep -m1 'Visible state line:' "$TMP/hdl.md" | sed 's/^- Visible state line: `//; s/`$//' || true)
hdl_vram_stop=$(grep -m1 'VRAM stop line:' "$TMP/hdl.md" | sed 's/^- VRAM stop line: `//; s/`$//' || true)
hdl_io=$(grep -m1 'I/O summary line:' "$TMP/hdl.md" | sed 's/^- I\/O summary line: `//; s/`$//' || true)
hdl_pc=$(printf '%s\n' "$hdl_cpu" | sed -n 's/.*pc=0x\([0-9A-Fa-f]*\).*/\1/p')
hdl_ba=$(printf '%s\n' "$hdl_cpu" | sed -n 's/.*ba=0x\([0-9A-Fa-f]*\).*/\1/p')
hdl_memr_n=$(printf '%s\n' "$hdl_cpu" | sed -n 's/.*memr_n=\([0-9]\).*/\1/p')
hdl_effective_pc=$hdl_pc
if [ "$hdl_memr_n" = "0" ] && [ -n "$hdl_ba" ]; then
  hdl_effective_pc=$hdl_ba
fi
hdl_reached_dump=NO
if [ -n "$hdl_cpu" ] && [ "$hdl_vram_stop" != "none" ]; then
  hdl_reached_dump=PASS
fi
if [ "$hdl_reached_dump" = PASS ] && [ -f "$HDL_VRAM" ]; then
  hdl_vram_sha=$(sha256sum "$HDL_VRAM" | awk '{print $1}')
fi
if [ "$hdl_reached_dump" = PASS ] && [ -f "$COSIM_VRAM" ] && [ -f "$HDL_VRAM" ] && cmp -s "$COSIM_VRAM" "$HDL_VRAM"; then
  vram_match="PASS"
fi

state_value() {
  local file=$1 key=$2
  awk -F= -v k="$key" '$1 == k { print $2; exit }' "$file"
}

line_value() {
  local line=$1 key=$2
  printf '%s\n' "$line" | tr ' ' '\n' | sed -n "s/^${key}=//p" | head -1
}

normalize_hex() {
  tr '[:lower:]' '[:upper:]'
}

state_failures=()
state_keys=(
  sp a b c d e h l sf zf hf pf cf iff mode portc kbd_col
  pic_icw1 pic_icw2 pic_mask pic_expect_icw2
  fdc_motor_on fdc_track fdc_sector fdc_data fdc_command
  fdc_buffer_pos fdc_buffer_len
)
hex_keys=" pc sp a b c d e h l portc kbd_col pic_icw1 pic_icw2 pic_mask fdc_track fdc_sector fdc_data fdc_command "
state_match="PASS"
if [ "$hdl_reached_dump" != PASS ]; then
  state_match="NO"
  state_failures+=("HDL did not reach the $DISPLAY_WRITES-write dump point within timeout")
elif [ ! -f "$cosim_state" ]; then
  state_match="FAIL"
  state_failures+=("missing cosim checkpoint state file")
elif [ -z "$hdl_state" ]; then
  state_match="FAIL"
  state_failures+=("missing HDL visible state line")
else
  for key in "${state_keys[@]}"; do
    cosim_val=$(state_value "$cosim_state" "$key")
    hdl_val=$(line_value "$hdl_state" "$key")
    if [[ "$hex_keys" == *" $key "* ]]; then
      cosim_val=$(printf '%s' "$cosim_val" | normalize_hex)
      hdl_val=$(printf '%s' "$hdl_val" | normalize_hex)
    fi
    if [ -z "$cosim_val" ] || [ -z "$hdl_val" ] || [ "$cosim_val" != "$hdl_val" ]; then
      state_match="FAIL"
      state_failures+=("$key cosim=${cosim_val:-missing} hdl=${hdl_val:-missing}")
    fi
  done
fi

status="PASS"
if [ "$hdl_reached_dump" != PASS ]; then
  status="INCOMPLETE"
elif [ -z "$cosim_pc" ] || [ -z "$hdl_effective_pc" ] || [ "${cosim_pc,,}" != "${hdl_effective_pc,,}" ]; then
  status="FAIL"
fi
if [ "$vram_match" != PASS ]; then
  status="FAIL"
fi
if [ "$state_match" != PASS ]; then
  status="FAIL"
fi

cat > "$REPORT" <<EOF
# juku_top ${DISPLAY_WRITES}-write state probe

Status: **$status**

This slow diagnostic compares the fast cosim and LVS-checked \`juku_top\` at
$DISPLAY_WRITES framebuffer writes on the vendored \`JUKU1.CPM\` \`TDD\` path. The fast
cosim timing reference first touches PIC at 30,520 writes; the default 30,000
write target proves whether the expensive top-level simulation is still aligned
immediately before that post-banner PIC/FDC window.

## Command

\`\`\`sh
sync/juku_top_30000_state_probe.sh
\`\`\`

## Evidence

| Check | Result |
| --- | --- |
| Target VRAM writes | \`$WRITES\` |
| HDL simulator | \`$SIMULATOR\` |
| Cosim frame cycles | \`$COSIM_FRAME_CYCLES\` |
| HDL frame settings | \`FRAMEIRQ=$HDL_FRAMEIRQ FRAMEPHASE=$HDL_FRAMEPHASE FRAMEMCYC=$HDL_FRAMEMCYC\` |
| Keyboard start VRAM | \`$KEYAT\` |
| HDL reached dump point | $hdl_reached_dump |
| HDL timeout exit code | \`${hdl_rc:-unknown}\` |
| Cosim stop PC | \`0x${cosim_pc:-unknown}\` |
| HDL stop PC | \`0x${hdl_pc:-unknown}\` |
| HDL effective PC | \`0x${hdl_effective_pc:-unknown}\` |
| Cosim/HDL effective PC match | $([ -n "$cosim_pc" ] && [ -n "$hdl_effective_pc" ] && [ "${cosim_pc,,}" = "${hdl_effective_pc,,}" ] && echo PASS || echo FAIL) |
| VRAM dump bytes | \`$vram_bytes\` |
| Cosim VRAM SHA256 | \`$cosim_vram_sha\` |
| HDL VRAM SHA256 | \`$hdl_vram_sha\` |
| Cosim/HDL VRAM match | $vram_match |
| Cosim/HDL visible state match | $state_match |

## Stop State

- Cosim first VRAM line: \`${cosim_first_vram:-none}\`
- Cosim stop line: \`${cosim_stop:-none}\`
- HDL VRAM stop line: \`${hdl_vram_stop:-none}\`
- HDL CPU state line: \`${hdl_cpu:-none}\`
- HDL visible state line: \`${hdl_state:-none}\`
- HDL I/O summary line: \`${hdl_io:-none}\`

## Disposition

- When HDL reaches the requested dump point, this guard compares PC,
  framebuffer bytes, and visible CPU/PPI/PIC/FDC register state against cosim.
- FDC status is intentionally excluded at this pre-FDC boundary because the HDL
  shim reports not-ready before motor/command activity.
- If HDL does not reach the requested dump point within the bound, the result is
  a reachability limit rather than a functional mismatch.
EOF

if [ "${#state_failures[@]}" -ne 0 ]; then
  {
    echo
    echo "## Visible State Failures"
    echo
    for failure in "${state_failures[@]}"; do
      echo "- $failure"
    done
  } >> "$REPORT"
fi

if [ "$hdl_reached_dump" = PASS ]; then
  cat >> "$REPORT" <<EOF

## Result Interpretation

- HDL reached the $DISPLAY_WRITES-write dump point, so the PC, framebuffer, and visible
  state comparisons above are authoritative for that boundary.
EOF
else
  cat >> "$REPORT" <<EOF

## Result Interpretation

- HDL did not reach the $DISPLAY_WRITES-write dump point within the configured timeout,
  so this run is a reachability result, not evidence of state divergence.
- Use a checkpoint/fast-forward or narrower post-banner harness before treating
  this boundary as a functional comparison.
EOF
fi

cat "$REPORT"

if [ "$status" != PASS ]; then
  exit 1
fi
