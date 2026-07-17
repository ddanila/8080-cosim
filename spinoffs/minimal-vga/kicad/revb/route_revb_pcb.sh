#!/usr/bin/env bash
# VJUGA rev B card routing via freerouting (TD.7.4; pattern: route_rev_a_pcb.sh).
# Needs a Java 25 runtime (freerouting requirement) AND kicad-cli. Skips (not fails)
# when either is absent -- routing then remains a documented tool-blocked step, not
# a hand-routing invitation (D1.24).
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../../../.." && pwd)"   # repo root (revb -> kicad -> minimal-vga -> spinoffs -> root)
cd "$REPO"
CARD="${1:-mem}"
PCB="fab/minimal-vga/revb/${CARD}.kicad_pcb"
. spinoffs/minimal-vga/kicad/revb/env.sh

revb_have KICAD_PYTHON || { echo "  SKIP  route ($CARD): KICAD_PYTHON not found"; exit 0; }
[ -f "$PCB" ] || { echo "  SKIP  route ($CARD): $PCB not generated yet (run gen_revb_pcb.py)"; exit 0; }
# freerouting.jar is the clear "routing configured?" gate. Absent here (as is a
# Java 25 runtime), so this skips -- routing stays a documented tool-blocked step.
[ -n "${FREEROUTING_JAR:-}" ] && [ -f "${FREEROUTING_JAR}" ] || {
  echo "  SKIP  route ($CARD): FREEROUTING_JAR not set. Routing needs freerouting.jar + a Java 25 runtime."
  echo "        LVS + PCB gen + content-check are complete; routing is the tool-blocked step (D1.24)."
  exit 0; }

# Java 25 (freerouting requires it; system Java 17 is not enough).
JAVA_BIN="${JAVA_BIN:-}"
if [ -z "$JAVA_BIN" ]; then
  for p in .tools/jre25/bin/java "$HOME"/.gradle/jdks/eclipse_adoptium-25-*/bin/java "$HOME"/.jdks/*25*/bin/java; do
    [ -x "$p" ] || continue
    case "$("$p" -version 2>&1 | head -1)" in *\"25*|*\ 25.*) JAVA_BIN="$p"; break;; esac
  done
fi
[ -n "$JAVA_BIN" ] || { echo "  SKIP  route ($CARD): no Java 25 runtime (set JAVA_BIN)."; exit 0; }

OUT="fab/minimal-vga/revb/routing"; mkdir -p "$OUT"
DSN="$OUT/${CARD}.dsn"; SES="$OUT/${CARD}.ses"
echo "== rev B route ($CARD) via freerouting =="
# KiCad 10 kicad-cli has no specctra export; use pcbnew (rev A route_rev_a_pcb.sh method).
"$KICAD_PYTHON" -c "import pcbnew,sys; b=pcbnew.LoadBoard('$PCB'); pcbnew.ExportSpecctraDSN(b,'$DSN')"
"$JAVA_BIN" -jar "$FREEROUTING_JAR" -de "$DSN" -do "$SES" -mp 100
"$KICAD_PYTHON" -c "import pcbnew; b=pcbnew.LoadBoard('$PCB'); pcbnew.ImportSpecctraSES(b,'$SES'); b.Save('$PCB')"
echo "  routed: $SES imported into $PCB"
