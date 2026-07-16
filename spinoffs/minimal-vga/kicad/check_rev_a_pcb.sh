#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../../.."

BOARD_JSON="spinoffs/minimal-vga/kicad/rev-a-physical.board.json"
PCB="spinoffs/minimal-vga/kicad/rev-a-physical.kicad_pcb"
KICAD_PYTHON="${KICAD_PYTHON:-$("scripts/find-kicad-python.sh")}"
KCLI="${KICAD_CLI:-$("scripts/find-kicad-cli.sh")}"

python3 spinoffs/minimal-vga/kicad/check_rev_a_physical.py "$BOARD_JSON"
if [ "${MINIMAL_VGA_REGENERATE_PCB:-0}" = "1" ] || [ ! -f "$PCB" ]; then
  "$KICAD_PYTHON" spinoffs/minimal-vga/kicad/gen_rev_a_pcb.py "$BOARD_JSON" "$PCB"
else
  echo "using existing Rev A PCB: $PCB"
fi
"$KICAD_PYTHON" spinoffs/minimal-vga/kicad/check_rev_a_pcb.py "$PCB"
"$KICAD_PYTHON" spinoffs/minimal-vga/kicad/export_jlcpcb_assembly.py \
  "$PCB" \
  spinoffs/minimal-vga/kicad/rev-a.bom.csv \
  /tmp/minimal-vga-rev-a-assembly
"$KCLI" pcb export drill --format excellon --drill-origin absolute -o /tmp/minimal-vga-rev-a-drill "$PCB" >/dev/null
echo "Rev A PCB scaffold check: PASS"
