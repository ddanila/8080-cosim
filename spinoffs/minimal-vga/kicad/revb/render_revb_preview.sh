#!/usr/bin/env bash
# Render a committable top-view SVG preview of a rev B card PCB (TE.2, eyeball review).
# Vector SVG (small, diff-friendly, no rasteriser/GPU). Skips without kicad-cli.
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../../../.." && pwd)"; cd "$REPO"
CARD="${1:-mem}"
. spinoffs/minimal-vga/kicad/revb/env.sh
revb_have KICAD_CLI || { echo "  SKIP  render ($CARD): kicad-cli not found"; exit 0; }
PCB="fab/minimal-vga/revb/${CARD}.kicad_pcb"
OUT="spinoffs/minimal-vga/docs/revb-previews/${CARD}-top.svg"
mkdir -p "$(dirname "$OUT")"
"$KICAD_CLI" pcb export svg --layers F.Cu,F.Silkscreen,Edge.Cuts --page-size-mode 2 \
  --output "$OUT" "$PCB" >/dev/null
echo "  rendered $OUT"
