#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../../.."

BOARD_JSON="${BOARD_JSON:-spinoffs/minimal-vga/kicad/rev-a-physical.board.json}"
PCB="${PCB:-spinoffs/minimal-vga/kicad/rev-a-physical.kicad_pcb}"
OUT="${OUT:-fab/minimal-vga/routing}"
DSN="$OUT/minimal-vga-rev-a-noplanes.dsn"
SES="$OUT/minimal-vga-rev-a-noplanes.ses"
DRC_JSON="$OUT/minimal-vga-rev-a-routed-drc.json"
DEFAULT_JAVA_BIN=".tools/jre25/bin/java"
if [ ! -x "$DEFAULT_JAVA_BIN" ] && [ -x "$HOME/.gradle/jdks/eclipse_adoptium-25-amd64-linux.2/bin/java" ]; then
  DEFAULT_JAVA_BIN="$HOME/.gradle/jdks/eclipse_adoptium-25-amd64-linux.2/bin/java"
fi
JAVA_BIN="${JAVA_BIN:-$DEFAULT_JAVA_BIN}"
# Prefer the repo submodule fork jar when built (ddanila/freerouting `custom`:
# PolylineTrace.combine fix, headless board-specific settings application,
# dense-board stagnation tuning, and headless v1.9 router selection). The stock
# jar remains a fallback only.
FORK_JARS=(
  "external/freerouting/build/libs/freerouting-current-executable.jar"
  "/Users/danila.sukharev/fun/freerouting/build/libs/freerouting-current-executable.jar"
)
if [ -z "${FREEROUTING_JAR:-}" ]; then
  for jar in "${FORK_JARS[@]}"; do
    if [ -f "$jar" ]; then
      FREEROUTING_JAR="$jar"
      break
    fi
  done
fi
USING_STOCK_FALLBACK=0
if [ -z "${FREEROUTING_JAR:-}" ]; then
  FREEROUTING_JAR=".tools/freerouting/freerouting-2.2.4.jar"
  USING_STOCK_FALLBACK=1
fi
FREEROUTING_ALGORITHM="${FREEROUTING_ALGORITHM:-freerouting-router-v19}"
PASSES="${PASSES:-30}"
if [ "$FREEROUTING_ALGORITHM" = "freerouting-router-v19" ]; then
  DEFAULT_THREADS=1
elif [ "$FREEROUTING_ALGORITHM" = "freerouting-router" ]; then
  DEFAULT_THREADS=4
else
  echo "Unsupported FreeRouting algorithm: $FREEROUTING_ALGORITHM" >&2
  echo "Use freerouting-router-v19 or freerouting-router." >&2
  exit 2
fi
THREADS="${THREADS:-$DEFAULT_THREADS}"
SEED_ROUTES="${SEED_ROUTES:-0}"
JAVA_HEAP="${JAVA_HEAP:-auto}"
KICAD_PYTHON="${KICAD_PYTHON:-$("scripts/find-kicad-python.sh")}"

auto_java_heap() {
  if [ -r /proc/meminfo ]; then
    awk '/MemAvailable:/ { printf "%dm\n", int($2 * 0.70 / 1024); exit }' /proc/meminfo
    return
  fi
  if command -v sysctl >/dev/null 2>&1; then
    mem_bytes="$(sysctl -n hw.memsize 2>/dev/null || true)"
    if [ -n "$mem_bytes" ]; then
      awk -v bytes="$mem_bytes" 'BEGIN { printf "%dm\n", int(bytes * 0.70 / 1024 / 1024) }'
      return
    fi
  fi
  echo ""
}

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
  if [ -d external/freerouting ]; then
    echo "Build the custom fork jar with:" >&2
    echo "  cd external/freerouting && JAVA_HOME=\$HOME/.gradle/jdks/eclipse_adoptium-25-amd64-linux.2 ./gradlew --no-daemon executableJar" >&2
  fi
  echo "Download FreeRouting 2.2.4+ or set FREEROUTING_JAR." >&2
  exit 2
fi

if [ "$USING_STOCK_FALLBACK" = "1" ] && [ "$FREEROUTING_ALGORITHM" = "freerouting-router-v19" ]; then
  echo "The default VJUGA router algorithm requires the custom FreeRouting fork jar." >&2
  echo "Build external/freerouting/build/libs/freerouting-current-executable.jar or set:" >&2
  echo "  FREEROUTING_ALGORITHM=freerouting-router" >&2
  echo "for a stock-router comparison run." >&2
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
if [ "$JAVA_HEAP" = "auto" ]; then
  JAVA_HEAP="$(auto_java_heap)"
fi
if [ -n "$JAVA_HEAP" ]; then
  JAVA_ARGS+=("-Xmx$JAVA_HEAP")
fi

echo "FreeRouting jar: $FREEROUTING_JAR"
echo "FreeRouting algorithm: $FREEROUTING_ALGORITHM"
echo "FreeRouting passes: $PASSES"
echo "FreeRouting threads: $THREADS"
if [ -n "$JAVA_HEAP" ]; then
  echo "Java heap limit: $JAVA_HEAP"
fi

"$JAVA_BIN" "${JAVA_ARGS[@]}" -jar "$FREEROUTING_JAR" \
  -de "$DSN" \
  -do "$SES" \
  -mp "$PASSES" \
  -mt "$THREADS" \
  -da \
  --router.algorithm="$FREEROUTING_ALGORITHM" \
  --gui.enabled=false \
  --user_data_path=.tools/freerouting-user \
  --logging.file.location=.tools/freerouting-user \
  --logging.console.level=INFO

if [ ! -s "$SES" ]; then
  echo "FreeRouting did not write a non-empty SES file: $SES" >&2
  echo "Rebuild the custom fork jar and verify headless v1.9 output serialization." >&2
  exit 3
fi

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
