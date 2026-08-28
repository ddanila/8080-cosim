#!/usr/bin/env bash
# R5.J2 — one-command archive release run for all five routed rev B board sources.
# Exports only the frozen production Gerbers + Excellon drill, validates both package
# structure and the JLCPCB profile, and writes exact hashes/tool identity to the
# package tree plus a tracked manifest. Layout regeneration/routing is a separate
# engineering audit: it is stochastic and must never silently replace reviewed source
# while packaging. All five routed .kicad_pcb files are tracked release inputs.
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../../../.." && pwd)"
cd "$REPO"
. spinoffs/minimal-vga/kicad/revb/env.sh
revb_have KICAD_CLI || { echo "  SKIP  export_fab: no kicad-cli"; exit 0; }
revb_have KICAD_PYTHON || { echo "  SKIP  export_fab: no pcbnew Python"; exit 0; }

CARDS=(cpu mem io backplane video)

echo "== R5.J2: verify five reviewed routed board sources =="
python3 scripts/check_revb_boards.py --completeness
for card in "${CARDS[@]}"; do
  pcb="fab/minimal-vga/revb/${card}.kicad_pcb"
  [ -f "$pcb" ] || { echo "  FAIL $card: tracked routed source missing"; exit 1; }
  python3 spinoffs/minimal-vga/kicad/revb/check_revb_footprints.py "$card"
  "$KICAD_PYTHON" spinoffs/minimal-vga/kicad/revb/check_revb_pcb.py "$card"
  python3 spinoffs/minimal-vga/kicad/revb/check_revb_drc.py "$card" --total
done
"$KICAD_PYTHON" spinoffs/minimal-vga/kicad/revb/check_revb_jlcpcb.py --self-test

PKG="$REPO/fab/minimal-vga/revb/package"
case "$PKG" in
  "$REPO/fab/minimal-vga/revb/package") ;;
  *) echo "  FAIL: unsafe package target $PKG"; exit 1 ;;
esac
rm -rf -- "$PKG"
mkdir -p "$PKG"

echo "== R5.J2: export and archive production layers only =="
for card in "${CARDS[@]}"; do
  pcb="fab/minimal-vga/revb/${card}.kicad_pcb"
  [ -f "$pcb" ] || { echo "  FAIL $card: $pcb missing (route it first)"; exit 1; }
  out="$PKG/$card"; mkdir -p "$out"
  layers="F.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,Edge.Cuts"
  if [ "$card" = video ]; then
    layers="F.Cu,In1.Cu,In2.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,Edge.Cuts"
  fi
  "$KICAD_CLI" pcb export gerbers \
    --layers "$layers" \
    --output "$out/" "$pcb" >/dev/null 2>&1
  "$KICAD_CLI" pcb export drill --output "$out/" "$pcb" >/dev/null 2>&1
  ( cd "$PKG" && find "$card" -type f -print | LC_ALL=C sort | zip -q -X "${card}.zip" -@ )
done
python3 spinoffs/minimal-vga/kicad/revb/check_revb_package.py
"$KICAD_PYTHON" spinoffs/minimal-vga/kicad/revb/check_revb_jlcpcb.py \
  --package-root "$PKG"
echo "R5.J2: PASS — five source-verified, JLC-profiled fabrication archives"
