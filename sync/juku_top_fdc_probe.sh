#!/usr/bin/env bash
# Bounded diagnostic for the full juku_top ROMBIOS -> FDC boundary.
#
# The same harness can stop at early decoded WD1793 activity or run through the
# committed uninterrupted EKDOS/JBASIC prompt boundaries. Long reruns remain
# opt-in because the bit-sliced top-level simulation is expensive.
set -euo pipefail
cd "$(dirname "$0")/.."

command -v iverilog >/dev/null || { echo "iverilog not found"; exit 2; }
command -v vvp >/dev/null || { echo "vvp not found"; exit 2; }

REPORT=${JUKU_TOP_FDC_REPORT:-${TMPDIR:-/tmp}/juku-top-fdc-probe.md}
REPORT_TITLE=${JUKU_TOP_FDC_REPORT_TITLE:-juku_top FDC probe}
SIMULATOR=${JUKU_TOP_FDC_SIM:-icarus}
DISK=${JUKU_TOP_FDC_DISK:-media/disks/JUKU1.CPM}
KEYAT=${JUKU_TOP_FDC_KEYAT:-42000}
KHOLD=${JUKU_TOP_FDC_KHOLD:-900000}
KGAP=${JUKU_TOP_FDC_KGAP:-900000}
FRAMEIRQ=${JUKU_TOP_FDC_FRAMEIRQ:-80000}
FRAMEPHASE=${JUKU_TOP_FDC_FRAMEPHASE:-0}
FRAMEMCYC=${JUKU_TOP_FDC_FRAMEMCYC:-0}
MAXVRAM=${JUKU_TOP_FDC_MAXVRAM:-88000}
TIMECAP=${JUKU_TOP_FDC_TIMECAP:-900000000}
TRACEPROGRESS=${JUKU_TOP_FDC_TRACEPROGRESS:-5000}
VRAMSTOP_SYNC=${JUKU_TOP_FDC_VRAMSTOP_SYNC:-0}
TRACEIO=${JUKU_TOP_FDC_TRACEIO:-0}
TRACECHK=${JUKU_TOP_FDC_TRACECHK:-0}
TRACEPPI=${JUKU_TOP_FDC_TRACEPPI:-1}
TRACEIRQ=${JUKU_TOP_FDC_TRACEIRQ:-1}
TRACEFDC=${JUKU_TOP_FDC_TRACEFDC:-1}
STOPIO=${JUKU_TOP_FDC_STOPIO:-0}
STOPFDC=${JUKU_TOP_FDC_STOPFDC:-1}
STOPFDCDATA=${JUKU_TOP_FDC_STOPFDCDATA:-0}
STOPPIC=${JUKU_TOP_FDC_STOPPIC:-0}
STOPPPI=${JUKU_TOP_FDC_STOPPPI:-0}
STOPPROMPT=${JUKU_TOP_FDC_STOPPROMPT:-0}
JBASICKEYS=${JUKU_TOP_FDC_JBASICKEYS:-0}
STOPJBASICCMD=${JUKU_TOP_FDC_STOPJBASICCMD:-0}
STOPJBASICREADY=${JUKU_TOP_FDC_STOPJBASICREADY:-0}
COMMAND_KEY_MCYC=${JUKU_TOP_FDC_COMMAND_KEY_MCYC:-0}
TIMEOUT_S=${JUKU_TOP_FDC_TIMEOUT:-60}
VRAM_COPY=${JUKU_TOP_FDC_VRAM_COPY:-}
STOPPC=${JUKU_TOP_FDC_STOPPC:-}
STOPPC_SKIP=${JUKU_TOP_FDC_STOPPC_SKIP:-0}

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

SIM="$TMP/juku_top_tb"
OUT="$TMP/out.txt"
BUILD_OUT="$TMP/build.txt"
OLD_VRAM="$TMP/vram_top.old"
if [ -f hdl/sim/vram_top.bin ]; then cp hdl/sim/vram_top.bin "$OLD_VRAM"; fi

