#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../../.."

BOARD="spinoffs/minimal-vga/kicad/rev-a-physical.board.json"
SCH="spinoffs/minimal-vga/kicad/rev-a-physical.kicad_sch"

python3 spinoffs/minimal-vga/kicad/check_rev_a_physical.py "$BOARD"
python3 kicad/gen_kicad_sch.py --include-power "$BOARD" "$SCH"
echo "wrote $SCH"
