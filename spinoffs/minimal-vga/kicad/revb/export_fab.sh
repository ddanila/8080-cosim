#!/usr/bin/env bash
# TG.4 — fab package export for the four rev B boards. Per board: Gerbers + Excellon
# drill into fab/minimal-vga/revb/package/<card>/, zipped, with a SHA256. The zips live
# under the untracked fab/ tree (big binaries, D1.25); the SHA256 manifest is printed so
# it can be recorded in docs/rev-b-order-readiness.md. Skips cleanly without kicad-cli.
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../../../.." && pwd)"
cd "$REPO"
. spinoffs/minimal-vga/kicad/revb/env.sh
revb_have KICAD_CLI || { echo "  SKIP  export_fab: no kicad-cli"; exit 0; }

PKG="fab/minimal-vga/revb/package"
rm -rf "$PKG"; mkdir -p "$PKG"
echo "# rev B fab package SHA256 manifest"
for card in mem io cpu backplane; do
  pcb="fab/minimal-vga/revb/${card}.kicad_pcb"
  [ -f "$pcb" ] || { echo "  SKIP $card: $pcb missing (route it first)"; continue; }
  out="$PKG/$card"; mkdir -p "$out"
  "$KICAD_CLI" pcb export gerbers --output "$out/" "$pcb" >/dev/null 2>&1
  "$KICAD_CLI" pcb export drill --output "$out/" "$pcb" >/dev/null 2>&1
  ( cd "$PKG" && zip -qr "${card}.zip" "$card" )
  sha=$(shasum -a 256 "$PKG/${card}.zip" | awk '{print $1}')
  nfiles=$(ls "$out" | wc -l | tr -d ' ')
  echo "  ${card}.zip  ${sha}  (${nfiles} files)"
done
