#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../../.."

BOARD_JSON="${BOARD_JSON:-spinoffs/minimal-vga/kicad/rev-a-physical.board.json}"
PCB="${PCB:-spinoffs/minimal-vga/kicad/rev-a-physical.kicad_pcb}"
OUT="${OUT:-fab/minimal-vga/routing}"
DSN="$OUT/minimal-vga-rev-a-noplanes.dsn"
SES="$OUT/minimal-vga-rev-a-noplanes.ses"
DRC_JSON="$OUT/minimal-vga-rev-a-routed-drc.json"
JAVA_BIN="${JAVA_BIN:-.tools/jre25/bin/java}"
# Prefer the local fork jar when built (ddanila/freerouting `custom`: PolylineTrace.combine
# recursion fix + dense-board stagnation tuning). NOTE (upstream discussion #508): freerouting
# v2.x headless/CLI jobs SKIP board-specific parameter optimizations that GUI runs apply — small
# boards route fine headless (this one does), but if a rerun stagnates, route via the GUI.
FORK_JAR="/Users/danila.sukharev/fun/freerouting/build/libs/freerouting-current-executable.jar"
if [ -z "${FREEROUTING_JAR:-}" ] && [ -f "$FORK_JAR" ]; then
  FREEROUTING_JAR="$FORK_JAR"
fi
FREEROUTING_JAR="${FREEROUTING_JAR:-.tools/freerouting/freerouting-2.2.4.jar}"
PASSES="${PASSES:-30}"
THREADS="${THREADS:-4}"
SEED_ROUTES="${SEED_ROUTES:-1}"
JAVA_HEAP="${JAVA_HEAP:-}"
KICAD_PYTHON="${KICAD_PYTHON:-$("scripts/find-kicad-python.sh")}"

if [ ! -x "$JAVA_BIN" ]; then
  if command -v java >/dev/null 2>&1; then
    JAVA_BIN="$(command -v java)"
  else
    echo "No Java runtime found." >&2
    echo "Install Java 25+ or set JAVA_BIN to a compatible runtime." >&2
    exit 2
  fi
fi

if [ ! -f "$FREEROUTING_JAR" ]; then
  echo "FreeRouting jar not found: $FREEROUTING_JAR" >&2
  echo "Download FreeRouting 2.2.4+ or set FREEROUTING_JAR." >&2
  exit 2
fi

mkdir -p "$OUT" .tools/freerouting-user

"$KICAD_PYTHON" spinoffs/minimal-vga/kicad/check_rev_a_physical.py "$BOARD_JSON"
MINIMAL_VGA_NO_ZONES=1 "$KICAD_PYTHON" spinoffs/minimal-vga/kicad/gen_rev_a_pcb.py "$BOARD_JSON" "$PCB"
if [ "$SEED_ROUTES" = "1" ]; then
  "$KICAD_PYTHON" spinoffs/minimal-vga/kicad/seed_rev_a_routes.py "$PCB"
fi

"$KICAD_PYTHON" - "$PCB" "$DSN" <<'PY'
import sys
import pcbnew

board = pcbnew.LoadBoard(sys.argv[1])
# Duplicate references make ExportSpecctraDSN return False with NO diagnostics (learned on the
# main juku board: ghost X2/X9/D51 twins). Fail loudly with the list instead.
from collections import Counter
refs = Counter(f.GetReference() for f in board.GetFootprints())
dups = sorted(r for r, c in refs.items() if c > 1)
if dups:
    raise SystemExit(f"duplicate footprint references (would silently break DSN export): {dups}")
if not pcbnew.ExportSpecctraDSN(board, sys.argv[2]):
    raise SystemExit(f"failed to export DSN: {sys.argv[2]}")
print(f"wrote DSN: {sys.argv[2]}")
PY

JAVA_ARGS=()
if [ -n "$JAVA_HEAP" ]; then
  JAVA_ARGS+=("-Xmx$JAVA_HEAP")
fi

"$JAVA_BIN" "${JAVA_ARGS[@]}" -jar "$FREEROUTING_JAR" \
  -de "$DSN" \
  -do "$SES" \
  -mp "$PASSES" \
  -mt "$THREADS" \
  -da \
  --gui.enabled=false \
  --user_data_path=.tools/freerouting-user \
  --logging.file.location=.tools/freerouting-user \
  --logging.console.level=INFO

"$KICAD_PYTHON" - "$PCB" "$SES" <<'PY'
import sys
import pcbnew

board = pcbnew.LoadBoard(sys.argv[1])
if not pcbnew.ImportSpecctraSES(board, sys.argv[2]):
    raise SystemExit(f"failed to import SES: {sys.argv[2]}")
pcbnew.SaveBoard(sys.argv[1], board)
print(f"imported SES into {sys.argv[1]}")
PY

kicad-cli pcb drc --severity-error --format json --output "$DRC_JSON" "$PCB" >/dev/null
python3 - "$DRC_JSON" <<'PY'
import json
import sys
from collections import Counter

data = json.load(open(sys.argv[1]))
violations = data.get("violations", [])
unconnected = data.get("unconnected_items", [])
print(f"Routed DRC: {len(violations)} violations, {len(unconnected)} unconnected items")
for typ, count in Counter(item.get("type", "unknown") for item in violations).most_common():
    print(f"  {typ}: {count}")
if violations or unconnected:
    raise SystemExit(3)
PY
