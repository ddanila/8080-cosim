#!/bin/sh
# Export the fab package (gerbers + drill) from the routed board.
# Usage: sh kicad/export_fab.sh [board] [outdir]
set -e
KCLI="$(scripts/find-kicad-cli.sh)"
BOARD="${1:-kicad/juku_routed.kicad_pcb}"
OUT="${2:-fab/gerbers}"
mkdir -p "$OUT"
"$KCLI" pcb export gerbers --layers "F.Cu,B.Cu,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts" \
    -o "$OUT/" "$BOARD"
"$KCLI" pcb export drill --format excellon --drill-origin absolute -o "$OUT/" "$BOARD"
echo "--- fab package ---"
ls -la "$OUT" | awk 'NR>1 {print $5, $NF}'
