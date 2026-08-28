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
           .tools/jdk25/bin/java \
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
# ExportSpecctraDSN returns False (silently) on duplicate refs -- check it. The DSN is
# exported ONCE from the pristine (pre-route) board so every retry routes the same input
# with a fresh seed; each attempt imports into a pristine copy, never compounding.
PRISTINE="$OUT/${CARD}.pristine.kicad_pcb"
cp "$PCB" "$PRISTINE"
"$KICAD_PYTHON" - "$PRISTINE" "$DSN" "$CARD" <<'PY'
import sys
import pcbnew

board = pcbnew.LoadBoard(sys.argv[1])
if sys.argv[3] == "video":
    for zone in list(board.Zones()):
        if not zone.GetIsRuleArea():
            board.Remove(zone)
    board.Save(sys.argv[1])
if not pcbnew.ExportSpecctraDSN(board, sys.argv[2]):
    raise SystemExit("DSN export failed")
PY

# R5.V5 reserves the Video inner layers as solid power planes. Mark them as power
# in Specctra so FreeRouting cannot consume them for signal tracks.
if [ "$CARD" = video ]; then
  python3 - "$DSN" <<'PY'
import sys
path = sys.argv[1]
text = open(path, encoding="utf-8").read()
for layer, net in (("In1.Cu", "GND"), ("In2.Cu", "VCC5")):
    old = f"    (layer {layer}\n      (type signal)"
    new = f"    (layer {layer}\n      (type power)\n      (use_net {net})"
    if text.count(old) != 1:
        raise SystemExit(f"cannot uniquely reserve {layer} for {net}")
    text = text.replace(old, new)
open(path, "w", encoding="utf-8").write(text)
print("  reserved In1.Cu=GND and In2.Cu=VCC5 in DSN")
PY
fi
# freerouting 2.x is GUI-first (-Djava.awt.headless=true runs it batch on macOS) and
# stochastic -- a run can report success in its log yet leave a net island. So we don't
# trust the log: we import each candidate and accept only when the TOTAL DRC is 0/0
# (0 violations AND 0 unconnected). FR_ATTEMPTS bounds the retries (the TF.1 sweep sets
# it low so a hopeless placement is rejected fast; routing uses the default otherwise).
if [ "$CARD" = video ]; then
  # R5.V5's four-layer placement plus two deterministic VGA necks reaches 0/0
  # in a single bounded solve. Keep this release path fast and repeatable.
  ATTEMPTS="${FR_ATTEMPTS:-1}"
  PASSES="${FR_PASSES:-25}"
else
  ATTEMPTS="${FR_ATTEMPTS:-25}"
  PASSES="${FR_PASSES:-100}"
fi
ROUTED=""
for attempt in $(seq 1 "$ATTEMPTS"); do
  # per-attempt DSN copy: freerouting derives job/board identity (and some caching/
  # seeding) from its input; a fresh filename per attempt guarantees an independent run.
  cp "$DSN" "$OUT/${CARD}-a${attempt}.dsn"
  "$JAVA_BIN" -Djava.awt.headless=true -jar "$FREEROUTING_JAR" \
    -de "$OUT/${CARD}-a${attempt}.dsn" -do "$SES" -mp "$PASSES" \
    >"$OUT/${CARD}-fr.log" 2>&1 || true
  rm -f "$OUT/${CARD}-a${attempt}.dsn"
  [ -f "$SES" ] || { echo "  attempt $attempt: no SES produced, retrying"; continue; }
  grep -qi "could not be routed" "$OUT/${CARD}-fr.log" && { echo "  attempt $attempt: log reports unrouted nets, retrying"; continue; }
  "$KICAD_PYTHON" - "$PRISTINE" "$SES" "$PCB" "$CARD" <<'PY'
import os
import sys
import pcbnew

board = pcbnew.LoadBoard(sys.argv[1])
if not pcbnew.ImportSpecctraSES(board, sys.argv[2]):
    raise SystemExit("SES import failed")
if sys.argv[4] == "video":
    def add_plane(net_name, layer, name):
        zone = pcbnew.ZONE(board)
        zone.SetLayer(layer)
        zone.SetNet(board.FindNet(net_name))
        zone.SetZoneName(name)
        zone.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
        zone.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        for x, y in ((0.8, 0.8), (99.2, 0.8), (99.2, 99.2), (0.8, 99.2)):
            zone.AppendCorner(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)), -1)
        board.Add(zone)
    add_plane("GND", pcbnew.In1_Cu, "VJUGA rev B Video GND plane")
    add_plane("VCC5", pcbnew.In2_Cu, "VJUGA rev B Video VCC5 plane")
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
board.Save(sys.argv[3])
PY
  if python3 spinoffs/minimal-vga/kicad/revb/check_revb_drc.py "$CARD" --total >/dev/null 2>&1; then
    ROUTED=1; echo "  routed 0/0 on attempt $attempt: $(grep -oE 'final score: [0-9.]+' "$OUT/${CARD}-fr.log" | tail -1)"; break
  fi
  echo "  attempt $attempt: imported but total DRC not 0/0, retrying"
done
rm -f "$PRISTINE"
[ -n "$ROUTED" ] || { echo "  route ($CARD): could not reach 0/0 in $ATTEMPTS attempts (needs placement margin)"; exit 1; }
echo "  routed: $SES imported into $PCB (total DRC 0/0)"
