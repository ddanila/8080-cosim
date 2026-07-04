#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../../.."

BOARD="${1:-spinoffs/minimal-vga/kicad/rev-a-physical.kicad_pcb}"
OUT="${2:-fab/minimal-vga/review}"
KCLI="$("scripts/find-kicad-cli.sh")"

if [ ! -f "$BOARD" ]; then
  echo "No PCB found: $BOARD" >&2
  exit 2
fi

mkdir -p "$OUT"
TMP_SVG="$(mktemp "${TMPDIR:-/tmp}/minimal-vga-top-bare.XXXXXX.svg")"
trap 'rm -f "$TMP_SVG"' EXIT

"$KCLI" pcb export svg \
  --layers F.Cu,F.Mask,F.SilkS,Edge.Cuts \
  --page-size-mode 2 \
  --fit-page-to-board \
  --exclude-drawing-sheet \
  --mode-single \
  --output "$TMP_SVG" \
  "$BOARD" >/dev/null

if command -v magick >/dev/null 2>&1; then
  magick -background white "$TMP_SVG" -resize '2400x2400>' "$OUT/rev-a-top-bare.png"
elif command -v convert >/dev/null 2>&1; then
  convert -background white "$TMP_SVG" -resize '2400x2400>' "$OUT/rev-a-top-bare.png"
elif command -v rsvg-convert >/dev/null 2>&1; then
  rsvg-convert -w 2400 "$TMP_SVG" -o "$OUT/rev-a-top-bare.png"
else
  echo "Need ImageMagick (magick/convert) or rsvg-convert to rasterize SVG." >&2
  exit 3
fi

"$KCLI" pcb render \
  --side top \
  --quality high \
  --width 2400 \
  --height 1800 \
  --background opaque \
  --output "$OUT/rev-a-top-populated.png" \
  "$BOARD"

echo "Wrote:"
echo "  $OUT/rev-a-top-bare.png"
echo "  $OUT/rev-a-top-populated.png"
