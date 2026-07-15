#!/usr/bin/env bash
# Legible silkscreen preview of the Rev-A board model: silk + board edge only,
# solid black on white, so reference designators, values, and block labels read
# clearly. Unlike render_placement_preview.sh (copper/pad view), this omits the
# F.Fab layer -- rendering silk AND fab together double-prints every outline and
# reference designator (F.Silkscreen and F.Fab each carry both).
set -euo pipefail

cd "$(dirname "$0")/../../.."

BOARD_JSON="${1:-spinoffs/minimal-vga/kicad/rev-a-physical.board.json}"
OUT="${2:-fab/minimal-vga/review}"
KCLI="$("scripts/find-kicad-cli.sh")"
KICAD_PYTHON="${KICAD_PYTHON:-$("scripts/find-kicad-python.sh")}"

# Locate the KiCad footprint library if not already provided (macOS app bundle
# and the Linux default live in different places).
if [ -z "${KICAD_FOOTPRINTS:-}" ]; then
  for cand in \
    /usr/share/kicad/footprints \
    /opt/homebrew/Caskroom/kicad/*/KiCad/KiCad.app/Contents/SharedSupport/footprints \
    /Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints; do
    [ -d "$cand" ] && { KICAD_FOOTPRINTS="$cand"; break; }
  done
fi
export KICAD_FOOTPRINTS

mkdir -p "$OUT"
TMP_BOARD="$(mktemp "${TMPDIR:-/tmp}/vjuga-silk.XXXXXX.kicad_pcb")"
SVG="$OUT/vjuga-silk.svg"
trap 'rm -f "$TMP_BOARD"' EXIT

MINIMAL_VGA_NO_ZONES=1 "$KICAD_PYTHON" spinoffs/minimal-vga/kicad/gen_rev_a_pcb.py "$BOARD_JSON" "$TMP_BOARD" >/dev/null

"$KCLI" pcb export svg \
  --layers F.Silkscreen,Edge.Cuts \
  --page-size-mode 2 \
  --fit-page-to-board \
  --exclude-drawing-sheet \
  --black-and-white \
  --mode-single \
  --output "$SVG" \
  "$TMP_BOARD" >/dev/null 2>&1

# Rasterize on a white background (rsvg-convert handles the KiCad SVG fonts
# cleanly; ImageMagick can trip over embedded font refs).
if command -v rsvg-convert >/dev/null 2>&1; then
  rsvg-convert --background-color=white -w 2800 "$SVG" -o "$OUT/vjuga-silk.png"
elif command -v magick >/dev/null 2>&1; then
  magick -background white "$SVG" -resize '2800x2800>' -flatten "$OUT/vjuga-silk.png"
else
  echo "Need rsvg-convert or ImageMagick to rasterize $SVG" >&2
  exit 3
fi

echo "Wrote:"
echo "  $SVG"
echo "  $OUT/vjuga-silk.png"