build_failed() {
  local build_rc=$1
  local errors
  errors=$(sed -n '/^%Error/p' "$BUILD_OUT")
  if [ -z "$errors" ]; then errors=$(tail -n 10 "$BUILD_OUT"); fi
  cat > "$REPORT" <<EOF
# $REPORT_TITLE

Status: **HDL JUKU_TOP BUILD BLOCKED**

The $SIMULATOR build exited with code $build_rc. No simulation ran.

## Build errors

\`\`\`text
$errors
\`\`\`

Resolve the simulator build failure before treating a prompt boundary as
verified for the current source. See the simulator compatibility section in
sync/README.md.
EOF
  printf '%s\n' "$errors" >&2
  exit "$build_rc"
}

case "$SIMULATOR" in
  icarus)
    iverilog -g2012 -o "$SIM" hdl/vendor/vm80a.v hdl/devices.v hdl/juku_top.v hdl/sim/juku_top_tb.v >"$BUILD_OUT" 2>&1 || build_failed $?
    ;;
  verilator)
    command -v verilator >/dev/null || { echo "verilator not found"; exit 2; }
    verilator --binary --timing -Wno-fatal --top-module juku_top_tb \
      -Mdir "$TMP/obj" \
      hdl/vendor/vm80a.v hdl/devices.v hdl/juku_top.v hdl/sim/juku_top_tb.v >"$BUILD_OUT" 2>&1 || build_failed $?
    SIM="$TMP/obj/Vjuku_top_tb"
    ;;
  *)
    echo "unsupported JUKU_TOP_FDC_SIM=$SIMULATOR (expected icarus or verilator)" >&2
    exit 2
    ;;
esac

set +e
STOPPC_PLUSARG=
if [ -n "$STOPPC" ]; then STOPPC_PLUSARG="+stoppc=$STOPPC +stoppc_skip=$STOPPC_SKIP"; fi
if command -v timeout >/dev/null; then
  if [ "$SIMULATOR" = icarus ]; then
    timeout "$TIMEOUT_S" vvp "$SIM" \
      +disk="$DISK" +disk_heads=2 \
      +frameirq="$FRAMEIRQ" \
      +framephase="$FRAMEPHASE" \
      +frame_mcyc="$FRAMEMCYC" \
      +traceprogress="$TRACEPROGRESS" \
      +vramstop_sync="$VRAMSTOP_SYNC" \
      $STOPPC_PLUSARG \
      +ekdoskeys=1 +jbasickeys="$JBASICKEYS" +command_key_mcyc="$COMMAND_KEY_MCYC" +keyat="$KEYAT" +khold="$KHOLD" +kgap="$KGAP" \
      +traceio="$TRACEIO" +tracechk="$TRACECHK" +stopio="$STOPIO" +tracekbd=1 +tracepic=1 +stoppic="$STOPPIC" +traceppi="$TRACEPPI" +traceirq="$TRACEIRQ" +stopppi="$STOPPPI" +tracefdc="$TRACEFDC" +stopfdc="$STOPFDC" +stopfdcdata="$STOPFDCDATA" \
      +stopprompt="$STOPPROMPT" +stopjbasiccmd="$STOPJBASICCMD" +stopjbasicready="$STOPJBASICREADY" \
      +maxvram="$MAXVRAM" +timecap="$TIMECAP" >"$OUT" 2>&1
  else
    timeout "$TIMEOUT_S" "$SIM" \
      +disk="$DISK" +disk_heads=2 \
      +frameirq="$FRAMEIRQ" \
      +framephase="$FRAMEPHASE" \
      +frame_mcyc="$FRAMEMCYC" \
      +traceprogress="$TRACEPROGRESS" \
      +vramstop_sync="$VRAMSTOP_SYNC" \
      $STOPPC_PLUSARG \
      +ekdoskeys=1 +jbasickeys="$JBASICKEYS" +command_key_mcyc="$COMMAND_KEY_MCYC" +keyat="$KEYAT" +khold="$KHOLD" +kgap="$KGAP" \
      +traceio="$TRACEIO" +tracechk="$TRACECHK" +stopio="$STOPIO" +tracekbd=1 +tracepic=1 +stoppic="$STOPPIC" +traceppi="$TRACEPPI" +traceirq="$TRACEIRQ" +stopppi="$STOPPPI" +tracefdc="$TRACEFDC" +stopfdc="$STOPFDC" +stopfdcdata="$STOPFDCDATA" \
      +stopprompt="$STOPPROMPT" +stopjbasiccmd="$STOPJBASICCMD" +stopjbasicready="$STOPJBASICREADY" \
      +maxvram="$MAXVRAM" +timecap="$TIMECAP" >"$OUT" 2>&1
  fi
  rc=$?
else
  if [ "$SIMULATOR" = icarus ]; then
    vvp "$SIM" \
      +disk="$DISK" +disk_heads=2 \
      +frameirq="$FRAMEIRQ" \
      +framephase="$FRAMEPHASE" \
      +frame_mcyc="$FRAMEMCYC" \
      +traceprogress="$TRACEPROGRESS" \
      +vramstop_sync="$VRAMSTOP_SYNC" \
      $STOPPC_PLUSARG \
      +ekdoskeys=1 +jbasickeys="$JBASICKEYS" +command_key_mcyc="$COMMAND_KEY_MCYC" +keyat="$KEYAT" +khold="$KHOLD" +kgap="$KGAP" \
      +traceio="$TRACEIO" +tracechk="$TRACECHK" +stopio="$STOPIO" +tracekbd=1 +tracepic=1 +stoppic="$STOPPIC" +traceppi="$TRACEPPI" +traceirq="$TRACEIRQ" +stopppi="$STOPPPI" +tracefdc="$TRACEFDC" +stopfdc="$STOPFDC" +stopfdcdata="$STOPFDCDATA" \
      +stopprompt="$STOPPROMPT" +stopjbasiccmd="$STOPJBASICCMD" +stopjbasicready="$STOPJBASICREADY" \
      +maxvram="$MAXVRAM" +timecap="$TIMECAP" >"$OUT" 2>&1
  else
    "$SIM" \
      +disk="$DISK" +disk_heads=2 \
      +frameirq="$FRAMEIRQ" \
      +framephase="$FRAMEPHASE" \
      +frame_mcyc="$FRAMEMCYC" \
      +traceprogress="$TRACEPROGRESS" \
      +vramstop_sync="$VRAMSTOP_SYNC" \
      $STOPPC_PLUSARG \
      +ekdoskeys=1 +jbasickeys="$JBASICKEYS" +command_key_mcyc="$COMMAND_KEY_MCYC" +keyat="$KEYAT" +khold="$KHOLD" +kgap="$KGAP" \
      +traceio="$TRACEIO" +tracechk="$TRACECHK" +stopio="$STOPIO" +tracekbd=1 +tracepic=1 +stoppic="$STOPPIC" +traceppi="$TRACEPPI" +traceirq="$TRACEIRQ" +stopppi="$STOPPPI" +tracefdc="$TRACEFDC" +stopfdc="$STOPFDC" +stopfdcdata="$STOPFDCDATA" \
      +stopprompt="$STOPPROMPT" +stopjbasiccmd="$STOPJBASICCMD" +stopjbasicready="$STOPJBASICREADY" \
      +maxvram="$MAXVRAM" +timecap="$TIMECAP" >"$OUT" 2>&1
  fi
  rc=$?
fi
set -e

if [ -n "$VRAM_COPY" ] && [ -f hdl/sim/vram_top.bin ]; then
  cp hdl/sim/vram_top.bin "$VRAM_COPY"
fi

if [ -f "$OLD_VRAM" ]; then cp "$OLD_VRAM" hdl/sim/vram_top.bin; else rm -f hdl/sim/vram_top.bin; fi

fdc_stop=$(grep -m1 '^\[FDC\] stop' "$OUT" || true)
fdc_data_stop=$(grep -m1 '^\[FDC\] data-stop' "$OUT" || true)
fdc_first=$(grep -m1 '^\[FDC\]' "$OUT" || true)
prompt_line=$(grep -m1 '^\[PROMPT\] EKDOS A> prompt reached' "$OUT" || true)
jbasic_cmd_line=$(grep -m1 '^\[JBASIC-CMD\]' "$OUT" || true)
jbasic_ready_line=$(grep -m1 '^\[JBASIC\]' "$OUT" || true)
key_first=$(grep -m1 '^\[KBD\]' "$OUT" || true)
key_last=$(grep '^\[KBD\]' "$OUT" | tail -1 || true)
pic_first=$(grep -m1 '^\[PIC\]' "$OUT" || true)
pic_stop=$(grep -m1 '^\[PIC\] stop' "$OUT" || true)
ppi_key_first=$(grep -m1 '^\[PPI0\] IN' "$OUT" || true)
ppi_stop=$(grep -m1 '^\[PPI0\] stop' "$OUT" || true)
ppi_first=$(grep -m1 '^\[PPI0\]' "$OUT" || true)
irq_first=$(grep -m1 '^\[IRQ\]' "$OUT" || true)
rawio_first=$(grep -m1 '^\[RAWIO\]' "$OUT" || true)
rawio_stop=$(grep -m1 '^\[RAWIO\] stop' "$OUT" || true)
chk_first=$(grep -m1 '^\[CHKHDL' "$OUT" || true)
chk_last=$(grep '^\[CHKHDL' "$OUT" | tail -1 || true)
io_summary=$(grep -m1 '^\[IO\]' "$OUT" || true)
fdc_state=$(grep -m1 '^\[FDCSTATE\]' "$OUT" || true)
first_vram=$(grep -m1 '^\[VRAM\] first video write' "$OUT" || true)
last_progress=$(grep '^\[VRAM\] progress' "$OUT" | tail -1 || true)
vram_stop=$(grep -m1 '^\[VRAM\] [0-9][0-9]* writes' "$OUT" || true)
timecap_line=$(grep -m1 '^\[SIM\] time cap' "$OUT" || true)
cpu_line=$(grep -m1 '^\[CPU\]' "$OUT" || true)
state_line=$(grep -m1 '^\[STATE\]' "$OUT" || true)
pc_stop=$(grep -m1 '^\[PC\] stop' "$OUT" || true)
disk_line=$(grep -m1 '^FDC-1793: loaded raw disk' "$OUT" || true)
fdc_lines=$(grep -c '^\[FDC\]' "$OUT" || true)
chk_lines=$(grep -c '^\[CHKHDL' "$OUT" || true)
kbd_lines=$(grep -c '^\[KBD\]' "$OUT" || true)
progress_lines=$(grep -c '^\[VRAM\] progress' "$OUT" || true)
pic_lines=$(grep -c '^\[PIC\]' "$OUT" || true)
ppi_key_lines=$(grep -c '^\[PPI0\] IN' "$OUT" || true)
ppi_lines=$(grep -c '^\[PPI0\]' "$OUT" || true)
irq_lines=$(grep -c '^\[IRQ\]' "$OUT" || true)
rawio_lines=$(grep -c '^\[RAWIO\]' "$OUT" || true)

status="HDL JUKU_TOP FDC PATH NOT YET OBSERVED"
fdc_result="NO"
prompt_result="NO"
if [ -n "$jbasic_ready_line" ]; then
  status="HDL JUKU_TOP JBASIC READY REACHED"
  fdc_result="YES"
  prompt_result="YES"
elif [ -n "$jbasic_cmd_line" ]; then
  status="HDL JUKU_TOP JBASIC COMMAND REACHED"
  fdc_result="YES"
  prompt_result="YES"
elif [ -n "$prompt_line" ]; then
  status="HDL JUKU_TOP EKDOS PROMPT REACHED"
  fdc_result="YES"
  prompt_result="YES"
elif [ -n "$fdc_stop" ] || [ -n "$fdc_data_stop" ]; then
  status="HDL JUKU_TOP FDC PATH OBSERVED"
  fdc_result="YES"
elif [ "$rc" -eq 124 ]; then
  status="HDL JUKU_TOP FDC PROBE TIMED OUT BEFORE FDC I/O"
fi

emit_trace() {
  local trace_text
  trace_text=$(grep "$2" "$OUT" || true)
  if [ -n "$trace_text" ]; then
    printf '## %s\n\n```text\n%s\n```\n' "$1" "$trace_text"
  fi
}

emit_state() {
  if [ -n "$2" ]; then
    printf -- '- %s: `%s`\n' "$1" "$2"
  fi
}

cat > "$REPORT" <<EOF
# $REPORT_TITLE

Status: **$status**

This report records a bounded \`juku_top\` run with the vendored disk image,
frame interrupts and ROMBIOS \`TDD\` keyboard sequence. Its status describes
that recorded run; checking the committed report does not rerun current HDL.
The harness defaults to Icarus and also accepts Verilator. See
[simulator compatibility](../sync/README.md#simulator-compatibility) before
attempting a Verilator rerun.

## Harness entry point

\`\`\`sh
sync/juku_top_fdc_probe.sh
\`\`\`

Harness defaults and all overrides are defined in
[\`sync/juku_top_fdc_probe.sh\`](../sync/juku_top_fdc_probe.sh).
The bare command uses the default early-FDC stop; it does not reproduce
this recorded prompt run. Use the recorded settings below for that case,
subject to the simulator compatibility limit above.

Requires Bash, \`iverilog\` and \`vvp\` for either simulator, plus \`verilator\` when
selected. Apply settings through \`JUKU_TOP_FDC_*\` environment variables, for
example \`JUKU_TOP_FDC_STOPPROMPT=1\`; the settings list below omits that prefix.
The output defaults to \`\${TMPDIR:-/tmp}/juku-top-fdc-probe.md\` and is overwritten;
set \`JUKU_TOP_FDC_REPORT\` to choose another path.

Recorded settings: \`DISK=$DISK SIM=$SIMULATOR KEYAT=$KEYAT KHOLD=$KHOLD KGAP=$KGAP FRAMEIRQ=$FRAMEIRQ FRAMEPHASE=$FRAMEPHASE FRAMEMCYC=$FRAMEMCYC TRACEPROGRESS=$TRACEPROGRESS VRAMSTOP_SYNC=$VRAMSTOP_SYNC TRACEIO=$TRACEIO TRACECHK=$TRACECHK TRACEPPI=$TRACEPPI TRACEIRQ=$TRACEIRQ TRACEFDC=$TRACEFDC STOPIO=$STOPIO MAXVRAM=$MAXVRAM TIMECAP=$TIMECAP STOPFDC=$STOPFDC STOPFDCDATA=$STOPFDCDATA STOPPIC=$STOPPIC STOPPPI=$STOPPPI STOPPROMPT=$STOPPROMPT JBASICKEYS=$JBASICKEYS STOPJBASICCMD=$STOPJBASICCMD STOPJBASICREADY=$STOPJBASICREADY COMMAND_KEY_MCYC=$COMMAND_KEY_MCYC STOPPC=${STOPPC:-none} STOPPC_SKIP=$STOPPC_SKIP TIMEOUT=$TIMEOUT_S\`.

## Evidence

| Check | Result |
| --- | --- |
| simulator | \`$SIMULATOR\` |
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
| EKDOS \`A>\` prompt bitmap observed | $prompt_result |
| EKDOS \`A>JBASIC\` command bitmap observed | $(if [ -n "$jbasic_cmd_line" ]; then echo YES; else echo NO; fi) |
| BASIC \`READY\` prompt bitmap observed | $(if [ -n "$jbasic_ready_line" ]; then echo YES; else echo NO; fi) |
| keyboard trace lines | \`$kbd_lines\` |
| VRAM progress trace lines | \`$progress_lines\` |
| PIC trace lines | \`$pic_lines\` |
| PPI key-read trace lines | \`$ppi_key_lines\` |
| PPI trace lines | \`$ppi_lines\` |
| IRQ trace lines | \`$irq_lines\` |
| raw I/O trace lines | \`$rawio_lines\` |
| FDC trace lines | \`$fdc_lines\` |
| checksum trace lines | \`$chk_lines\` |

## Stop State

$(
emit_state 'Disk line' "$disk_line"
emit_state 'First VRAM line' "$first_vram"
emit_state 'Last VRAM progress line' "$last_progress"
emit_state 'VRAM stop line' "$vram_stop"
emit_state 'First keyboard line' "$key_first"
emit_state 'Last keyboard line' "$key_last"
emit_state 'First PIC line' "$pic_first"
emit_state 'PIC stop line' "$pic_stop"
emit_state 'First PPI key-read line' "$ppi_key_first"
emit_state 'First PPI line' "$ppi_first"
emit_state 'PPI stop line' "$ppi_stop"
emit_state 'First IRQ line' "$irq_first"
emit_state 'First raw I/O line' "$rawio_first"
emit_state 'Raw I/O stop line' "$rawio_stop"
emit_state 'First checksum line' "$chk_first"
emit_state 'Last checksum line' "$chk_last"
emit_state 'First FDC line' "$fdc_first"
emit_state 'FDC stop line' "$fdc_stop"
emit_state 'FDC data-stop line' "$fdc_data_stop"
emit_state 'EKDOS prompt line' "$prompt_line"
emit_state 'EKDOS JBASIC command line' "$jbasic_cmd_line"
emit_state 'BASIC READY line' "$jbasic_ready_line"
emit_state 'PC stop line' "$pc_stop"
emit_state 'Time-cap line' "$timecap_line"
emit_state 'CPU state line' "$cpu_line"
emit_state 'Visible state line' "$state_line"
emit_state 'I/O summary line' "$io_summary"
emit_state 'FDC state line' "$fdc_state"
)

$(emit_trace 'Checksum Trace' '^\[CHKHDL')
$(emit_trace 'PPI0 Trace' '^\[PPI0\]')
$(emit_trace 'Raw I/O Trace' '^\[RAWIO\]')
$(emit_trace 'IRQ Trace' '^\[IRQ\]')
$(emit_trace 'FDC Trace' '^\[FDC\]')

## Scope

- \`STOPPROMPT=1\` stops on the EKDOS \`A>\` bitmap. \`JBASICKEYS=1\` with
  \`STOPJBASICREADY=1\` targets disk BASIC \`READY\`; use \`JUKPROG2.CPM\` for
  the preserved live-load BASIC candidate.
- The status and markers describe the recorded stop. A zero runner exit
  also permits a timeout (\`124\`); it does not by itself prove either prompt.
- [Timing reference](ekdos-timing-reference.md) pins the C-model anchors.
  This diagnostic does not establish physical FDC behavior.
EOF

echo "JUKU-TOP-FDC-PROBE: wrote $REPORT"
cat "$REPORT"

if [ "$rc" -ne 0 ] && [ "$rc" -ne 124 ]; then
  exit "$rc"
fi
