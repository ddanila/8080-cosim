#!/usr/bin/env bash
# Guard the checkpoint-resumed juku_top EKDOS JBASIC READY prompt proof.
set -euo pipefail
cd "$(dirname "$0")/.."

command -v iverilog >/dev/null || { echo "iverilog not found"; exit 2; }
command -v cc >/dev/null || { echo "cc not found"; exit 2; }

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

REPORT=${EKDOS_JBASIC_CHECKPOINT_REPORT:-$TMP/juku-top-checkpoint-jbasic.md}
OUT="$TMP/ekdos-jbasic-checkpoint.out"

echo "== checkpoint-resumed juku_top EKDOS JBASIC READY check =="
JUKU_TOP_CHECKPOINT_JBASIC_REPORT="$REPORT" \
  sync/juku_top_checkpoint_jbasic_probe.py >"$OUT"

cat "$OUT"

if ! grep -q 'Status: \*\*HDL EKDOS JBASIC READY\*\*' "$REPORT"; then
  echo "EKDOS-JBASIC-CHECKPOINT: FAIL"
  exit 1
fi

if ! grep -q '^\- READY stop line: `\[RESUME-JBASIC\] READY prompt reached' "$REPORT"; then
  echo "EKDOS-JBASIC-CHECKPOINT: FAIL (READY stop missing)"
  exit 1
fi

if ! grep -q '^\- Command echo line: `\[RESUME-JBASIC-CMD\] A>JBASIC command line reached' "$REPORT"; then
  echo "EKDOS-JBASIC-CHECKPOINT: FAIL (command echo missing)"
  exit 1
fi

if ! grep -q '^\- Final visible `A>JBASIC` command line at scanline 71: `yes`' "$REPORT"; then
  echo "EKDOS-JBASIC-CHECKPOINT: FAIL (command glyph missing)"
  exit 1
fi

echo "EKDOS-JBASIC-CHECKPOINT: PASS"
