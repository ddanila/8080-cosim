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
# freerouting.jar gate (default to the home-folder install, .tools/freerouting).
: "${FREEROUTING_JAR:=.tools/freerouting/freerouting.jar}"
[ -f "${FREEROUTING_JAR}" ] || {
  echo "  SKIP  route ($CARD): freerouting.jar not found (set FREEROUTING_JAR)."
  echo "        LVS + PCB gen + content-check are complete; routing is the tool-blocked step (D1.24)."
  exit 0; }

# Java 25 (freerouting requires it; system Java 17 is not enough). Handles both the
# Linux (bin/java) and macOS bundle (Contents/Home/bin/java) layouts.
JAVA_BIN="${JAVA_BIN:-}"
if [ -z "$JAVA_BIN" ]; then
  for p in .tools/jre25/bin/java .tools/jre25/Contents/Home/bin/java \
           "$HOME"/.jdks/*25*/bin/java "$HOME"/.jdks/*25*/Contents/Home/bin/java \
           "$HOME"/.gradle/jdks/eclipse_adoptium-25-*/bin/java; do
    [ -x "$p" ] || continue
    case "$("$p" -version 2>&1 | head -1)" in *\"25*|*\ 25.*) JAVA_BIN="$p"; break;; esac
  done
fi
[ -n "$JAVA_BIN" ] || { echo "  SKIP  route ($CARD): no Java 25 runtime (set JAVA_BIN)."; exit 0; }
echo "  using java: $JAVA_BIN"

OUT="fab/minimal-vga/revb/routing"; mkdir -p "$OUT"
DSN="$OUT/${CARD}.dsn"; SES="$OUT/${CARD}.ses"
echo "== rev B route ($CARD) via freerouting =="
# KiCad 10 kicad-cli has no specctra export; use pcbnew (rev A route_rev_a_pcb.sh method).
# ExportSpecctraDSN returns False (silently) on duplicate refs -- check it.
"$KICAD_PYTHON" -c "import pcbnew,sys; b=pcbnew.LoadBoard('$PCB');
sys.exit(0 if pcbnew.ExportSpecctraDSN(b,'$DSN') else 'DSN export failed')"
# freerouting 2.x is GUI-first (-Djava.awt.headless=true runs it batch on macOS) and
# stochastic -- this board is near the 2-layer routability edge, so retry until a run
# routes every net (no "could not be routed" in the log).
ROUTED=""
for attempt in 1 2 3 4 5 6 7 8 9 10 11 12; do
  "$JAVA_BIN" -Djava.awt.headless=true -jar "$FREEROUTING_JAR" -de "$DSN" -do "$SES" -mp 100 \
    >"$OUT/${CARD}-fr.log" 2>&1 || true
  if [ -f "$SES" ] && ! grep -qi "could not be routed" "$OUT/${CARD}-fr.log"; then
    ROUTED=1; echo "  fully routed on attempt $attempt: $(grep -oE 'final score: [0-9.]+' "$OUT/${CARD}-fr.log" | tail -1)"; break
  fi
  echo "  attempt $attempt: not fully routed, retrying"
done
[ -n "$ROUTED" ] || { echo "  route ($CARD): could not fully route (needs placement margin) (needs placement margin)"; exit 1; }
"$KICAD_PYTHON" -c "import pcbnew; b=pcbnew.LoadBoard('$PCB'); pcbnew.ImportSpecctraSES(b,'$SES'); b.Save('$PCB')"
echo "  routed: $SES imported into $PCB"
