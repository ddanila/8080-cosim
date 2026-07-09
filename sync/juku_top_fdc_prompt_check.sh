#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

ALIGN_REPORT=docs/juku-top-fdc-alignment.md
PROBE_REPORT=docs/juku-top-fdc-verilator-probe.md

python3 scripts/report_juku_top_fdc_alignment.py
git diff --exit-code -- "$ALIGN_REPORT"

grep -q 'Status: \*\*HDL JUKU_TOP EKDOS PROMPT REACHED\*\*' "$PROBE_REPORT"
grep -q 'EKDOS prompt line: `\[PROMPT\] EKDOS A> prompt reached x=0 y=70 mcyc=2701313 vram=73405 pc=0x097a`' "$PROBE_REPORT"
grep -q 'FDC state line: `\[FDCSTATE\] data_reads=10752 buffer_pos=0 buffer_len=0`' "$PROBE_REPORT"
grep -q 'Status: \*\*HDL RESET RUN REACHES EKDOS A> PROMPT\*\*' "$ALIGN_REPORT"

if [ "${JUKU_TOP_FDC_PROMPT_DEEP:-0}" = "1" ]; then
  command -v verilator >/dev/null || { echo "verilator not found"; exit 2; }
  tmp=$(mktemp)
  trap 'rm -f "$tmp"' EXIT
  JUKU_TOP_FDC_SIM=verilator \
  JUKU_TOP_FDC_TIMECAP=12000000000 \
  JUKU_TOP_FDC_TIMEOUT="${JUKU_TOP_FDC_PROMPT_TIMEOUT:-420}" \
  JUKU_TOP_FDC_MAXVRAM=100000 \
  JUKU_TOP_FDC_FRAMEIRQ=0 \
  JUKU_TOP_FDC_FRAMEMCYC=50761 \
  JUKU_TOP_FDC_FRAMEPHASE=49891 \
  JUKU_TOP_FDC_STOPPIC=0 \
  JUKU_TOP_FDC_STOPFDC=0 \
  JUKU_TOP_FDC_STOPFDCDATA=0 \
  JUKU_TOP_FDC_STOPPROMPT=1 \
  JUKU_TOP_FDC_TRACEFDC=0 \
  JUKU_TOP_FDC_TRACEPPI=0 \
  JUKU_TOP_FDC_TRACEIRQ=0 \
  JUKU_TOP_FDC_TRACEPROGRESS=10000 \
  JUKU_TOP_FDC_REPORT="$tmp" \
  JUKU_TOP_FDC_REPORT_TITLE='juku_top calibrated FDC prompt guard' \
    sync/juku_top_fdc_probe.sh
  grep -q 'Status: \*\*HDL JUKU_TOP EKDOS PROMPT REACHED\*\*' "$tmp"
  grep -q 'EKDOS prompt line: `\[PROMPT\] EKDOS A> prompt reached x=0 y=70' "$tmp"
  grep -q 'FDC state line: `\[FDCSTATE\] data_reads=10752 buffer_pos=0 buffer_len=0`' "$tmp"
fi

echo "JUKU-TOP-FDC-PROMPT-CHECK: PASS"
