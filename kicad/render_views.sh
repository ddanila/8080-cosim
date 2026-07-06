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
  tmp="/tmp/juku_png_$side"
  rm -rf "$tmp"
  mkdir -p "$tmp"
  if [ "$side" = front ]; then
    "$KCLI" pcb export png --layers F.Cu --common-layers F.SilkS,Edge.Cuts \
        --scale 0 --dpi 300 -o "$tmp" "$BOARD" >/dev/null 2>&1
    mv "$tmp"/*F_Cu.png "renders/board_2d_$side.png"
  else
    "$KCLI" pcb export png --layers B.Cu --common-layers B.SilkS,Edge.Cuts --mirror \
        --scale 0 --dpi 300 -o "$tmp" "$BOARD" >/dev/null 2>&1
    mv "$tmp"/*B_Cu.png "renders/board_2d_$side.png"
  fi
  rm -rf "$tmp"
done
"$KCLI" pcb render --side top --quality high --width 2000 --height 1716 \
    --background opaque -o renders/board_3d_top.png "$BOARD" >/dev/null 2>&1
"$KCLI" pcb render --rotate "-30,20,-20" --zoom 0.9 --quality high --width 2000 --height 1430 \
    --background opaque -o renders/board_3d_persp.png "$BOARD" >/dev/null 2>&1
echo "renders/ updated: $(ls renders/*.png | wc -l | tr -d ' ') views"
