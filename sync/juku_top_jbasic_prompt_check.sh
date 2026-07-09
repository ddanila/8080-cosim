#!/usr/bin/env bash
# Guard the committed uninterrupted juku_top EKDOS JBASIC READY evidence.
set -euo pipefail
cd "$(dirname "$0")/.."

REPORT=docs/juku-top-jbasic-verilator-probe.md

grep -q 'Status: \*\*HDL JUKU_TOP JBASIC READY REACHED\*\*' "$REPORT"
grep -q 'EKDOS prompt line: `\[PROMPT\] EKDOS A> prompt reached x=0 y=70 mcyc=2733010 vram=73405 pc=0x097a`' "$REPORT"
grep -q 'EKDOS JBASIC command line: `\[JBASIC-CMD\] A>JBASIC command line reached mcyc=4062390 vram=73485 pc=0x097a`' "$REPORT"
grep -q 'BASIC READY line: `\[JBASIC\] READY prompt reached mcyc=4765627 vram=73885 pc=0x097a`' "$REPORT"
grep -q 'FDC state line: `\[FDCSTATE\] data_reads=19968 buffer_pos=0 buffer_len=0`' "$REPORT"

if [ "${JUKU_TOP_JBASIC_DEEP:-0}" = "1" ]; then
  command -v verilator >/dev/null || { echo "verilator not found"; exit 2; }
  tmp=$(mktemp)
  trap 'rm -f "$tmp"' EXIT
  JUKU_TOP_FDC_SIM=verilator \
  JUKU_TOP_FDC_DISK=media/disks/JUKPROG2.CPM \
  JUKU_TOP_FDC_TIMECAP=30000000000 \
  JUKU_TOP_FDC_TIMEOUT="${JUKU_TOP_JBASIC_TIMEOUT:-900}" \
  JUKU_TOP_FDC_MAXVRAM=85000 \
  JUKU_TOP_FDC_FRAMEIRQ=0 \
  JUKU_TOP_FDC_FRAMEMCYC=50761 \
  JUKU_TOP_FDC_FRAMEPHASE=49891 \
  JUKU_TOP_FDC_STOPPIC=0 \
  JUKU_TOP_FDC_STOPFDC=0 \
  JUKU_TOP_FDC_STOPFDCDATA=0 \
  JUKU_TOP_FDC_STOPPROMPT=0 \
  JUKU_TOP_FDC_JBASICKEYS=1 \
  JUKU_TOP_FDC_STOPJBASICCMD=0 \
  JUKU_TOP_FDC_STOPJBASICREADY=1 \
  JUKU_TOP_FDC_TRACEFDC=0 \
  JUKU_TOP_FDC_TRACEPPI=0 \
  JUKU_TOP_FDC_TRACEIRQ=0 \
  JUKU_TOP_FDC_TRACEPROGRESS=10000 \
  JUKU_TOP_FDC_REPORT="$tmp" \
  JUKU_TOP_FDC_REPORT_TITLE='juku_top uninterrupted JBASIC READY guard' \
    sync/juku_top_fdc_probe.sh
  grep -q 'Status: \*\*HDL JUKU_TOP JBASIC READY REACHED\*\*' "$tmp"
  grep -q 'BASIC READY line: `\[JBASIC\] READY prompt reached' "$tmp"
  grep -q 'FDC state line: `\[FDCSTATE\] data_reads=19968 buffer_pos=0 buffer_len=0`' "$tmp"
fi

echo "JUKU-TOP-JBASIC-PROMPT-CHECK: PASS"
