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

OUT="fab/minimal-vga/revb/routing"; mkdir -p "$OUT" .tools/freerouting-user
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

# R5.V6: the normal machine current must not traverse 0.20-mm signal tracks.
# Route the two bus rails at their frozen 0.8 mm release width and the short
# protected barrel-input raw link at 2.0 mm from the outset. Routing PWR_RAW at its
# final width prevents post-import widening from creating an otherwise invisible
# signal short. The system-level copper solver proves the resulting voltage trough.
if [ "$CARD" = backplane ]; then
  python3 - "$DSN" <<'PY'
import re
import sys

path = sys.argv[1]
text = open(path, encoding="utf-8").read()
start = text.index("    (class kicad_default ")
depth = 0
end = None
for i in range(start, len(text)):
    if text[i] == "(":
        depth += 1
    elif text[i] == ")":
        depth -= 1
        if depth == 0:
            end = i + 1
            break
if end is None:
    raise SystemExit("cannot parse kicad_default DSN class")
block = text[start:end]
head_end = block.index("      (circuit")
head, tail = block[:head_end], block[head_end:]
for net in ("GND_BUS", "PWR_RAW", "VCC_BUS"):
    head, n = re.subn(rf"(?<![A-Za-z0-9_]){net}(?![A-Za-z0-9_])", "", head)
    if n != 1:
        raise SystemExit(f"expected {net} once in default DSN class, got {n}")
default = head + tail
power = """    (class r5_power GND_BUS VCC_BUS
      (circuit
        (use_via \"Via[0-1]_600:300_um\")
      )
      (rule
        (width 800)
        (clearance 200)
      )
    )
    (class r5_raw PWR_RAW
      (circuit
        (use_via \"Via[0-1]_600:300_um\")
      )
      (rule
        (width 2000)
        (clearance 200)
      )
    )
"""
text = text[:start] + power + default + text[end:]
open(path, "w", encoding="utf-8").write(text)
print("  assigned GND_BUS/VCC_BUS to 0.8 mm and PWR_RAW to 2.0 mm")
PY
fi

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
  # Per-attempt DSN identity: FreeRouting hashes the PCB name inside the file, not
  # merely the input filename.  Rewrite that name so retry N really receives a
  # distinct optimization seed instead of deterministically repeating attempt 1.
  cp "$DSN" "$OUT/${CARD}-a${attempt}.dsn"
  python3 - "$OUT/${CARD}-a${attempt}.dsn" "$CARD" "$attempt" <<'PY'
import re
import sys

path, card, attempt = sys.argv[1:]
text = open(path, encoding="utf-8").read()
text, count = re.subn(r'^\(pcb "[^"]+"', f'(pcb "{card}-attempt-{attempt}"',
                      text, count=1)
if count != 1:
    raise SystemExit("cannot rewrite per-attempt DSN identity")
open(path, "w", encoding="utf-8").write(text)
PY
  "$JAVA_BIN" -Djava.awt.headless=true -jar "$FREEROUTING_JAR" \
    -de "$OUT/${CARD}-a${attempt}.dsn" -do "$SES" -mp "$PASSES" \
    -is "${FR_SELECTION:-prioritized}" -us "${FR_UPDATE:-greedy}" \
    --router.optimizer.enabled=false \
    --gui.enabled=false \
    --user_data_path="$REPO/.tools/freerouting-user" \
    --logging.file.location="$REPO/.tools/freerouting-user" \
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
