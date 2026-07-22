#!/usr/bin/env bash
# Build the freerouting router FROM OUR SUBMODULE (external/freerouting @ custom)
# and install it at .tools/freerouting/freerouting.jar -- the jar the routing
# workflow uses. Do NOT drop a stock freerouting release there: the custom branch
# carries fixes we depend on (bounded PolylineTrace.combine so headless routing of
# DSNs with locked wires can't StackOverflow, dense-board stagnation tuning,
# headless v1.9 routing). See docs/freerouting-build.md.
#
# The jar is gitignored (~59 MB); the submodule commit is the source of truth, so
# a fresh checkout runs this once to reproduce the exact router.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SUB="$ROOT/external/freerouting"
DEST="$ROOT/.tools/freerouting/freerouting.jar"
# Custom-only string baked into PolylineTrace by the recursion fix; its presence
# is how we tell the custom build apart from a stock release.
MARKER="PolylineTrace.combine: iteration limit reached"

# --- locate a JDK 25+ (the jar targets class-file 69.0) ---
find_jdk() {
  for c in "${FREEROUTING_JDK:-}" \
           "/opt/homebrew/opt/openjdk@25/libexec/openjdk.jdk/Contents/Home" \
           "/opt/homebrew/opt/openjdk@26/libexec/openjdk.jdk/Contents/Home"; do
    [ -n "$c" ] && [ -x "$c/bin/java" ] && { echo "$c"; return; }
  done
  if [ -x /usr/libexec/java_home ]; then
    for v in 26 25; do /usr/libexec/java_home -v "$v" 2>/dev/null && return; done
  fi
  for c in /usr/lib/jvm/java-2[56]-openjdk* /usr/lib/jvm/temurin-2[56]*; do
    [ -x "$c/bin/java" ] && { echo "$c"; return; }
  done
  return 1
}
JDK="$(find_jdk || true)"
[ -n "$JDK" ] || { echo "build-freerouting: need a JDK 25+; set FREEROUTING_JDK=/path/to/jdk" >&2; exit 2; }
echo "build-freerouting: JDK = $JDK"

# --- ensure the submodule is present at the pinned commit ---
if [ ! -f "$SUB/gradlew" ]; then
  echo "build-freerouting: initializing submodule external/freerouting"
  git -C "$ROOT" submodule update --init external/freerouting
fi
COMMIT="$(git -C "$SUB" rev-parse HEAD)"
echo "build-freerouting: external/freerouting @ $COMMIT"

# --- build the executable jar ---
( cd "$SUB" && JAVA_HOME="$JDK" ./gradlew executableJar -x test --console=plain )
BUILT="$SUB/build/libs/freerouting-current-executable.jar"
[ -f "$BUILT" ] || { echo "build-freerouting: expected jar not produced: $BUILT" >&2; exit 1; }

# --- verify it really is the custom build, then install ---
if ! unzip -p "$BUILT" 'app/freerouting/board/PolylineTrace.class' 2>/dev/null | grep -qa "$MARKER"; then
  echo "build-freerouting: built jar is missing the custom marker -- refusing to install" >&2
  exit 1
fi
mkdir -p "$(dirname "$DEST")"
cp "$BUILT" "$DEST"
SHA="$(shasum -a 256 "$DEST" | cut -d' ' -f1)"
cat > "$ROOT/.tools/freerouting/PROVENANCE.txt" <<EOF
Built from submodule external/freerouting @ $COMMIT (branch custom)
jar sha256: $SHA
built: $(date -u +%Y-%m-%dT%H:%M:%SZ)
custom marker verified: yes
EOF
echo "build-freerouting: installed custom jar -> $DEST"
echo "build-freerouting: sha256 $SHA"
