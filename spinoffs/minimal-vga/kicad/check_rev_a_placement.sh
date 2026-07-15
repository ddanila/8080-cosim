#!/usr/bin/env bash
# Generate the Rev-A PCB from the board model and run the silk/placement
# collision checker (docs: automatic version of eyeballing the silk preview).
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

TMP_BOARD="$(mktemp "${TMPDIR:-/tmp}/vjuga-place.XXXXXX.kicad_pcb")"
trap 'rm -f "$TMP_BOARD"' EXIT

MINIMAL_VGA_NO_ZONES=1 "$KICAD_PYTHON" spinoffs/minimal-vga/kicad/gen_rev_a_pcb.py "$BOARD_JSON" "$TMP_BOARD" >/dev/null
"$KICAD_PYTHON" spinoffs/minimal-vga/kicad/check_rev_a_placement.py "$TMP_BOARD"
