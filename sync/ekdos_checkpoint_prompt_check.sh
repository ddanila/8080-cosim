#!/usr/bin/env bash
# Guard the checkpoint-resumed juku_top EKDOS A> prompt proof.
set -euo pipefail
cd "$(dirname "$0")/.."

command -v iverilog >/dev/null || { echo "iverilog not found"; exit 2; }
command -v cc >/dev/null || { echo "cc not found"; exit 2; }

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

REPORT=${EKDOS_CHECKPOINT_PROMPT_REPORT:-$TMP/juku-top-checkpoint-fdc-prompt.md}
OUT="$TMP/ekdos-checkpoint-prompt.out"

echo "== checkpoint-resumed juku_top EKDOS prompt check =="
JUKU_TOP_CHECKPOINT_FDC_CYCLES=${JUKU_TOP_CHECKPOINT_FDC_CYCLES:-10066690} \
JUKU_TOP_CHECKPOINT_FDC_STOP_DATA_READS=${JUKU_TOP_CHECKPOINT_FDC_STOP_DATA_READS:-0} \
JUKU_TOP_CHECKPOINT_FDC_STOP_PROMPT=${JUKU_TOP_CHECKPOINT_FDC_STOP_PROMPT:-1} \
JUKU_TOP_CHECKPOINT_FDC_TIMEOUT=${JUKU_TOP_CHECKPOINT_FDC_TIMEOUT:-300} \
JUKU_TOP_CHECKPOINT_FDC_REPORT="$REPORT" \
  sync/juku_top_checkpoint_fdc_probe.py >"$OUT"

cat "$OUT"

if ! grep -q 'Status: \*\*PASS\*\*' "$REPORT"; then
  echo "EKDOS-CHECKPOINT-PROMPT: FAIL"
  exit 1
fi

if ! grep -q '^\- Prompt stop line: `\[RESUME-PROMPT\] EKDOS A> prompt reached' "$REPORT"; then
  echo "EKDOS-CHECKPOINT-PROMPT: FAIL (prompt stop missing)"
  exit 1
fi

echo "EKDOS-CHECKPOINT-PROMPT: PASS"
