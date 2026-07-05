#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../../.."

BOARD_JSON="${1:-spinoffs/minimal-vga/kicad/rev-a-physical.board.json}"
OUT="${2:-fab/minimal-vga/review}"
KCLI="$("scripts/find-kicad-cli.sh")"

mkdir -p "$OUT"
TMP_BOARD="$(mktemp "${TMPDIR:-/tmp}/vjuga-placement.XXXXXX.kicad_pcb")"
TMP_SVG="$(mktemp "${TMPDIR:-/tmp}/vjuga-placement.XXXXXX.svg")"
trap 'rm -f "$TMP_BOARD" "$TMP_SVG"' EXIT

MINIMAL_VGA_NO_ZONES=1 python3 spinoffs/minimal-vga/kicad/gen_rev_a_pcb.py "$BOARD_JSON" "$TMP_BOARD" >/dev/null

"$KCLI" pcb export svg \
  --layers F.Cu,F.Mask,F.SilkS,Edge.Cuts \
  --page-size-mode 2 \
  --fit-page-to-board \
  --exclude-drawing-sheet \
  --drill-shape-opt 2 \
  --black-and-white \
  --mode-single \
  --output "$TMP_SVG" \
  "$TMP_BOARD" >/dev/null

cp "$TMP_SVG" "$OUT/vjuga-placement-top.svg"

if command -v magick >/dev/null 2>&1; then
  magick -background white "$TMP_SVG" -resize '2400x2400>' "$OUT/vjuga-placement-top.png"
elif command -v convert >/dev/null 2>&1; then
  convert -background white "$TMP_SVG" -resize '2400x2400>' "$OUT/vjuga-placement-top.png"
elif command -v rsvg-convert >/dev/null 2>&1; then
  rsvg-convert -w 2400 "$TMP_SVG" -o "$OUT/vjuga-placement-top.png"
else
  echo "Need ImageMagick (magick/convert) or rsvg-convert to rasterize SVG." >&2
  exit 3
fi

echo "Wrote:"
echo "  $OUT/vjuga-placement-top.svg"
echo "  $OUT/vjuga-placement-top.png"
