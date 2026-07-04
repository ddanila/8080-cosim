#!/bin/sh
# Regenerate the board preview PNGs in renders/ from the routed board.
# Run after any change to kicad/juku_routed.kicad_pcb (the pre-commit hook in
# .githooks/ does this automatically when the board is staged).
set -e
cd "$(dirname "$0")/.."
KCLI="$(scripts/find-kicad-cli.sh)"
BOARD="${1:-kicad/juku_routed.kicad_pcb}"
mkdir -p renders
for side in front back; do
  if [ "$side" = front ]; then L="F.Cu,F.SilkS,Edge.Cuts"; else L="B.Cu,B.SilkS,Edge.Cuts"; fi
  "$KCLI" pcb export svg --layers "$L" --page-size-mode 2 --fit-page-to-board \
      --exclude-drawing-sheet -o "/tmp/juku_$side.svg" "$BOARD" >/dev/null 2>&1
  rsvg-convert -w 2000 "/tmp/juku_$side.svg" -o "renders/board_2d_$side.png"
  rm -f "/tmp/juku_$side.svg"
done
"$KCLI" pcb render --side top --quality high --width 2000 --height 1716 \
    --background opaque -o renders/board_3d_top.png "$BOARD" >/dev/null 2>&1
"$KCLI" pcb render --rotate "-30,20,-20" --zoom 0.9 --quality high --width 2000 --height 1430 \
    --background opaque -o renders/board_3d_persp.png "$BOARD" >/dev/null 2>&1
echo "renders/ updated: $(ls renders/*.png | wc -l | tr -d ' ') views"
