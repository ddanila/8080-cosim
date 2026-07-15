#!/usr/bin/env bash
# Validate every Rev-A part's footprint against the board model (modelled pins
# land on real pads, pad counts match the package). Pre-fab footprint check.
set -euo pipefail

cd "$(dirname "$0")/../../.."

BOARD_JSON="${1:-spinoffs/minimal-vga/kicad/rev-a-physical.board.json}"
KICAD_PYTHON="${KICAD_PYTHON:-$("scripts/find-kicad-python.sh")}"

if [ -z "${KICAD_FOOTPRINTS:-}" ]; then
  for cand in \
    /usr/share/kicad/footprints \
    /opt/homebrew/Caskroom/kicad/*/KiCad/KiCad.app/Contents/SharedSupport/footprints \
    /Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints; do
    [ -d "$cand" ] && { KICAD_FOOTPRINTS="$cand"; break; }
  done
fi
export KICAD_FOOTPRINTS

"$KICAD_PYTHON" spinoffs/minimal-vga/kicad/check_rev_a_footprints.py "$BOARD_JSON"
