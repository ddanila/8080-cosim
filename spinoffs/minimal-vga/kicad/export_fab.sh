#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../../.."

BOARD="${1:-spinoffs/minimal-vga/kicad/rev-a-physical.kicad_pcb}"
OUT="${2:-fab/minimal-vga}"
KCLI="${KICAD_CLI:-kicad-cli}"

if [ ! -f "$BOARD" ]; then
  echo "No routed PCB yet: $BOARD" >&2
  echo "Create the Rev A .kicad_pcb before exporting fab files." >&2
  exit 2
fi

if [ "${MINIMAL_VGA_ALLOW_DRC_EXPORT:-0}" != "1" ]; then
  mkdir -p "$OUT"
  if ! "$KCLI" pcb drc --severity-error --exit-code-violations \
      --output "$OUT/drc-report.txt" "$BOARD" >/dev/null; then
    echo "KiCad DRC failed for $BOARD; fab export blocked." >&2
    echo "Report: $OUT/drc-report.txt" >&2
    echo "Set MINIMAL_VGA_ALLOW_DRC_EXPORT=1 only for debug exports." >&2
    exit 3
  fi
fi

mkdir -p "$OUT/gerbers" "$OUT/drill"
mkdir -p "$OUT/assembly" "$OUT/review"
python3 spinoffs/minimal-vga/kicad/export_jlcpcb_assembly.py \
  "$BOARD" \
  spinoffs/minimal-vga/kicad/rev-a.bom.csv \
  "$OUT/assembly"
"$KCLI" pcb export gerbers \
  --layers "F.Cu,In1.Cu,In2.Cu,B.Cu,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts" \
  -o "$OUT/gerbers/" "$BOARD"
"$KCLI" pcb export drill --format excellon --drill-origin absolute -o "$OUT/drill/" "$BOARD"
kicad-cli sch export pdf \
  --black-and-white \
  --output "$OUT/review/rev-a-physical-schematic.pdf" \
  spinoffs/minimal-vga/kicad/rev-a-physical.kicad_sch
"$KCLI" pcb export pdf \
  --layers F.Fab,F.SilkS,F.CrtYd,Edge.Cuts \
  --common-layers Edge.Cuts \
  --black-and-white \
  --mode-single \
  --output "$OUT/review/rev-a-assembly-front.pdf" \
  "$BOARD"
"$KCLI" pcb export pdf \
  --layers B.Fab,B.SilkS,B.CrtYd,Edge.Cuts \
  --common-layers Edge.Cuts \
  --black-and-white \
  --mirror \
  --mode-single \
  --output "$OUT/review/rev-a-assembly-back.pdf" \
  "$BOARD"
"$KCLI" pcb export pos \
  --side both \
  --format csv \
  --units mm \
  --output "$OUT/assembly/rev-a-position.csv" \
  "$BOARD"
cp spinoffs/minimal-vga/kicad/rev-a.bom.csv "$OUT/rev-a.engineering-bom.csv"
cp spinoffs/minimal-vga/kicad/rev-a-jlcpcb-cpn-checklist.csv "$OUT/assembly/"
cp spinoffs/minimal-vga/kicad/fab-notes.md "$OUT/"
echo "Exported fab package to $OUT"
