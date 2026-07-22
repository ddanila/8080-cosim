#!/usr/bin/env bash
# THE way to run freerouting in this repo. Guarantees:
#   1. the router is OUR custom submodule build, not a stock release, and
#   2. it runs headless (no GUI window).
# It (re)builds from external/freerouting via scripts/build-freerouting.sh
# whenever the installed jar is missing or is a stock jar (no custom marker),
# then execs it. All arguments pass through, e.g.:
#   scripts/run-freerouting.sh -de kicad/juku.dsn -do out.ses -mp 10 -mt 10
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
JAR="$ROOT/.tools/freerouting/freerouting.jar"
MARKER="PolylineTrace.combine: iteration limit reached"

is_custom() {
  [ -f "$JAR" ] && unzip -p "$JAR" 'app/freerouting/board/PolylineTrace.class' 2>/dev/null \
    | grep -qa "$MARKER"
}
if ! is_custom; then
  echo "run-freerouting: installed jar is missing/stock -> building the custom router" >&2
  "$ROOT/scripts/build-freerouting.sh"
fi

find_java() {
  for c in "${FREEROUTING_JDK:-}" \
           "/opt/homebrew/opt/openjdk@25/libexec/openjdk.jdk/Contents/Home" \
           "/opt/homebrew/opt/openjdk@26/libexec/openjdk.jdk/Contents/Home"; do
    [ -n "$c" ] && [ -x "$c/bin/java" ] && { echo "$c/bin/java"; return; }
  done
  if [ -x /usr/libexec/java_home ]; then
    h="$(/usr/libexec/java_home -v 26 2>/dev/null || /usr/libexec/java_home -v 25 2>/dev/null || true)"
    [ -n "$h" ] && { echo "$h/bin/java"; return; }
  fi
  command -v java
}
JAVA="$(find_java)"
# -Djava.awt.headless=true guarantees no window even though the custom build
# defaults the GUI off; harmless belt-and-braces.
exec "$JAVA" -Djava.awt.headless=true -jar "$JAR" "$@"
