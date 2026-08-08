#!/usr/bin/env bash
# TG.4 — fab package export for the four rev B B1 boards. Per board: the exact
# two-layer production Gerbers + Excellon drill, zipped and content-validated. The
# packages and detailed hash manifest live under the untracked fab/ tree (D1.25).
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../../../.." && pwd)"
cd "$REPO"
. spinoffs/minimal-vga/kicad/revb/env.sh
revb_have KICAD_CLI || { echo "  SKIP  export_fab: no kicad-cli"; exit 0; }
revb_have KICAD_PYTHON || { echo "  SKIP  export_fab: no pcbnew Python"; exit 0; }

PKG="fab/minimal-vga/revb/package"
rm -rf "$PKG"; mkdir -p "$PKG"
for card in mem io cpu backplane; do
  pcb="fab/minimal-vga/revb/${card}.kicad_pcb"
  [ -f "$pcb" ] || { echo "  FAIL $card: $pcb missing (route it first)"; exit 1; }
  "$KICAD_PYTHON" spinoffs/minimal-vga/kicad/revb/check_revb_pcb.py "$card" >/dev/null
  python3 spinoffs/minimal-vga/kicad/revb/check_revb_drc.py "$card" --total
  out="$PKG/$card"; mkdir -p "$out"
  "$KICAD_CLI" pcb export gerbers \
    --layers F.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,Edge.Cuts \
    --output "$out/" "$pcb" >/dev/null 2>&1
  "$KICAD_CLI" pcb export drill --output "$out/" "$pcb" >/dev/null 2>&1
  ( cd "$PKG" && find "$card" -type f -print | LC_ALL=C sort | zip -q -X "${card}.zip" -@ )
done
python3 spinoffs/minimal-vga/kicad/revb/check_revb_package.py
